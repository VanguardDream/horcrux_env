"""전환 위상 선택 규칙 비교 — 학습 없이 평가만 한다.

전환(인계 시작) 순간에 목표 gait의 시작 위상 k를 고르는 네 가지 규칙을 같은 은행 상태에서 비교한다.
  k0    위상 0 재시작
  sign  부호 정렬 (현행): col = argmax_c <M_T[:, c], m_S>, 역재생 gait는 k = -col
  near  목표 궤도 최근접점: 은행(kind=det)에서 만든 목표 gait의 "패턴별 평균 (관절각, 관절각속도)" 표에 대해
        J_var = Σ_j Δθ_j²/σθ_j² + Σ_j Δθ̇_j²/σθ̇_j² 가 최소인 패턴 → 그 패턴을 갖는 열
  kin   운동 에너지 계량: J_kin = ½ Δθ̇ᵀ M_jj(θ) Δθ̇ (질량 행렬의 관절 블록) 가 최소인 패턴

모든 진입에 대해 선택 위상에서의 거리(J_var, J_kin)와 낙상 여부(post_steps 안 종료)를 기록해
"거리 vs 실패" 곡선과 규칙별 실패 행렬을 만든다. 진입 실행은 eval_expert_transitions.py와 같은
환경(plane-moving-init-v0, 정지 reset 후 set_state)과 같은 전문가 체크포인트를 쓴다.

사용:
  python training/eval_phase_rules.py --targets diag_fr diag_bl forward --states-per-source 20
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "training"))
from eval_expert_transitions import LINEAR, N_CMD, NAMES, default_ckpt, load_policy, make_env  # noqa: E402
from horcrux_env.envs.phase_align import align_column  # noqa: E402

Q_J, V_J = slice(7, 21), slice(6, 20)   # 자유 관절(7 qpos / 6 qvel) 뒤의 14개 힌지 관절
RULES = ("k0", "sign", "near", "kin")
KIND_DET = 0


def load_bank(path: str) -> dict:
    d = np.load(path)
    return {"qpos": np.asarray(d["qpos"], dtype=np.float64), "qvel": np.asarray(d["qvel"], dtype=np.float64),
            "mvec": np.asarray(d["mvec"], dtype=np.int8), "source": np.asarray(d["source"]), "kind": np.asarray(d["kind"])}


def pattern_key(vec) -> tuple:
    return tuple(int(x) for x in np.sign(vec))


class OrbitTable:
    """gait별 (모션 벡터 패턴 → 평균 관절각·각속도) 표와 분산 정규화 가중치. 은행의 결정론 상태만 쓴다."""

    def __init__(self, bank: dict, kind: int = KIND_DET):
        self.table, self.inv_var, self.n_states = {}, {}, {}
        for g in range(N_CMD):
            m = (bank["source"] == g) & (bank["kind"] == kind)
            q, v, mv = bank["qpos"][m][:, Q_J], bank["qvel"][m][:, V_J], bank["mvec"][m]
            groups: dict[tuple, list[int]] = {}
            for i, row in enumerate(mv):
                groups.setdefault(pattern_key(row), []).append(i)
            self.table[g] = {k: (q[idx].mean(0), v[idx].mean(0), len(idx)) for k, idx in groups.items()}
            self.inv_var[g] = (1.0 / (q.var(0) + 1e-6), 1.0 / (v.var(0) + 1e-6))
            self.n_states[g] = int(m.sum())

    def candidates(self, g: int, M: np.ndarray) -> list[tuple[tuple, int]]:
        """목표 gait 모션 행렬의 서로 다른 패턴(첫 등장 열)과 표에 있는 것만."""
        seen, out = set(), []
        for c in range(M.shape[1]):
            k = pattern_key(M[:, c])
            if k in seen:
                continue
            seen.add(k)
            if k in self.table[g]:
                out.append((k, c))
        return out

    def dist(self, g: int, key: tuple, q: np.ndarray, v: np.ndarray, Mjj: np.ndarray | None):
        """(J_var, J_kin) — 패턴이 표에 없으면 nan."""
        if key not in self.table[g]:
            return float("nan"), float("nan")
        qm, vm, _ = self.table[g][key]
        ivq, ivv = self.inv_var[g]
        j_var = float(((q - qm) ** 2 * ivq).sum() + ((v - vm) ** 2 * ivv).sum())
        dv = v - vm
        j_kin = float(0.5 * dv @ Mjj @ dv) if Mjj is not None else float("nan")
        return j_var, j_kin


def choose_column(rule: str, gait, cands, table: OrbitTable, g: int, q, v, m_src, Mjj) -> int:
    M = gait.MotionMatrix
    if rule == "k0":
        return 0
    if rule in ("sign", "lat"):
        # 환경과 같은 구현(horcrux_env/envs/phase_align.py): sign = 현행 부호 정렬, lat = 가로 부호 우선
        return align_column(M, m_src, rule)
    if rule == "signmom":
        # 부호 정렬의 근소 동점(최대−2 이내) 가운데, 토크 방향이 지금 속도와 반대인 관절들의 운동 에너지가 가장 작은 열
        agree = (M * m_src[:, None]).sum(axis=0)
        inertia = np.diag(Mjj)
        best, best_col, seen = None, int(np.argmax(agree)), set()
        for c in np.flatnonzero(agree >= agree.max() - 2):
            key = pattern_key(M[:, c])
            if key in seen:
                continue
            seen.add(key)
            conflict = (M[:, c] * v) < 0
            cost = float(0.5 * np.sum(inertia * v ** 2 * conflict))
            if best is None or cost < best:
                best, best_col = cost, int(c)
        return best_col
    best, best_col = None, 0
    for key, col in cands:
        j_var, j_kin = table.dist(g, key, q, v, Mjj)
        j = j_var if rule == "near" else j_kin
        if best is None or j < best:
            best, best_col = j, col
    return best_col


def col_to_k(gait, col: int) -> int:
    return -col if gait._reverse else col


def mass_matrix_joint_block(base) -> np.ndarray:
    full = np.zeros((base.model.nv, base.model.nv))
    mujoco.mj_fullM(base.model, base.data, full)   # MuJoCo 3.x: (model, data, dst)
    return full[V_J, V_J]


def run_entry(env, base, act, qpos, qvel, k: int, post_steps: int):
    env.reset()
    base.set_state(qpos.copy(), qvel.copy())
    base._k = int(k)
    base._motion_vector = base._gait.getMvec(base._k).copy()
    raw = base._get_obs(base._motion_vector)
    t = 0
    for t in range(post_steps):
        raw, _, te, tr, _ = env.step(act(raw))
        if te:
            return True, t + 1
        if tr:
            break
    return False, t + 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default=str(ROOT / "runs/moving_state_bank/bank_iter1.npz"))
    ap.add_argument("--targets", nargs="+", default=LINEAR)
    ap.add_argument("--rules", nargs="+", default=list(RULES))
    ap.add_argument("--override", action="append", default=[], help="cmd=model.zip:vecnormalize.pkl")
    ap.add_argument("--states-per-source", type=int, default=20)
    ap.add_argument("--post-steps", type=int, default=150)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--label", default="phase_rules")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    overrides = {}
    for o in a.override:
        k, val = o.split("=", 1)
        m, vn = val.split(":", 1)
        overrides[k] = (Path(m), Path(vn))

    t0 = time.time()
    bank = load_bank(a.bank)
    table = OrbitTable(bank)
    rng = np.random.default_rng(a.seed)
    picks = {}
    for s in range(N_CMD):
        idx = np.flatnonzero((bank["source"] == s) & (bank["kind"] == KIND_DET))
        picks[s] = rng.choice(idx, size=min(a.states_per_source, len(idx)), replace=False)

    records = []
    for name in a.targets:
        g = NAMES.index(name)
        m_path, vn_path = overrides.get(name, default_ckpt(name))
        act = load_policy(m_path, vn_path)
        env = make_env(g, a.seed, None, None, 0.0)
        base = env.unwrapped
        cands = table.candidates(g, base._gait.MotionMatrix)
        print(f"[{name}] 궤도 표 패턴 {len(table.table[g])}개 (상태 {table.n_states[g]:,}), 후보 열 {len(cands)}개", flush=True)
        for s in range(N_CMD):
            if s == g:
                continue
            for i in picks[s]:
                qpos, qvel, m_src = bank["qpos"][i], bank["qvel"][i], bank["mvec"][i].astype(np.float64)
                env.reset()
                base.set_state(qpos.copy(), qvel.copy())
                Mjj = mass_matrix_joint_block(base)
                q, v = qpos[Q_J], qvel[V_J]
                for rule in a.rules:
                    if rule == "all":
                        # 후보 패턴 전부 시도 — 상태별 '어떤 위상이든 되는가'(오라클)와 거리-실패 관계용
                        trials = [(f"all", col) for _, col in cands]
                    else:
                        trials = [(rule, choose_column(rule, base._gait, cands, table, g, q, v, m_src, Mjj))]
                    for rname, col in trials:
                        k = col_to_k(base._gait, col)
                        j_var, j_kin = table.dist(g, pattern_key(base._gait.MotionMatrix[:, col]), q, v, Mjj)
                        fail, steps = run_entry(env, base, act, qpos, qvel, k, a.post_steps)
                        records.append(dict(target=name, source=NAMES[s], state=int(i), rule=rname, col=int(col), k=int(k),
                                            j_var=j_var, j_kin=j_kin, fail=bool(fail), steps=int(steps)))
            done = [r for r in records if r["target"] == name and r["source"] == NAMES[s]]
            summary = " ".join(f"{rule} {np.mean([r['fail'] for r in done if r['rule'] == rule]):.2f}" for rule in a.rules)
            print(f"  {name:8s} ← {NAMES[s]:8s} | {summary}", flush=True)
        env.close()

    # 요약: 규칙별 실패 행렬
    lines = ["| 목표 | 규칙 | " + " | ".join(NAMES) + " | 평균 |", "|---|---|" + "---|" * (N_CMD + 1)]
    summary = {}
    for name in a.targets:
        summary[name] = {}
        for rule in a.rules:
            row, vals = [], []
            for s in NAMES:
                if s == name:
                    row.append("-")
                    continue
                f = [r["fail"] for r in records if r["target"] == name and r["rule"] == rule and r["source"] == s]
                vals.append(float(np.mean(f)))
                row.append(f"{vals[-1]:.2f}")
            summary[name][rule] = dict(per_source=dict(zip([s for s in NAMES if s != name], vals)), mean=float(np.mean(vals)))
            lines.append(f"| {name} | {rule} | " + " | ".join(row) + f" | {np.mean(vals):.3f} |")
    print("\n".join(lines))
    out = a.out or (ROOT / "results/moving_state_bank" / f"eval_{a.label}.json")   # git 추적 폴더 (2026-10-20)
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(dict(label=a.label, bank=a.bank, args=vars(a) | {"out": str(out)}, rules=a.rules, targets=a.targets,
                   n_patterns={NAMES[g]: len(table.table[g]) for g in range(N_CMD)}, summary=summary, records=records,
                   table="\n".join(lines), elapsed_sec=time.time() - t0), open(out, "w"), indent=1, ensure_ascii=False, default=str)
    print("저장:", out, f"({(time.time() - t0) / 60:.1f}분)")


if __name__ == "__main__":
    main()
