"""통합 정책 체크포인트 고정 시드 벤치마크 (2026-09-10 scratchpad 판을 CLI로 정리, 2026-09-14).

같은 무작위 전환 에피소드(시드 5000부터 N개, 결정론 행동, horizon 1000)로 후보 체크포인트들을 비교한다.
지표: 평균 리턴, 에피소드 길이, 완주율(종료 없이 1000스텝), 전환 뒤 100스텝 안 실패율(전체 / δ=203 도착: diag_fr·diag_bl).
전환 시작 위상 규칙(--align-rule)은 환경 kwargs로 넘긴다 — 같은 시드면 전환 일정은 같고 시작 위상만 규칙에 따라 다르다.

사용:
  python training/bench_unified_ckpts.py --out results/unified_bench/s3_vs_s4.json --align-rule lat \
      --cand "S3 final=policies/unified/03_transition_stage3/final_model.zip:policies/unified/03_transition_stage3/vecnormalize.pkl" \
      --cand "S4 final=runs/.../final_model.zip:runs/.../vecnormalize.pkl"
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))


def bench(name: str, model_path: str, vecnorm_path: str, env_kwargs: dict, n_ep: int, seed0: int = 5000) -> dict:
    import gymnasium as gym
    import horcrux_env  # noqa: F401
    import torch
    from horcrux_env.wrappers import NormalizeAction
    from distill_experts import Student

    torch.set_num_threads(2)
    vn = pickle.load(open(vecnorm_path, "rb"))
    pol = Student(Path(model_path), vn.obs_rms.mean, np.sqrt(vn.obs_rms.var + vn.epsilon), float(vn.clip_obs))
    env = NormalizeAction(gym.make("horcrux_env/plane-unified-v0", **env_kwargs))
    rets, lens, done_full = [], [], 0
    sw_total = sw_fail = sw203 = sw203_fail = 0
    episodes = []   # 에피소드별 기록 (2026-09-15): 같은 시드끼리 짝지은 비교용
    for ep in range(n_ep):
        raw, _ = env.reset(seed=seed0 + ep)
        ret, pending, t = 0.0, [], 0
        ep_sw = ep_fail = ep_203 = ep_203_fail = 0
        for t in range(1000):
            raw, r, te, tr, info = env.step(pol.act(raw))
            ret += r
            if info.get("switched"):
                pending.append([int(info["switch_to"]), 0])
                sw_total += 1
                ep_sw += 1
                if info["switch_to"] in (4, 6):
                    sw203 += 1
                    ep_203 += 1
            for p_ in pending:
                p_[1] += 1
            if te:
                for p_ in pending:
                    if p_[1] <= 100:
                        sw_fail += 1
                        ep_fail += 1
                        if p_[0] in (4, 6):
                            sw203_fail += 1
                            ep_203_fail += 1
                break
            pending = [p_ for p_ in pending if p_[1] <= 100]
            if tr:
                break
        rets.append(ret)
        lens.append(t + 1)
        done_full += int(not te)
        episodes.append(dict(seed=seed0 + ep, ret=float(ret), len=t + 1, terminated=bool(te), n_sw=ep_sw, n_fail=ep_fail, n203=ep_203, n203_fail=ep_203_fail))
    env.close()
    return dict(ret=float(np.mean(rets)), ret_sd=float(np.std(rets)), eplen=float(np.mean(lens)), survive=done_full / n_ep,
                fail100=sw_fail / max(sw_total, 1), fail203=sw203_fail / max(sw203, 1), n_sw=sw_total, n203=sw203, n_ep=n_ep,
                model=model_path, vecnorm=vecnorm_path, episodes=episodes)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", action="append", required=True, help='"이름=model.zip:vecnormalize.pkl" (반복)')
    ap.add_argument("--config", default=str(ROOT / "training/configs/ppo_unified_transition_stage3.yaml"), help="환경 kwargs를 가져올 설정")
    ap.add_argument("--align-rule", choices=("sign", "lat"), default="sign")
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    kw = dict(cfg["environment"]["kwargs"])
    kw["align_rule"] = a.align_rule
    t0 = time.time()
    res = {"align_rule": a.align_rule, "episodes": a.episodes, "config": a.config, "results": {}}
    for c in a.cand:
        name, rest = c.split("=", 1)
        mp_, vp = rest.split(":", 1)
        r = bench(name, mp_, vp, kw, a.episodes)
        res["results"][name] = r
        print(f"[{a.align_rule}] {name:14s} 리턴 {r['ret']:9,.0f} ± {r['ret_sd']:6,.0f} | 길이 {r['eplen']:6.0f} | 완주율 {r['survive']:.2f} | "
              f"전환실패(100) {r['fail100']:.3f} ({r['n_sw']}) | δ=203 도착 실패 {r['fail203']:.2f} ({r['n203']})", flush=True)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(res, open(a.out, "w"), indent=1, ensure_ascii=False)
    print("저장:", a.out, f"({(time.time() - t0) / 60:.1f}분)")


if __name__ == "__main__":
    main()
