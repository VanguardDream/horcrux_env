"""전문가 전환 진입 평가 — 정상 주행(정지 시작) + 출발별 진입 실패율 행렬(은행 상태 사용).

각 목표 전문가에 대해:
  (a) 정지 시작 정상 주행: rest_episodes × rest_steps, joy 방향 진행 속도·리턴·낙상
  (b) 진입 행렬: 출발 명령 10개 × states_per_source개 은행 상태에서 align 전환으로 시작해
      post_steps 안에 종료(불건강)되면 실패. plane-moving-init-v0(moving_init_prob=1,
      align_prob=1, source_weights one-hot)를 그대로 써서 학습 규약과 동일하게 재현.

--override 로 특정 명령의 체크포인트를 바꿔 새 전문가를 평가한다.
  --override diag_fr=policies/.../final_model.zip:policies/.../vecnormalize.pkl

사용:
  python training/eval_expert_transitions.py --bank runs/moving_state_bank/bank_iter1.npz --targets diag_fr diag_bl forward
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))
from path_following import EXPERT_PATHS  # noqa: E402
from build_moving_state_bank import BASE_KW  # noqa: E402
from horcrux_env.envs.gait_provider import VALIDATED_COMMANDS  # noqa: E402

NAMES = [c[0] for c in VALIDATED_COMMANDS]
N_CMD = len(NAMES)
LINEAR = [n for n, joy, _ in VALIDATED_COMMANDS if joy[2] == 0.0]


def load_policy(model_path: Path, vecnorm_path: Path):
    from stable_baselines3 import PPO
    model = PPO.load(str(model_path), device="cpu")
    with open(vecnorm_path, "rb") as f:
        vn = pickle.load(f)
    mean, std, clip = vn.obs_rms.mean.copy(), np.sqrt(vn.obs_rms.var + vn.epsilon), float(vn.clip_obs)

    def act(raw):
        obs = np.clip((raw - mean) / std, -clip, clip).astype(np.float32)
        a, _ = model.predict(obs, deterministic=True)
        return a.astype(np.float32)
    return act


def default_ckpt(name: str):
    base = ROOT / EXPERT_PATHS[name] / "evaluation"
    return base / "best_model.zip", base / "best_model_vecnormalize.pkl"


def make_env(cmd: int, seed: int, bank: str | None, source: int | None, moving_init_prob: float):
    import gymnasium as gym
    import horcrux_env  # noqa: F401
    from horcrux_env.wrappers import NormalizeAction
    kw = dict(BASE_KW)
    kw.update(joy_input=list(VALIDATED_COMMANDS[cmd][1]), gait_params=list(VALIDATED_COMMANDS[cmd][2]))
    if bank:
        w = np.ones(N_CMD)
        if source is not None:
            w = np.zeros(N_CMD)
            w[source] = 1.0
        kw.update(bank_path=bank, moving_init_prob=moving_init_prob, align_prob=1.0, moving_episode_horizon=None, source_weights=w)
    env = NormalizeAction(gym.make("horcrux_env/plane-moving-init-v0", **kw))
    env.reset(seed=seed)
    return env


def evaluate_target(name: str, model_path: Path, vecnorm_path: Path, bank: str, states_per_source: int, post_steps: int,
                    rest_episodes: int, rest_steps: int, seed: int) -> dict:
    cmd = NAMES.index(name)
    act = load_policy(model_path, vecnorm_path)
    joy = np.asarray(VALIDATED_COMMANDS[cmd][1][:2], dtype=float)
    # (a) 정지 시작
    env = make_env(cmd, seed, None, None, 0.0)
    speeds, rets, falls = [], [], 0
    for ep in range(rest_episodes):
        raw, _ = env.reset(seed=seed + ep)
        com0 = None
        ret = 0.0
        for t in range(rest_steps):
            raw, r, te, tr, info = env.step(act(raw))
            if com0 is None:
                com0 = np.asarray(info["com_pos"][:2], dtype=float)
            ret += r
            if te or tr:
                break
        com1 = np.asarray(info["com_pos"][:2], dtype=float)
        speeds.append(float((com1 - com0) @ joy / ((t + 1) * 0.05)))
        rets.append(ret)
        falls += int(te)
    env.close()
    rest = dict(speed=float(np.mean(speeds)), ret=float(np.mean(rets)), fall_rate=falls / rest_episodes)
    # (b) 진입 행렬
    matrix = {}
    for src in range(N_CMD):
        if src == cmd:
            continue
        env = make_env(cmd, seed + 1000 + src, bank, src, 1.0)
        fails = 0
        for k in range(states_per_source):
            raw, _ = env.reset(seed=seed + 1000 + 37 * src + k)
            for t in range(post_steps):
                raw, r, te, tr, info = env.step(act(raw))
                if te:
                    fails += 1
                    break
                if tr:
                    break
        env.close()
        matrix[NAMES[src]] = fails / states_per_source
    return dict(rest=rest, entry_fail=matrix, entry_fail_mean=float(np.mean(list(matrix.values()))))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", type=str, default=str(ROOT / "runs/moving_state_bank/bank_iter1.npz"))
    ap.add_argument("--targets", nargs="+", default=LINEAR)
    ap.add_argument("--override", action="append", default=[], help="cmd=model.zip:vecnormalize.pkl")
    ap.add_argument("--states-per-source", type=int, default=20)
    ap.add_argument("--post-steps", type=int, default=150)
    ap.add_argument("--rest-episodes", type=int, default=5)
    ap.add_argument("--rest-steps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--label", default="baseline")
    a = ap.parse_args()
    overrides = {}
    for o in a.override:
        k, v = o.split("=", 1)
        m, vn = v.split(":", 1)
        overrides[k] = (Path(m), Path(vn))
    t0 = time.time()
    results = {}
    for name in a.targets:
        m, vn = overrides.get(name, default_ckpt(name))
        res = evaluate_target(name, m, vn, a.bank, a.states_per_source, a.post_steps, a.rest_episodes, a.rest_steps, a.seed)
        res["model"] = str(m)
        results[name] = res
        worst = max(res["entry_fail"].items(), key=lambda kv: kv[1])
        print(f"{name:9s} 정지: 속도 {res['rest']['speed']:.3f} m/s 리턴 {res['rest']['ret']:,.0f} 낙상 {res['rest']['fall_rate']:.2f} | "
              f"진입 실패 평균 {res['entry_fail_mean']:.3f} 최악 {worst[0]} {worst[1]:.2f}", flush=True)
    # 행렬 표
    srcs = [n for n in NAMES]
    lines = ["| 목표 \\ 출발 | " + " | ".join(srcs) + " | 평균 |", "|---|" + "---|" * (len(srcs) + 1)]
    for name in a.targets:
        row = [f"{results[name]['entry_fail'].get(s, float('nan')):.2f}" if s != name else "-" for s in srcs]
        lines.append(f"| {name} | " + " | ".join(row) + f" | {results[name]['entry_fail_mean']:.3f} |")
    table = "\n".join(lines)
    print(table)
    out = a.out or (ROOT / "runs/moving_state_bank" / f"eval_{a.label}_{time.strftime('%Y%m%d-%H%M%S')}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(dict(label=a.label, bank=a.bank, args=vars(a) | {"out": str(out)}, results=results, table=table,
                   elapsed_sec=time.time() - t0), open(out, "w"), indent=1, ensure_ascii=False, default=str)
    print("저장:", out, f"({(time.time()-t0)/60:.1f}분)")


if __name__ == "__main__":
    main()
