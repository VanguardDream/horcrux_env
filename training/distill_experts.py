"""10명 방위/회전 전문가 → 단일 명령 조건부 정책 증류 (Phase B).

전환 학습(PPO 미세조정)의 출발점을 만든다. RL로 9개 명령을 새로 익히는
불확실성을 피하기 위해, 이미 있는 전문가 행동을 지도학습(BC)으로 한
네트워크에 옮겨 담고 PPO 체크포인트 형식으로 저장한다.

단계 (각 단계 산출물은 out/ 아래에 캐시되어 재실행 시 건너뛸 수 있다):
  1. collect   전문가 10명을 통합 환경(명령 고정)에서 굴려 (원본 관측, 전문가
               행동[-1,1], 보상, 에피소드 경계) 기록. 명령별 병렬(spawn).
  2. normalize 전체 관측으로 통합 obs_rms 생성 (학생 전용 VecNormalize).
  3. bc        PPO MlpPolicy와 같은 구조의 학생을 만들어 actor를 MSE로 모방,
               critic은 할인 누적 보상(MC return)에 회귀. log_std는 보수적으로.
  4. dagger    (선택) 학생을 굴려 방문 상태에 전문가 라벨을 달아 데이터에 합친
               뒤 재학습 — 오차 누적 보정.
  5. eval      명령별 학생 vs 전문가 (리턴·진행 속도·낙상률·회전 지표).
  6. package   out/model.zip + vecnormalize.pkl + metadata.json + DISTILL_REPORT.md

사용:
  python training/distill_experts.py --config training/configs/ppo_unified_transition_stage1.yaml \
      --out policies/unified/00_distilled
  python training/distill_experts.py ... --skip-collect --dagger-rounds 1   # 캐시 재사용 + 보정
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

from path_following import EXPERT_PATHS  # noqa: E402  (evaluation/best 조합)
from horcrux_env.envs.gait_provider import VALIDATED_COMMANDS  # noqa: E402

N_CMD = len(VALIDATED_COMMANDS)
CMD_NAMES = [c[0] for c in VALIDATED_COMMANDS]


# ----------------------------------------------------------------------------- 환경/전문가 유틸
def load_env_kwargs(config_path: Path) -> dict:
    """RL 설정 YAML의 environment.kwargs를 그대로 쓰되, 전문가 롤아웃용으로
    전환 커리큘럼은 끈다 (전문가는 전환을 모른다). 보상·종료 의미는 RL과 동일."""
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    kw = dict(cfg["environment"].get("kwargs", {}))
    kw.update(switch_enabled=False, random_init_phase=False)
    kw.pop("command_weights", None)
    return kw


def make_env(env_kwargs: dict, command_id: int | None, seed: int):
    import gymnasium as gym
    import horcrux_env  # noqa: F401
    from horcrux_env.wrappers import NormalizeAction

    kw = dict(env_kwargs)
    if command_id is not None:
        w = np.zeros(N_CMD)
        w[command_id] = 1.0
        kw["command_weights"] = w
    env = NormalizeAction(gym.make("horcrux_env/plane-unified-v0", **kw))
    env.reset(seed=seed)
    return env


class Expert:
    """전문가 정책 + 자기 관측 정규화 통계 (path_following.ExpertBank와 동일 규약)."""

    def __init__(self, command_id: int, device: str = "cpu"):
        from stable_baselines3 import PPO

        base = ROOT / EXPERT_PATHS[CMD_NAMES[command_id]] / "evaluation"
        self.model = PPO.load(str(base / "best_model.zip"), device=device)
        with open(base / "best_model_vecnormalize.pkl", "rb") as f:
            vn = pickle.load(f)
        self.mean = vn.obs_rms.mean.copy()
        self.std = np.sqrt(vn.obs_rms.var + vn.epsilon)
        self.clip = float(vn.clip_obs)

    def act(self, raw_obs: np.ndarray, deterministic: bool = True) -> np.ndarray:
        obs = np.clip((raw_obs - self.mean) / self.std, -self.clip, self.clip).astype(np.float32)
        a, _ = self.model.predict(obs, deterministic=deterministic)
        return a.astype(np.float32)


class Student:
    """저장된 학생(PPO) + 통합 정규화 통계로 결정론적 행동."""

    def __init__(self, model_path: Path, mean: np.ndarray, std: np.ndarray, clip: float, device: str = "cpu"):
        from stable_baselines3 import PPO

        self.model = PPO.load(str(model_path), device=device)
        self.mean, self.std, self.clip = mean, std, clip

    def act(self, raw_obs: np.ndarray) -> np.ndarray:
        obs = np.clip((raw_obs - self.mean) / self.std, -self.clip, self.clip).astype(np.float32)
        a, _ = self.model.predict(obs, deterministic=True)
        return a.astype(np.float32)


# ----------------------------------------------------------------------------- 1. 수집 (워커)
def _collect_worker(args):
    """한 명령에 대해 actor(전문가 또는 학생)를 굴리고 전문가 라벨을 기록한다."""
    (command_id, env_kwargs, n_steps, episode_cap, seed, actor_spec, stochastic_steps) = args
    import torch

    torch.set_num_threads(1)
    env = make_env(env_kwargs, command_id, seed)
    expert = Expert(command_id)
    if actor_spec is None:
        actor = expert
    else:  # DAgger: 학생이 행동, 전문가가 라벨
        actor = Student(Path(actor_spec["model_path"]), np.asarray(actor_spec["mean"]),
                        np.asarray(actor_spec["std"]), float(actor_spec["clip"]))

    obs_buf, act_buf, rew_buf, term_buf, trunc_buf = [], [], [], [], []
    raw, _ = env.reset()
    ep_len = 0
    total = n_steps + (stochastic_steps if actor is expert else 0)
    while len(obs_buf) < total:
        label = expert.act(raw)
        if actor is expert:
            # 앞 n_steps는 결정론적 전문가, 이후는 전문가 자체 가우시안으로 샘플한
            # 행동을 실행 (DART식 노이즈 주입) — 상태 분포/정규화 통계를 넓혀
            # 공변량 이동을 줄인다. 라벨은 항상 결정론적 평균 행동.
            a = label if len(obs_buf) < n_steps else expert.act(raw, deterministic=False)
        else:
            a = actor.act(raw)
        nxt, r, terminated, truncated, info = env.step(a)
        ep_len += 1
        cap_hit = ep_len >= episode_cap
        obs_buf.append(raw.astype(np.float32))
        act_buf.append(label)
        rew_buf.append(float(r))
        term_buf.append(bool(terminated))
        trunc_buf.append(bool(truncated or cap_hit) and not terminated)
        if terminated or truncated or cap_hit:
            raw, _ = env.reset()
            ep_len = 0
        else:
            raw = nxt
    env.close()
    return command_id, (np.asarray(obs_buf), np.asarray(act_buf), np.asarray(rew_buf, dtype=np.float32),
                        np.asarray(term_buf), np.asarray(trunc_buf))


def collect(env_kwargs: dict, n_steps: int, episode_cap: int, seed: int, actor_spec=None, workers: int = N_CMD,
            stochastic_steps: int = 0):
    jobs = [(c, env_kwargs, n_steps, episode_cap, seed + 1000 * c, actor_spec, stochastic_steps) for c in range(N_CMD)]
    ctx = mp.get_context("spawn")
    with ctx.Pool(min(workers, N_CMD)) as pool:
        results = dict(pool.map(_collect_worker, jobs))
    obs = np.concatenate([results[c][0] for c in range(N_CMD)])
    act = np.concatenate([results[c][1] for c in range(N_CMD)])
    rew = np.concatenate([results[c][2] for c in range(N_CMD)])
    term = np.concatenate([results[c][3] for c in range(N_CMD)])
    trunc = np.concatenate([results[c][4] for c in range(N_CMD)])
    cmd = np.concatenate([np.full(len(results[c][0]), c, dtype=np.int64) for c in range(N_CMD)])
    return dict(obs=obs, act=act, rew=rew, term=term, trunc=trunc, cmd=cmd)


def mc_returns(rew: np.ndarray, term: np.ndarray, trunc: np.ndarray, gamma: float, horizon_mask: int):
    """에피소드별 할인 누적 보상과 유효 마스크.

    절단(truncated)된 에피소드의 꼬리 horizon_mask 스텝은 미래 보상이 잘려
    return이 과소평가되므로 critic 학습에서 제외한다. 종료(terminated)된
    에피소드는 정확한 return이라 전부 유효하다."""
    n = len(rew)
    ret = np.zeros(n, dtype=np.float64)
    valid = np.ones(n, dtype=bool)
    g = 0.0
    steps_to_end = 0
    ended_by_trunc = False
    for i in range(n - 1, -1, -1):
        if term[i] or trunc[i]:
            g = 0.0
            steps_to_end = 0
            ended_by_trunc = bool(trunc[i])
        g = rew[i] + gamma * g
        ret[i] = g
        if ended_by_trunc and steps_to_end < horizon_mask:
            valid[i] = False
        steps_to_end += 1
    return ret.astype(np.float32), valid


# ----------------------------------------------------------------------------- 3. 학생 구축/BC
def build_student(env_kwargs: dict, cfg: dict, mean: np.ndarray, var: np.ndarray, count: float, seed: int, device: str):
    """RL 설정과 동일한 PPO 하이퍼파라미터/구조로 학생을 만들고 통합 정규화 통계를 심는다."""
    import torch.nn as nn
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    venv = DummyVecEnv([lambda: make_env(env_kwargs, None, seed)])
    norm_cfg = cfg["normalization"]
    vnorm = VecNormalize(venv, training=False, norm_obs=True,
                         norm_reward=bool(norm_cfg.get("norm_reward", False)),
                         clip_obs=float(norm_cfg.get("clip_obs", 10.0)),
                         epsilon=float(norm_cfg.get("epsilon", 1e-8)))
    vnorm.obs_rms.mean[:] = mean
    vnorm.obs_rms.var[:] = var
    vnorm.obs_rms.count = float(count)

    alg = cfg["algorithm"]
    pk = dict(alg.get("policy_kwargs", {}))
    act_name = str(pk.pop("activation_fn", "tanh")).lower()
    pk["activation_fn"] = {"tanh": nn.Tanh, "relu": nn.ReLU, "elu": nn.ELU}[act_name]
    kw = dict(alg.get("kwargs", {}))
    model = PPO(alg.get("policy", "MlpPolicy"), vnorm, seed=seed, device=device, policy_kwargs=pk,
                verbose=0, **kw)
    return model, vnorm


def bc_train(model, X: np.ndarray, Y: np.ndarray, G: np.ndarray, valid: np.ndarray, cmd: np.ndarray,
             epochs: int, batch_size: int, lr: float, device: str, log_every: int = 5):
    """actor: MSE(평균 행동, 전문가 행동). critic: MSE(가치, MC return) — 별도 옵티마이저."""
    import torch

    policy = model.policy
    policy.set_training_mode(True)
    actor_params = list(policy.mlp_extractor.policy_net.parameters()) + list(policy.action_net.parameters())
    critic_params = list(policy.mlp_extractor.value_net.parameters()) + list(policy.value_net.parameters())
    opt_a = torch.optim.Adam(actor_params, lr=lr)
    opt_c = torch.optim.Adam(critic_params, lr=lr)

    n = len(X)
    rng = np.random.default_rng(0)
    perm = rng.permutation(n)
    n_val = max(int(0.05 * n), 1)
    val_idx, tr_idx = perm[:n_val], perm[n_val:]
    Xt = torch.as_tensor(X, device=device)
    Yt = torch.as_tensor(Y, device=device)
    Gt = torch.as_tensor(G, device=device)
    Vt = torch.as_tensor(valid, device=device)
    g_scale = float(np.std(G[valid]) + 1e-6)  # 가치 손실 스케일 정규화 (보상 단위가 커서)
    with torch.no_grad():  # critic 출력 편향을 return 평균으로 초기화 (수렴 가속)
        policy.value_net.bias.fill_(float(np.mean(G[valid])))

    steps_per_epoch = int(np.ceil(len(tr_idx) / batch_size))
    sched_a = torch.optim.lr_scheduler.CosineAnnealingLR(opt_a, T_max=epochs * steps_per_epoch)
    sched_c = torch.optim.lr_scheduler.CosineAnnealingLR(opt_c, T_max=epochs * steps_per_epoch)
    history = []

    def forward(idx):
        feats = policy.extract_features(Xt[idx])
        lat_pi, lat_vf = policy.mlp_extractor(feats)
        return policy.action_net(lat_pi), policy.value_net(lat_vf).squeeze(-1)

    for ep in range(epochs):
        rng.shuffle(tr_idx)
        loss_a_sum = loss_c_sum = 0.0
        for b in range(steps_per_epoch):
            idx = torch.as_tensor(tr_idx[b * batch_size:(b + 1) * batch_size], device=device)
            mean_a, value = forward(idx)
            loss_a = torch.mean((mean_a - Yt[idx]) ** 2)
            vmask = Vt[idx]
            loss_c = torch.mean(((value - Gt[idx]) / g_scale) ** 2 * vmask) / (vmask.float().mean() + 1e-6)
            opt_a.zero_grad(); loss_a.backward(); opt_a.step(); sched_a.step()
            opt_c.zero_grad(); loss_c.backward(); opt_c.step(); sched_c.step()
            loss_a_sum += loss_a.item(); loss_c_sum += loss_c.item()
        with torch.no_grad():
            vi = torch.as_tensor(val_idx, device=device)
            mean_a, value = forward(vi)
            val_a = float(torch.mean((mean_a - Yt[vi]) ** 2))
            vmask = Vt[vi]
            val_c = float(torch.mean(((value - Gt[vi]) / g_scale) ** 2 * vmask) / (vmask.float().mean() + 1e-6))
            # 명령별 검증 MSE (약한 명령 탐지)
            per_cmd = {}
            cmd_v = cmd[val_idx]
            err = ((mean_a - Yt[vi]) ** 2).mean(dim=1).cpu().numpy()
            for c in range(N_CMD):
                m = cmd_v == c
                per_cmd[CMD_NAMES[c]] = float(err[m].mean()) if m.any() else float("nan")
        history.append(dict(epoch=ep + 1, train_actor=loss_a_sum / steps_per_epoch,
                            train_critic=loss_c_sum / steps_per_epoch, val_actor=val_a, val_critic=val_c,
                            val_actor_per_cmd=per_cmd))
        if (ep + 1) % log_every == 0 or ep == 0 or ep + 1 == epochs:
            worst = max(per_cmd.items(), key=lambda kv: kv[1])
            print(f"  [BC] epoch {ep+1:3d}/{epochs}  actor tr {loss_a_sum/steps_per_epoch:.5f} val {val_a:.5f}"
                  f"  critic tr {loss_c_sum/steps_per_epoch:.4f} val {val_c:.4f}  worst cmd {worst[0]} {worst[1]:.5f}",
                  flush=True)
    policy.set_training_mode(False)
    return history


# ----------------------------------------------------------------------------- 5. 평가 (워커)
def _eval_worker(args):
    (command_id, env_kwargs, n_episodes, episode_cap, seed, student_spec) = args
    import torch

    torch.set_num_threads(1)
    expert = Expert(command_id)
    student = Student(Path(student_spec["model_path"]), np.asarray(student_spec["mean"]),
                      np.asarray(student_spec["std"]), float(student_spec["clip"]))
    joy = np.asarray(VALIDATED_COMMANDS[command_id][1], dtype=np.float64)
    is_rot = abs(joy[2]) > 0.5
    out = {}
    for name, actor in (("expert", expert), ("student", student)):
        env = make_env(env_kwargs, command_id, seed)
        rets, lens, falls, prog, yaw_rates, anchors = [], [], [], [], [], []
        for ep in range(n_episodes):
            raw, _ = env.reset(seed=seed + ep)
            com0 = None
            ret = 0.0
            yr, an = [], []
            for t in range(episode_cap):
                raw, r, terminated, truncated, info = env.step(actor.act(raw))
                if com0 is None:
                    com0 = np.asarray(info["com_pos"][:2], dtype=np.float64)
                ret += float(r)
                if is_rot:
                    yr.append(float(info.get("aligned_yaw_vel", 0.0)))
                    an.append(float(info.get("anchor_distance", 0.0)))
                if terminated or truncated:
                    break
            n_steps = t + 1
            com1 = np.asarray(info["com_pos"][:2], dtype=np.float64)
            rets.append(ret); lens.append(n_steps); falls.append(bool(terminated))
            if is_rot:
                yaw_rates.append(float(np.mean(yr))); anchors.append(float(np.max(an)))
            else:
                prog.append(float((com1 - com0) @ joy[:2] / (n_steps * 0.05)))
        env.close()
        out[name] = dict(
            return_mean=float(np.mean(rets)), eplen_mean=float(np.mean(lens)), fall_rate=float(np.mean(falls)),
            progress_vel=float(np.mean(prog)) if prog else None,
            aligned_yaw_vel=float(np.mean(yaw_rates)) if yaw_rates else None,
            anchor_max=float(np.mean(anchors)) if anchors else None,
        )
    return command_id, out


def evaluate(env_kwargs: dict, n_episodes: int, episode_cap: int, seed: int, student_spec: dict, workers: int = N_CMD):
    jobs = [(c, env_kwargs, n_episodes, episode_cap, seed + 7919 * c, student_spec) for c in range(N_CMD)]
    ctx = mp.get_context("spawn")
    with ctx.Pool(min(workers, N_CMD)) as pool:
        return dict(pool.map(_eval_worker, jobs))


def report_table(results: dict) -> str:
    rows = ["| 명령 | 전문가 리턴 | 학생 리턴 | 비율 | 전문가 낙상 | 학생 낙상 | 진행속도/yaw (전문가→학생) |",
            "|---|---:|---:|---:|---:|---:|---|"]
    for c in range(N_CMD):
        e, s = results[c]["expert"], results[c]["student"]
        ratio = s["return_mean"] / e["return_mean"] if e["return_mean"] > 0 else float("nan")
        if e["progress_vel"] is not None:
            extra = f"{e['progress_vel']:.3f} → {s['progress_vel']:.3f} m/s"
        else:
            extra = (f"yaw {e['aligned_yaw_vel']:.3f} → {s['aligned_yaw_vel']:.3f} rad/s, "
                     f"앵커max {e['anchor_max']:.2f} → {s['anchor_max']:.2f} m")
        rows.append(f"| {CMD_NAMES[c]} | {e['return_mean']:,.0f} | {s['return_mean']:,.0f} | {ratio:.2f} | "
                    f"{e['fall_rate']:.2f} | {s['fall_rate']:.2f} | {extra} |")
    return "\n".join(rows)


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=ROOT / "training/configs/ppo_unified_transition_stage1.yaml")
    ap.add_argument("--out", type=Path, default=ROOT / "policies/unified/00_distilled")
    ap.add_argument("--steps-per-command", type=int, default=40000, help="결정론적 전문가 롤아웃 스텝/명령")
    ap.add_argument("--stochastic-steps-per-command", type=int, default=40000,
                    help="전문가 자체 노이즈로 실행한 롤아웃 스텝/명령 (DART식; 라벨은 평균 행동). 0이면 끔")
    ap.add_argument("--episode-cap", type=int, default=1500)
    ap.add_argument("--bc-epochs", type=int, default=30)
    ap.add_argument("--bc-batch", type=int, default=4096)
    ap.add_argument("--bc-lr", type=float, default=3e-4)
    ap.add_argument("--log-std", type=float, default=-1.2, help="학생 초기 log_std (방위 전문가 평균 -1.1 근처, 보수적)")
    ap.add_argument("--dagger-rounds", type=int, default=0)
    ap.add_argument("--dagger-steps-per-command", type=int, default=20000)
    ap.add_argument("--dagger-epochs", type=int, default=10)
    ap.add_argument("--eval-episodes", type=int, default=10)
    ap.add_argument("--eval-cap", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=N_CMD)
    ap.add_argument("--skip-collect", action="store_true", help="out/dataset.npz 재사용")
    ap.add_argument("--init-model", type=Path, default=None,
                    help="저장된 학생(model.zip)의 가중치에서 이어서 진행. out/의 기존 dataset_dagger_r*.npz도 합쳐 "
                         "DAgger 라운드를 이어 번호 매긴다 (예: cw 보강용 추가 라운드)")
    ap.add_argument("--skip-eval", action="store_true")
    a = ap.parse_args()

    a.out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load(a.config.read_text(encoding="utf-8"))
    env_kwargs = load_env_kwargs(a.config)
    gamma = float(cfg["algorithm"]["kwargs"].get("gamma", 0.99))
    horizon_mask = int(3.0 / (1.0 - gamma))
    t0 = time.time()
    meta = dict(config=str(a.config), experts=EXPERT_PATHS, gamma=gamma, log_std_init=a.log_std,
                args={k: (str(v) if isinstance(v, Path) else v) for k, v in vars(a).items()})

    # 1. 수집
    ds_path = a.out / "dataset.npz"
    if a.skip_collect and ds_path.exists():
        d = dict(np.load(ds_path))
        print(f"[1/6] 데이터셋 캐시 로드: {len(d['obs']):,} 샘플")
    else:
        print(f"[1/6] 전문가 롤아웃 수집: 명령당 결정론 {a.steps_per_command:,} + 확률적 {a.stochastic_steps_per_command:,} 스텝 "
              f"(워커 {min(a.workers, N_CMD)})", flush=True)
        d = collect(env_kwargs, a.steps_per_command, a.episode_cap, a.seed, workers=a.workers,
                    stochastic_steps=a.stochastic_steps_per_command)
        np.savez_compressed(ds_path, **d)
        print(f"      완료 {len(d['obs']):,} 샘플, {time.time()-t0:.0f}s")
    meta["n_samples_bc"] = int(len(d["obs"]))

    # 2. 통합 정규화 통계
    mean = d["obs"].astype(np.float64).mean(axis=0)
    var = d["obs"].astype(np.float64).var(axis=0)
    count = float(len(d["obs"]))
    eps = float(cfg["normalization"].get("epsilon", 1e-8))
    clip = float(cfg["normalization"].get("clip_obs", 10.0))
    std = np.sqrt(var + eps)
    tiny = int((np.sqrt(var) < 1e-3).sum())
    print(f"[2/6] 통합 obs_rms 생성 (count {count:,.0f}) — std<1e-3 차원 {tiny}/{len(var)} (클리핑 취약 차원)")
    meta["n_tiny_std_dims"] = tiny

    # 3. 학생 + BC
    print(f"[3/6] 학생 구축 + BC (epochs {a.bc_epochs}, gamma {gamma}, return 마스크 {horizon_mask} 스텝)", flush=True)
    model, vnorm = build_student(env_kwargs, cfg, mean, var, count, a.seed, a.device)
    import torch
    with torch.no_grad():
        model.policy.log_std.fill_(a.log_std)
    if a.init_model is not None:
        from stable_baselines3 import PPO
        model.policy.load_state_dict(PPO.load(str(a.init_model), device=a.device).policy.state_dict())
        print(f"      학생 가중치 로드: {a.init_model}")

    def normalize(obs):
        return np.clip((obs - mean) / std, -clip, clip).astype(np.float32)

    X = normalize(d["obs"]); Y = d["act"].astype(np.float32)
    G, valid = mc_returns(d["rew"], d["term"], d["trunc"], gamma, horizon_mask)
    print(f"      critic 유효 샘플 {valid.mean()*100:.1f}%  return 범위 [{G[valid].min():,.0f}, {G[valid].max():,.0f}]")
    cmd_all = d["cmd"]
    hist = []
    if a.bc_epochs > 0:
        hist = bc_train(model, X, Y, G, valid, cmd_all, a.bc_epochs, a.bc_batch, a.bc_lr, a.device)
    meta["bc_history"] = hist

    model_path = a.out / "model.zip"
    vn_path = a.out / "vecnormalize.pkl"
    model.save(model_path); vnorm.save(vn_path)
    student_spec = dict(model_path=str(model_path), mean=mean.tolist(), std=std.tolist(), clip=clip)

    # 4. DAgger
    def append_round(dd):
        nonlocal X, Y, G, valid, cmd_all
        X = np.concatenate([X, normalize(dd["obs"])]); Y = np.concatenate([Y, dd["act"].astype(np.float32)])
        Gd, vd = mc_returns(dd["rew"], dd["term"], dd["trunc"], gamma, horizon_mask)
        G = np.concatenate([G, Gd]); valid = np.concatenate([valid, vd]); cmd_all = np.concatenate([cmd_all, dd["cmd"]])

    start_round = 0
    if a.init_model is not None:  # 기존 DAgger 라운드 데이터를 합쳐 이어간다
        prior = sorted(a.out.glob("dataset_dagger_r*.npz"), key=lambda f: int(f.stem.rsplit("_r", 1)[1]))
        for f in prior:
            append_round(dict(np.load(f)))
        start_round = len(prior)
        if prior:
            print(f"      기존 DAgger 데이터 {len(prior)}라운드 합침 → 총 {len(X):,} 샘플")
    for r in range(start_round, start_round + a.dagger_rounds):
        print(f"[4/6] DAgger round {r+1} (이번 실행 {r-start_round+1}/{a.dagger_rounds}): "
              f"학생 롤아웃 명령당 {a.dagger_steps_per_command:,} 스텝", flush=True)
        dd = collect(env_kwargs, a.dagger_steps_per_command, a.episode_cap, a.seed + 100 * (r + 1),
                     actor_spec=student_spec, workers=a.workers)
        np.savez_compressed(a.out / f"dataset_dagger_r{r+1}.npz", **dd)
        append_round(dd)
        hist = bc_train(model, X, Y, G, valid, cmd_all, a.dagger_epochs, a.bc_batch, a.bc_lr * 0.5, a.device)
        meta[f"dagger_r{r+1}_history"] = hist
        meta[f"dagger_r{r+1}_samples"] = int(len(dd["obs"]))
        model.save(model_path); vnorm.save(vn_path)

    # 5. 평가
    if not a.skip_eval:
        print(f"[5/6] 평가: 명령별 학생 vs 전문가 {a.eval_episodes} 에피소드", flush=True)
        results = evaluate(env_kwargs, a.eval_episodes, a.eval_cap, a.seed + 555, student_spec, workers=a.workers)
        table = report_table(results)
        print(table)
        meta["eval"] = {CMD_NAMES[c]: results[c] for c in range(N_CMD)}
        ratios = [results[c]["student"]["return_mean"] / max(results[c]["expert"]["return_mean"], 1e-6) for c in range(N_CMD)]
        meta["eval_min_ratio"] = float(min(ratios))
    else:
        table = "(평가 생략)"

    # 6. 패키징
    meta["elapsed_sec"] = time.time() - t0
    (a.out / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    report = [
        "# 전문가 증류 리포트",
        f"- 생성: {time.strftime('%Y-%m-%d %H:%M:%S')}  | 소요 {meta['elapsed_sec']/60:.1f}분",
        f"- 데이터: BC {meta['n_samples_bc']:,} 샘플" + "".join(
            f", DAgger r{r+1} {meta[f'dagger_r{r+1}_samples']:,}" for r in range(start_round + a.dagger_rounds)
            if f"dagger_r{r+1}_samples" in meta) + f" (학습에 쓴 총 {len(X):,})",
        f"- gamma {gamma}, log_std 초기값 {a.log_std}, BC epochs {a.bc_epochs}"
        + (f", 이어서 진행: {a.init_model}" if a.init_model is not None else ""),
        (f"- 최종 검증 MSE: actor {hist[-1]['val_actor']:.5f}, critic(정규화) {hist[-1]['val_critic']:.4f}"
         if hist else "- (이번 실행에서 BC/DAgger 학습 없음)"),
        "",
        "## 명령별 학생 vs 전문가",
        table,
        "",
        "## 산출물",
        "- model.zip (PPO 체크포인트, 전환 학습 YAML의 resume.model_path)",
        "- vecnormalize.pkl (통합 obs_rms — 반드시 model.zip과 쌍으로)",
        "- dataset*.npz (수집 데이터, 재실행/보정용)",
    ]
    (a.out / "DISTILL_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"[6/6] 저장: {a.out}  ({meta['elapsed_sec']/60:.1f}분)")


if __name__ == "__main__":
    main()
