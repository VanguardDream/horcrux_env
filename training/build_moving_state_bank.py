"""이동 상태 은행 생성 — 인계 시작 학습(plane-moving-init-v0)용.

전문가 10명(+선택: 통합 정책)이 실제로 만드는 몸 상태(qpos, qvel)와 그 순간 gait가 다음에
적용할 motion vector를 저장한다. reset 시 이 상태를 복원하고 목표 gait로 전환하면
"다른 정책이 움직이던 상태에서 전환된 순간"이 재현된다.

구성 (출발 명령당 per_source개, 총 10 × per_source):
  kind 0  결정론 롤아웃      전문가 평균 행동, 사전 주행 길이 100~800스텝 무작위, 매 스텝 저장
  kind 1  노이즈 롤아웃      전문가 자체 가우시안 샘플 행동 (분포 폭 확장)
  kind 2  2차 상태           전문가가 (1차 은행의) 다른 출발 상태에서 인계 시작해 굴린 뒤의 상태
                            — "전환 뒤의 전환" 상태
  kind 3  통합 정책 롤아웃   S3 final을 무작위 전환 커리큘럼으로 굴린 상태 (출발 = 실행 중 명령)
  + 이전 은행 재사용 (--prev-bank, 비율 prev_frac): 반복 학습 시 분포 협착 방지
건강한 상태(롤 범위 내)만 저장, xy는 원점으로 평행이동. 메타데이터(체크포인트·시드·개수)는
같은 이름의 .json에 기록한다.

사용:
  python training/build_moving_state_bank.py --out runs/moving_state_bank/bank_iter1.npz --per-source 20000
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))
from path_following import EXPERT_PATHS  # noqa: E402
from horcrux_env.envs.gait_provider import VALIDATED_COMMANDS  # noqa: E402

NAMES = [c[0] for c in VALIDATED_COMMANDS]
N_CMD = len(NAMES)
# 방위/회전 계보 공통 env 인자 (보상 frozen, 창 없음)
BASE_KW = dict(forward_reward_weight=60.0, efficiency_reward_weight=3.0, healthy_reward=2.0,
               rotation_norm_cost_weight=10.0, proj_dist_cost_weight=0.0, ctrl_cost_weight=0.0,
               use_friction_chg=False, terminate_when_unhealthy=True, unhealthy_max_steps=30,
               use_imu_window=False, use_vels_window=False)


def _expert(cmd: int, device: str = "cpu"):
    from stable_baselines3 import PPO
    base = ROOT / EXPERT_PATHS[NAMES[cmd]] / "evaluation"
    model = PPO.load(str(base / "best_model.zip"), device=device)
    with open(base / "best_model_vecnormalize.pkl", "rb") as f:
        vn = pickle.load(f)
    mean, std, clip = vn.obs_rms.mean.copy(), np.sqrt(vn.obs_rms.var + vn.epsilon), float(vn.clip_obs)

    def act(raw, deterministic=True):
        obs = np.clip((raw - mean) / std, -clip, clip).astype(np.float32)
        a, _ = model.predict(obs, deterministic=deterministic)
        return a.astype(np.float32)
    return act


def _make_env(cmd: int, seed: int, bank_path: str | None = None, source_weights=None, moving_init_prob: float = 0.0):
    import gymnasium as gym
    import horcrux_env  # noqa: F401
    from horcrux_env.wrappers import NormalizeAction
    kw = dict(BASE_KW)
    kw.update(joy_input=list(VALIDATED_COMMANDS[cmd][1]), gait_params=list(VALIDATED_COMMANDS[cmd][2]))
    if bank_path:
        kw.update(bank_path=bank_path, moving_init_prob=moving_init_prob, align_prob=1.0,
                  moving_episode_horizon=None, source_weights=source_weights)
    env = NormalizeAction(gym.make("horcrux_env/plane-moving-init-v0", **kw))
    env.reset(seed=seed)
    return env


def _record(u, buf, source: int, kind: int):
    """현재 상태를 저장 (건강할 때만). xy 원점 평행이동."""
    if not u.is_healthy:
        return False
    qpos = u.data.qpos.copy()
    qpos[0:2] = 0.0
    buf["qpos"].append(qpos.astype(np.float32))
    buf["qvel"].append(u.data.qvel.copy().astype(np.float32))
    buf["mvec"].append(u._motion_vector.astype(np.int8))
    buf["source"].append(source)
    buf["kind"].append(kind)
    return True


def _worker_pass1(args):
    cmd, n_target, seed = args
    import torch
    torch.set_num_threads(1)
    rng = np.random.default_rng(seed)
    act = _expert(cmd)
    env = _make_env(cmd, seed)
    u = env.unwrapped
    buf = {k: [] for k in ("qpos", "qvel", "mvec", "source", "kind")}
    ep = 0
    while len(buf["source"]) < n_target:
        stochastic = bool(rng.random() < 0.5)
        pre = int(rng.integers(100, 800))
        raw, _ = env.reset(seed=seed + 100 * ep)
        for t in range(pre + 200):
            raw, r, te, tr, info = env.step(act(raw, deterministic=not stochastic))
            if te or tr:
                break
            if t >= 100:
                _record(u, buf, cmd, 1 if stochastic else 0)
                if len(buf["source"]) >= n_target:
                    break
        ep += 1
    env.close()
    return cmd, {k: np.asarray(v) for k, v in buf.items()}


def _worker_pass2(args):
    cmd, n_target, seed, bank_path = args
    import torch
    torch.set_num_threads(1)
    rng = np.random.default_rng(seed)
    act = _expert(cmd)
    w = np.ones(N_CMD)
    w[cmd] = 0.0  # 다른 출발 상태에서 인계
    env = _make_env(cmd, seed, bank_path=bank_path, source_weights=w, moving_init_prob=1.0)
    u = env.unwrapped
    buf = {k: [] for k in ("qpos", "qvel", "mvec", "source", "kind")}
    ep = 0
    while len(buf["source"]) < n_target:
        raw, _ = env.reset(seed=seed + 100 * ep)
        stochastic = bool(rng.random() < 0.5)
        for t in range(300):
            raw, r, te, tr, info = env.step(act(raw, deterministic=not stochastic))
            if te or tr:
                break
            if t >= 50:
                _record(u, buf, cmd, 2)
                if len(buf["source"]) >= n_target:
                    break
        ep += 1
    env.close()
    return cmd, {k: np.asarray(v) for k, v in buf.items()}


def _unified_states(model_path: Path, vecnorm_path: Path, config: Path, n_target: int, seed: int):
    """통합 정책을 전환 커리큘럼 env로 굴려 상태 수집 (출발 = 실행 중 명령)."""
    import gymnasium as gym
    import horcrux_env  # noqa: F401
    from horcrux_env.wrappers import NormalizeAction
    from distill_experts import Student
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    kw = dict(cfg["environment"]["kwargs"])
    vn = pickle.load(open(vecnorm_path, "rb"))
    pol = Student(model_path, vn.obs_rms.mean, np.sqrt(vn.obs_rms.var + vn.epsilon), float(vn.clip_obs))
    env = NormalizeAction(gym.make("horcrux_env/plane-unified-v0", **kw))
    u = env.unwrapped
    buf = {k: [] for k in ("qpos", "qvel", "mvec", "source", "kind")}
    ep = 0
    while len(buf["source"]) < n_target:
        raw, _ = env.reset(seed=seed + ep)
        for t in range(1000):
            raw, r, te, tr, info = env.step(pol.act(raw))
            if te or tr:
                break
            if t >= 50:
                _record(u, buf, int(u.command_id), 3)
                if len(buf["source"]) >= n_target:
                    break
        ep += 1
    env.close()
    return {k: np.asarray(v) for k, v in buf.items()}


def _concat(parts):
    return {k: np.concatenate([p[k] for p in parts]) for k in ("qpos", "qvel", "mvec", "source", "kind")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "runs/moving_state_bank/bank_iter1.npz")
    ap.add_argument("--per-source", type=int, default=20000)
    ap.add_argument("--second-order-frac", type=float, default=0.25, help="출발 명령당 2차 상태 비율")
    ap.add_argument("--unified-frac", type=float, default=0.10, help="전체 대비 통합 정책 상태 비율 (0이면 생략)")
    ap.add_argument("--unified-model", type=Path, default=ROOT / "policies/unified/03_transition_stage3/final_model.zip")
    ap.add_argument("--unified-vecnorm", type=Path, default=ROOT / "policies/unified/03_transition_stage3/vecnormalize.pkl")
    ap.add_argument("--unified-config", type=Path, default=ROOT / "training/configs/ppo_unified_transition_stage3.yaml")
    ap.add_argument("--prev-bank", type=Path, default=None)
    ap.add_argument("--prev-frac", type=float, default=0.30)
    ap.add_argument("--workers", type=int, default=N_CMD)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ctx = mp.get_context("spawn")
    n1 = int(a.per_source * (1 - a.second_order_frac))
    n2 = a.per_source - n1
    print(f"[1/4] 1차 상태 (결정론+노이즈): 출발 명령당 {n1:,}", flush=True)
    with ctx.Pool(min(a.workers, N_CMD)) as pool:
        p1 = dict(pool.map(_worker_pass1, [(c, n1, a.seed + 17 * c) for c in range(N_CMD)]))
    bank1 = _concat([p1[c] for c in range(N_CMD)])
    tmp = a.out.with_name(a.out.stem + "_pass1.npz")
    np.savez_compressed(tmp, **bank1)
    print(f"      {len(bank1['source']):,} 상태, {time.time()-t0:.0f}s", flush=True)
    parts = [bank1]
    if n2 > 0:
        print(f"[2/4] 2차 상태 (다른 출발에서 인계 후): 출발 명령당 {n2:,}", flush=True)
        with ctx.Pool(min(a.workers, N_CMD)) as pool:
            p2 = dict(pool.map(_worker_pass2, [(c, n2, a.seed + 1000 + 17 * c, str(tmp)) for c in range(N_CMD)]))
        parts.append(_concat([p2[c] for c in range(N_CMD)]))
        print(f"      {len(parts[-1]['source']):,} 상태, {time.time()-t0:.0f}s", flush=True)
    if a.unified_frac > 0 and a.unified_model.exists():
        n3 = int(a.per_source * N_CMD * a.unified_frac)
        print(f"[3/4] 통합 정책 상태: {n3:,}", flush=True)
        parts.append(_unified_states(a.unified_model, a.unified_vecnorm, a.unified_config, n3, a.seed + 5000))
    if a.prev_bank is not None and a.prev_bank.exists():
        prev = dict(np.load(a.prev_bank))
        n_prev = int(a.per_source * N_CMD * a.prev_frac)
        idx = np.random.default_rng(a.seed).choice(len(prev["source"]), size=min(n_prev, len(prev["source"])), replace=False)
        parts.append({k: prev[k][idx] for k in ("qpos", "qvel", "mvec", "source", "kind")})
        print(f"      이전 은행 {len(idx):,} 상태 합침", flush=True)
    bank = _concat(parts)
    np.savez_compressed(a.out, **bank)
    tmp.unlink(missing_ok=True)
    counts = {NAMES[c]: int((bank["source"] == c).sum()) for c in range(N_CMD)}
    kinds = {k: int((bank["kind"] == i).sum()) for i, k in enumerate(("det", "stoch", "second", "unified"))}
    meta = dict(created=time.strftime("%Y-%m-%d %H:%M:%S"), args={k: str(v) for k, v in vars(a).items()},
                experts={n: EXPERT_PATHS[n] for n in NAMES}, n_states=int(len(bank["source"])), per_source=counts, kinds=kinds,
                elapsed_sec=time.time() - t0)
    a.out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[4/4] 저장 {a.out}  총 {meta['n_states']:,} 상태  ({a.out.stat().st_size/1e6:.1f} MB, {meta['elapsed_sec']/60:.1f}분)")
    print("      출발별:", counts)
    print("      종류별:", kinds)


if __name__ == "__main__":
    main()
