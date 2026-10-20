"""완성 계보 환경의 의미가 바뀌지 않았는지 확인하는 회귀 테스트 (2026-10-20).

무엇을 잠그나: 완성 계보가 실제로 쓴 환경 설정(resolved_config.yaml의 environment.kwargs)으로
고정 시드·고정 행동열 300스텝을 돌린 결과 — 관측 차원, 총 리턴, 보상·비용 항별 합계, 종료 횟수,
마지막 무게중심 위치. 기준값은 tests/golden.json 에 있고, 네 환경 모두 같은 입력에 같은 출력을
내는 결정론 환경이라(재실행 차이 0) 허용 오차는 1e-6 이다.

왜 "항별 합계"인가: 어느 보상 항이 바뀌었는지 바로 가리키기 위해서다. 보상값은 info 항들의 단순
합이 아니므로(가중·부호 처리가 _get_rew 안에 있음) 분해 항등식 대신 항별 합계를 잠근다.

기준값에는 지금의 동작이 그대로 들어간다. plane_v3 의 종료 스텝 낙상 벌점이 0으로 적용되는
알려진 결함(is_terminated 이중 호출, docs/TECH_NOTES.md "알려진 함정")도 포함된다. 이 테스트는
"고치지 말라"가 아니라 "바뀌면 알아채라"는 뜻이다. 의도한 변경이면 기준값을 다시 만든다:

    /home/bong/anaconda3/envs/horcrux/bin/python tests/test_env_regression.py --update

실행:  /home/bong/anaconda3/envs/horcrux/bin/python -m pytest tests -q   (환경당 약 0.5초)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = Path(__file__).with_name("golden.json")
SEED = 123
N_STEPS = 300
TOL = 1e-6

# (이름, 환경 id, 환경 kwargs를 가져올 설정 파일). 설정 파일은 완성 계보가 실제로 쓴 것.
CASES = [
    ("forward_expert", "horcrux_env/plane-v0",
     "policies/path_tracking/forward/03_forward_delta0_continue_stage3/resolved_config.yaml"),
    ("ccw_rotation", "horcrux_env/plane-rotation-v0",
     "policies/rotation/ccw/05_ccw_v2_stage5/resolved_config.yaml"),
    ("unified_stage3", "horcrux_env/plane-unified-v0",
     "policies/unified/03_transition_stage3/resolved_config.yaml"),
    # 인계 시작 환경은 상태 은행(runs/ 아래, git 미추적)이 있어야 돈다. 없으면 건너뛴다.
    ("moving_init_iter4", "horcrux_env/plane-moving-init-v0",
     "training/configs/ppo_plane_forward_moving_init_iter4.yaml"),
]


def env_kwargs(cfg_path: str) -> dict:
    cfg = yaml.safe_load(open(ROOT / cfg_path, encoding="utf-8"))
    kw = dict(cfg["environment"]["kwargs"])
    bank = kw.get("bank_path")
    if bank and not (ROOT / bank).exists():
        pytest.skip(f"상태 은행이 없어 건너뜀: {bank}")
    if bank:
        kw["bank_path"] = str(ROOT / bank)
    return kw


def rollout(env_id: str, kw: dict) -> dict:
    import gymnasium as gym
    import horcrux_env  # noqa: F401  (환경 등록)

    env = gym.make(env_id, **kw)
    obs, _ = env.reset(seed=SEED)
    rng = np.random.default_rng(SEED)
    total, terms, n_term, n_trunc = 0.0, {}, 0, 0
    for _ in range(N_STEPS):
        action = rng.uniform(0.0, 2.7, size=env.action_space.shape).astype(np.float32)
        obs, r, te, tr, info = env.step(action)
        total += float(r)
        n_term += int(te)
        n_trunc += int(tr)
        for k, v in info.items():
            if k.startswith(("reward_", "cost_")) and np.ndim(v) == 0:
                terms[k] = terms.get(k, 0.0) + float(v)
        if te or tr:
            obs, _ = env.reset(seed=SEED + 1)
    com = [float(x) for x in np.asarray(info["com_pos"]).ravel()[:2]]
    env.close()
    return dict(obs_dim=int(obs.shape[0]), total_reward=total, terms=terms,
                n_terminated=n_term, n_truncated=n_trunc, final_com_xy=com)


def load_golden() -> dict:
    if not GOLDEN.exists():
        pytest.fail(f"기준값 파일이 없습니다: {GOLDEN}. `python tests/test_env_regression.py --update` 로 만드세요.")
    return json.load(open(GOLDEN, encoding="utf-8"))


@pytest.mark.parametrize("name,env_id,cfg", CASES, ids=[c[0] for c in CASES])
def test_env_semantics_unchanged(name: str, env_id: str, cfg: str) -> None:
    golden = load_golden()
    assert name in golden, f"기준값에 {name} 이 없습니다. --update 로 만드세요."
    got = rollout(env_id, env_kwargs(cfg))
    exp = golden[name]
    assert got["obs_dim"] == exp["obs_dim"], f"관측 차원 {exp['obs_dim']} → {got['obs_dim']}"
    assert got["n_terminated"] == exp["n_terminated"], f"종료 횟수 {exp['n_terminated']} → {got['n_terminated']}"
    assert got["n_truncated"] == exp["n_truncated"], f"절단 횟수 {exp['n_truncated']} → {got['n_truncated']}"
    assert set(got["terms"]) == set(exp["terms"]), f"보상·비용 항 목록이 바뀜: {sorted(set(got['terms']) ^ set(exp['terms']))}"
    changed = {k: (exp["terms"][k], got["terms"][k]) for k in exp["terms"]
               if abs(exp["terms"][k] - got["terms"][k]) > TOL * max(1.0, abs(exp["terms"][k]))}
    assert not changed, "항별 합계가 바뀜 (기준 → 지금): " + ", ".join(f"{k}: {a:.4f} → {b:.4f}" for k, (a, b) in changed.items())
    assert abs(got["total_reward"] - exp["total_reward"]) <= TOL * max(1.0, abs(exp["total_reward"])), \
        f"총 리턴 {exp['total_reward']:.4f} → {got['total_reward']:.4f}"
    assert np.allclose(got["final_com_xy"], exp["final_com_xy"], atol=TOL), \
        f"마지막 무게중심 {exp['final_com_xy']} → {got['final_com_xy']}"


def test_rollout_is_deterministic() -> None:
    """같은 시드·같은 행동열이면 같은 결과여야 기준값 비교가 뜻이 있다."""
    name, env_id, cfg = CASES[0]
    kw = env_kwargs(cfg)
    a, b = rollout(env_id, kw), rollout(env_id, kw)
    assert a["total_reward"] == b["total_reward"] and a["final_com_xy"] == b["final_com_xy"]


def update_golden() -> None:
    out = {}
    for name, env_id, cfg in CASES:
        try:
            kw = env_kwargs(cfg)
        except BaseException as e:  # pytest.skip 은 예외로 전달된다
            print(f"{name}: 건너뜀 ({e})")
            continue
        out[name] = rollout(env_id, kw)
        print(f"{name}: obs {out[name]['obs_dim']}, 리턴 {out[name]['total_reward']:.4f}, 종료 {out[name]['n_terminated']}")
    json.dump(out, open(GOLDEN, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("저장:", GOLDEN)


if __name__ == "__main__":
    if "--update" in sys.argv:
        update_golden()
    else:
        sys.exit(pytest.main([str(Path(__file__)), "-q"]))
