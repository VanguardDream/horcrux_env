"""전환 위상 선택 근거 덱용 그림 생성.

F1 serpenoid_sign      기준 관절각과 모션 벡터(가속도 부호 = 각도 부호의 반대)
F2 delta180            δ와 δ+180의 가로 파동 반전, 목표 열별 부호 일치(집안 안/밖)
F3 agreement_heatmap   10×10 부호 일치 상한 (위상 정렬 후 최대 내적)
F4 robot_joints        로봇 렌더 위에 세로(홀수)/가로(짝수) 관절 표시
F5 phase_portrait      은행에서 본 목표 gait 주기 궤도 + 현재 상태 + 부호 규칙/최근접 규칙 선택점 + J(k) 곡선
F6 distance_vs_failure 진입 거리 vs 실패 확률 (실험 JSON 필요)
F7 rule_comparison     규칙별 실패 비율 (실험 JSON 필요)
F8 schematic_basin, schematic_initiation  도식
출력: docs/figures/phase_selection/*.png
"""
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, Polygon
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/home/bong/projects/horcrux_env")
OUT = ROOT / "docs/figures/phase_selection"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "training"))
sys.path.insert(0, str(ROOT))
from eval_phase_rules import KIND_DET, Q_J, V_J, OrbitTable, choose_column, load_bank, mass_matrix_joint_block, pattern_key  # noqa: E402
from eval_expert_transitions import N_CMD, NAMES, make_env  # noqa: E402
from horcrux_env.envs.gait_v2 import GaitV2  # noqa: E402
from horcrux_env.envs.gait_provider import VALIDATED_COMMANDS  # noqa: E402

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(FONT_PATH)
FONT_NAME = fm.FontProperties(fname=FONT_PATH).get_name()
plt.rcParams.update({"font.family": FONT_NAME, "axes.unicode_minus": False, "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
NAVY, BLUE, ORANGE, GREEN, RED, GRAY, LIGHT = "#203864", "#2E75B6", "#E97132", "#196B24", "#C0392B", "#8A8A8A", "#EEF3FA"
FAMILY_ORDER = ["forward", "backward", "diag_fl", "diag_br", "left", "right", "diag_fr", "diag_bl", "ccw", "cw"]
PARAMS = {n: p for n, _, p in VALIDATED_COMMANDS}
DT, OMEGA = 0.05, 4.0          # 환경의 gait 표본 간격(초), 시간 파라미터 40 → 각속도 4 rad/s
PERIOD = 2 * np.pi / OMEGA     # 1.571초


def gait(name):
    return GaitV2(tuple(PARAMS[name]), frame_skip=10)   # 환경과 동일: 0.005 × 10 = 0.05초 간격


def save(fig, name):
    p = OUT / f"{name}.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", p)


# ---------------------------------------------------------------- F1
def fig_serpenoid_sign():
    g = gait("forward")
    t = g._t
    ref = g.serpenoid(t, g._ed1, g._el1, g._ed2, g._el2, g._delta)   # (14, N) 기준 각도(정규화 진폭)
    M = g.MotionMatrix                                                 # (14, N-2)
    n = int(2 * PERIOD / DT) + 1
    fig, axes = plt.subplots(2, 1, figsize=(8, 4.6), sharex=True)
    for ax, j, label in zip(axes, (0, 1), ("관절 1 (세로 파동)", "관절 2 (가로 파동, δ만큼 밀림)")):
        ax.plot(t[:n], ref[j, :n], color=NAVY, lw=2, label="기준 관절 각도 (사인파)")
        ax.step(t[1:n + 1], M[j, :n], where="mid", color=ORANGE, lw=1.6, label="모션 벡터 = 가속도의 부호")
        ax.plot(t[:n], -np.sign(ref[j, :n]) * 0.9, ls=":", color=GREEN, lw=1.4, label="각도 부호의 반대 (같은 선)")
        ax.axhline(0, color=GRAY, lw=0.6)
        ax.set_ylabel(label, fontsize=9.5)
        ax.set_ylim(-1.35, 1.35)
    axes[0].legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8.5, ncol=3, frameon=False)
    axes[1].set_xlabel("시간 (초)  —  한 주기는 1.57초, 표본 간격 0.05초")
    fig.suptitle("모션 벡터는 기준 각도를 두 번 미분한 값의 부호입니다. 사인파라서 각도 부호의 반대와 같습니다.", fontsize=10.5, y=1.02)
    save(fig, "F1_serpenoid_sign")


# ---------------------------------------------------------------- F2
def agreement_curve(src_pattern, M_T, ncol):
    return (M_T[:, :ncol] * src_pattern[:, None]).sum(axis=0)


def fig_delta180():
    gl, gr, gf = gait("left"), gait("right"), gait("forward")
    t = gl._t
    n = int(2 * PERIOD / DT) + 1
    rl = gl.serpenoid(t, gl._ed1, gl._el1, gl._ed2, gl._el2, gl._delta)
    rr = gr.serpenoid(t, gr._ed1, gr._el1, gr._ed2, gr._el2, gr._delta)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    ax = axes[0]
    ax.plot(t[:n], rl[0, :n], color=NAVY, lw=2, label="세로 관절 1: left(δ=45)와 right(δ=225)가 같음")
    ax.plot(t[:n], rl[1, :n], color=BLUE, lw=2, label="가로 관절 2: left (δ=45)")
    ax.plot(t[:n], rr[1, :n], color=ORANGE, lw=2, ls="--", label="가로 관절 2: right (δ=225)  → 정확히 부호 반전")
    ax.axhline(0, color=GRAY, lw=0.6)
    ax.set_xlabel("시간 (초)")
    ax.set_ylabel("기준 관절 각도")
    ax.set_title("δ에 180도를 더하면 가로 파동만 뒤집힙니다", fontsize=10.5)
    ax.set_ylim(-1.6, 1.25)
    ax.legend(fontsize=8, frameon=False, loc="lower center", ncol=1)
    ax = axes[1]
    c0 = 10
    src = gf.MotionMatrix[:, c0]
    ncol = int(2 * PERIOD / DT)
    for name, color, lab in (("left", BLUE, "forward → left (같은 집안)"), ("right", ORANGE, "forward → right (다른 집안)")):
        cur = agreement_curve(src, gait(name).MotionMatrix, ncol)
        ax.plot(np.arange(ncol), cur, color=color, lw=2, label=f"{lab}: 최대 {cur.max():.0f}")
    ax.axhline(14, color=GRAY, lw=0.8, ls=":")
    ax.text(ncol - 1, 14.3, "14 = 전부 같음", ha="right", fontsize=8.5, color=GRAY)
    ax.set_xlabel("목표 gait의 후보 위상 (열 번호, 두 주기)")
    ax.set_ylabel("부호가 같은 수 − 다른 수")
    ax.set_ylim(-15, 16)
    ax.set_title("forward의 한 패턴을 목표 gait의 모든 위상과 비교", fontsize=10.5)
    ax.legend(fontsize=8.5, frameon=False, loc="lower right")
    save(fig, "F2_delta180")


# ---------------------------------------------------------------- F3
def unique_patterns(M):
    keys, cols = {}, []
    for c in range(M.shape[1]):
        k = pattern_key(M[:, c])
        if k not in keys:
            keys[k] = 0
            cols.append(c)
        keys[k] += 1
    return keys, cols


def agreement_matrix():
    G = {n: gait(n) for n in FAMILY_ORDER}
    A = np.zeros((len(FAMILY_ORDER), len(FAMILY_ORDER)))
    for i, s in enumerate(FAMILY_ORDER):
        keys, _ = unique_patterns(G[s].MotionMatrix)
        w = np.array(list(keys.values()), dtype=float)
        pats = np.array([np.array(k, dtype=float) for k in keys])
        for j, tname in enumerate(FAMILY_ORDER):
            MT = G[tname].MotionMatrix
            best = np.array([(MT * p[:, None]).sum(axis=0).max() for p in pats])
            A[i, j] = (best * w).sum() / w.sum()
    return A


def fig_agreement_heatmap():
    A = agreement_matrix()
    fig, ax = plt.subplots(figsize=(7.2, 6))
    im = ax.imshow(A, cmap="Blues", vmin=0, vmax=14)
    ax.set_xticks(range(10), FAMILY_ORDER, rotation=45, ha="right")
    ax.set_yticks(range(10), FAMILY_ORDER)
    ax.set_xlabel("도착 gait")
    ax.set_ylabel("출발 gait")
    for i in range(10):
        for j in range(10):
            ax.text(j, i, f"{A[i, j]:.1f}", ha="center", va="center", fontsize=8.5, color="white" if A[i, j] > 8 else NAVY)
    for lo, hi, lab in ((0, 5, "집안 A (다섯 gait)"), (5, 8, "집안 B (세 gait)"), (8, 10, "회전")):
        ax.add_patch(plt.Rectangle((lo - 0.5, lo - 0.5), hi - lo, hi - lo, fill=False, ec=ORANGE, lw=2))
        ax.text((lo + hi) / 2 - 0.5, -0.8, lab, ha="center", va="bottom", fontsize=9, color=ORANGE, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8, label="위상을 맞춘 뒤 부호가 같은 수 − 다른 수 (최대 14)")
    ax.set_title("위상을 아무리 잘 맞춰도 집안을 건너면 부호 일치가 5~6에 막힙니다", fontsize=10.5, pad=28)
    save(fig, "F3_agreement_heatmap")
    json.dump({"order": FAMILY_ORDER, "matrix": A.round(2).tolist()}, open(OUT / "F3_agreement_matrix.json", "w"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- F4
def project(scene, p, W, H):
    c0, c1 = scene.camera[0], scene.camera[1]
    pos = (np.array(c0.pos) + np.array(c1.pos)) / 2
    fwd = (np.array(c0.forward) + np.array(c1.forward)) / 2
    up = (np.array(c0.up) + np.array(c1.up)) / 2
    fwd /= np.linalg.norm(fwd)
    up /= np.linalg.norm(up)
    right = np.cross(fwd, up)
    near = (c0.frustum_near + c1.frustum_near) / 2
    center, width = (c0.frustum_center + c1.frustum_center) / 2, (c0.frustum_width + c1.frustum_width) / 2
    top, bottom = (c0.frustum_top + c1.frustum_top) / 2, (c0.frustum_bottom + c1.frustum_bottom) / 2
    if width <= 0:   # 원근 카메라는 가로 폭을 뷰포트 비율로 정한다
        width = (top - bottom) * W / H
    v = np.asarray(p) - pos
    z = v @ fwd
    xn, yn = (v @ right) * near / z, (v @ up) * near / z
    u = (xn - (center - width / 2)) / width * W
    w = (top - yn) / (top - bottom) * H
    return float(u), float(w)


def fig_robot_joints(bank):
    """기존 녹화 코드와 같은 방식(gymnasium rgb_array 뷰어)으로 렌더한다 — 별도 GL 백엔드 설정 없음."""
    import gymnasium as gym
    import mujoco
    import horcrux_env  # noqa: F401
    from build_moving_state_bank import BASE_KW
    kw = dict(BASE_KW)
    kw.update(joy_input=list(VALIDATED_COMMANDS[0][1]), gait_params=list(VALIDATED_COMMANDS[0][2]))
    try:
        env = gym.make("horcrux_env/plane-moving-init-v0", render_mode="rgb_array", width=1280, height=720, **kw)
    except TypeError:
        env = gym.make("horcrux_env/plane-moving-init-v0", render_mode="rgb_array", **kw)
    env.reset(seed=0)
    base = env.unwrapped
    idx = np.flatnonzero((bank["source"] == 0) & (bank["kind"] == KIND_DET))
    i = idx[len(idx) // 3]
    base.set_state(bank["qpos"][i].copy(), bank["qvel"][i].copy())
    viewer = base.mujoco_renderer._get_viewer("rgb_array")
    cam = viewer.cam
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    com = base.get_robot_com()
    cam.lookat[:] = [com[0], com[1], 0.05]
    cam.distance, cam.azimuth, cam.elevation = 1.35, 135, -55
    frame = viewer.render(render_mode="rgb_array")
    img = Image.fromarray(np.asarray(frame))
    H, W = img.height, img.width
    renderer = type("R", (), {"scene": viewer.scn})()   # project()가 기대하는 인터페이스
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 26)
    small = ImageFont.truetype(FONT_PATH, 22)
    hinge = [j for j in range(base.model.njnt) if base.model.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE]
    axes = {j: tuple(np.round(base.model.jnt_axis[j], 2)) for j in hinge}
    print("힌지 관절", len(hinge), "축", axes)
    for n, j in enumerate(hinge, start=1):
        u, w = project(renderer.scene, base.data.xanchor[j], W, H)
        color = (46, 117, 182) if n % 2 == 1 else (233, 113, 50)
        r = 17
        draw.ellipse([u - r, w - r, u + r, w + r], fill=color, outline="white", width=2)
        draw.text((u, w), str(n), fill="white", font=small, anchor="mm")
    lx, ly = 30, 30
    draw.rectangle([lx - 12, ly - 12, lx + 620, ly + 96], fill=(255, 255, 255, 230))
    draw.ellipse([lx, ly + 6, lx + 26, ly + 32], fill=(46, 117, 182))
    draw.text((lx + 40, ly + 19), "홀수 관절 = 세로 파동 (위아래로 굽힘, 땅에 닿는 마디를 정함)", fill=(32, 56, 100), font=font, anchor="lm")
    draw.ellipse([lx, ly + 54, lx + 26, ly + 80], fill=(233, 113, 50))
    draw.text((lx + 40, ly + 67), "짝수 관절 = 가로 파동 (좌우로 굽힘, 미는 방향을 정함)", fill=(32, 56, 100), font=font, anchor="lm")
    img.save(OUT / "F4_robot_joints.png")
    print("saved", OUT / "F4_robot_joints.png")
    env.close()
    return axes


# ---------------------------------------------------------------- F5
def phase_of_col(c):
    return (OMEGA * DT * c) % (2 * np.pi)


def fig_phase_portrait(bank, table: OrbitTable, target="diag_fr", source="forward", joints=(6, 7)):
    g = NAMES.index(target)
    s = NAMES.index(source)
    env = make_env(g, 0, None, None, 0.0)
    base = env.unwrapped
    G = base._gait
    M = G.MotionMatrix
    cands = table.candidates(g, M)
    # 궤도 표를 위상 순서로 정렬
    order = sorted(cands, key=lambda kc: phase_of_col(kc[1]))
    orbit_q = np.array([table.table[g][k][0] for k, _ in order])
    orbit_v = np.array([table.table[g][k][1] for k, _ in order])
    # 목표 gait 자체의 상태 구름
    m = (bank["source"] == g) & (bank["kind"] == KIND_DET)
    cloud_q, cloud_v = bank["qpos"][m][:, Q_J], bank["qvel"][m][:, V_J]
    sub = np.random.default_rng(0).choice(len(cloud_q), size=min(2500, len(cloud_q)), replace=False)
    # 출발 상태 하나 — 부호 규칙이 고른 패턴도 궤도 표에 있는 상태를 고른다 (희귀 패턴은 표에 없을 수 있음)
    idx = np.flatnonzero((bank["source"] == s) & (bank["kind"] == KIND_DET))
    picks = {}
    for i in idx[len(idx) // 2::37]:
        qpos, qvel, m_src = bank["qpos"][i], bank["qvel"][i], bank["mvec"][i].astype(float)
        env.reset()
        base.set_state(qpos.copy(), qvel.copy())
        Mjj = mass_matrix_joint_block(base)
        q, v = qpos[Q_J], qvel[V_J]
        picks = {}
        for rule, color, lab in (("sign", ORANGE, "부호 정렬이 고른 점"), ("near", GREEN, "가장 가까운 점 (제안)")):
            col = choose_column(rule, G, cands, table, g, q, v, m_src, Mjj)
            key = pattern_key(M[:, col])
            j_var, _ = table.dist(g, key, q, v, Mjj)
            picks[rule] = (col, key, j_var, color, lab)
        if all(p[1] in table.table[g] for p in picks.values()):
            break
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9))
    for ax, j in zip(axes[:2], joints):
        ax.scatter(cloud_q[sub, j], cloud_v[sub, j], s=3, color="#C7D3E3", label=f"{target} 전문가의 상태 구름")
        ax.plot(np.r_[orbit_q[:, j], orbit_q[0, j]], np.r_[orbit_v[:, j], orbit_v[0, j]], color=NAVY, lw=2, label="패턴별 평균 = 주기 궤도")
        ax.plot(q[j], v[j], "o", color=RED, ms=9, label=f"지금 상태 ({source}로 움직이던 몸)")
        for rule, (col, key, j_var, color, lab) in picks.items():
            qm, vm, _ = table.table[g][key]
            ax.plot(qm[j], vm[j], "s", color=color, ms=9, label=f"{lab}, J={j_var:.0f}")
            ax.annotate("", xy=(qm[j], vm[j]), xytext=(q[j], v[j]), arrowprops=dict(arrowstyle="->", color=color, lw=1.6))
        ax.set_xlabel(f"관절 {j + 1} 각도 (rad)")
        ax.set_ylabel(f"관절 {j + 1} 각속도 (rad/s)")
        ax.set_title(f"관절 {j + 1} ({'세로' if j % 2 == 0 else '가로'} 파동)", fontsize=10.5)
    axes[0].legend(fontsize=7.5, frameon=False, loc="upper left")
    ax = axes[2]
    phis = np.array([phase_of_col(c) for _, c in order])
    J = np.array([table.dist(g, k, q, v, Mjj)[0] for k, _ in order])
    ax.plot(np.degrees(phis), J, color=NAVY, lw=1.8)
    for rule, (col, key, j_var, color, lab) in picks.items():
        ax.plot(np.degrees(phase_of_col(col)), j_var, "s", color=color, ms=9, label=lab)
    ax.set_xlabel("목표 gait의 후보 위상 (도)")
    ax.set_ylabel("거리 J (분산 정규화)")
    ax.set_title("후보 위상마다 잰 거리", fontsize=10.5)
    ax.legend(fontsize=8, frameon=False)
    fig.suptitle(f"{source} 로 움직이던 몸을 {target} 로 바꿀 때: 궤도 위에서 어느 점을 고르는가", fontsize=11)
    save(fig, "F5_phase_portrait")
    env.close()
    return {r: dict(col=int(p[0]), j_var=float(p[2])) for r, p in picks.items()}


# ---------------------------------------------------------------- F6 / F7 (실험 결과)
def fig_experiment(path):
    if not Path(path).exists():
        print("실험 결과 없음:", path)
        return None
    d = json.load(open(path))
    rec = d["records"]
    rules = list(d["rules"])
    sm_path = Path(path).with_name("eval_phase_rules_signmom.json")   # 하이브리드 규칙(별도 실행) 병합
    if sm_path.exists():
        sm = json.load(open(sm_path))
        for t in d["targets"]:
            d["summary"][t]["signmom"] = sm["summary"][t]["signmom"]
        rules.append("signmom")
    # F6 거리 vs 실패 (모든 규칙·목표 합침, 10분위)
    J = np.array([r["j_var"] for r in rec], dtype=float)
    F = np.array([r["fail"] for r in rec], dtype=float)
    ok = np.isfinite(J)
    J, F = J[ok], F[ok]
    edges = np.quantile(J, np.linspace(0, 1, 11))
    xs, ys, es = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (J >= lo) & (J <= hi)
        if m.sum() == 0:
            continue
        p = F[m].mean()
        xs.append(J[m].mean())
        ys.append(p)
        es.append(np.sqrt(p * (1 - p) / m.sum()))
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.errorbar(xs, ys, yerr=es, fmt="o-", color=NAVY, ecolor=BLUE, capsize=3, lw=1.8)
    ax.set_xlabel("진입 순간의 거리 J (선택한 위상에서 목표 궤도까지, 분산 정규화)")
    ax.set_ylabel("150스텝 안에 넘어진 비율")
    ax.set_ylim(0, 1)
    ax.set_title(f"거리가 멀수록 실패가 늘어나는가 (진입 {len(J):,}번, 10분위 평균)", fontsize=10.5)
    save(fig, "F6_distance_vs_failure")
    # F7 규칙별 실패
    targets = d["targets"]
    means = {r: [d["summary"][t][r]["mean"] for t in targets] for r in rules}
    fig, ax = plt.subplots(figsize=(7, 3.8))
    w = 0.8 / len(rules)
    colors = {"k0": GRAY, "sign": ORANGE, "near": GREEN, "kin": BLUE, "signmom": NAVY}
    labels = {"k0": "위상 0 재시작", "sign": "부호 정렬 (현행)", "near": "가장 가까운 점 (분산)", "kin": "운동 에너지", "signmom": "부호 정렬 + 운동량"}
    for i, r in enumerate(rules):
        xs = np.arange(len(targets)) + (i - (len(rules) - 1) / 2) * w
        ax.bar(xs, means[r], width=w, color=colors.get(r, NAVY), label=labels.get(r, r))
        for x, y in zip(xs, means[r]):
            ax.text(x, y + 0.01, f"{y:.2f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(targets)), targets)
    ax.set_ylabel("전환 뒤 실패 비율 (출발 9개 평균)")
    ax.set_ylim(0, max(0.6, max(max(v) for v in means.values()) + 0.1))
    ax.legend(fontsize=8.5, frameon=False, ncol=2)
    ax.set_title("같은 은행 상태에서 시작 위상 규칙만 바꿨을 때", fontsize=10.5)
    save(fig, "F7_rule_comparison")
    return dict(n=len(J), bins=list(zip(xs, ys)), means=means)


# ---------------------------------------------------------------- F9 위상별 결과 지도 (후보 위상 전부 시도)
def fig_phase_raster(path_all, targets=("diag_fr", "forward", "diag_bl")):
    from matplotlib.colors import ListedColormap
    if not Path(path_all).exists():
        print("전부 시도 결과 없음:", path_all)
        return None
    d = json.load(open(path_all))
    rec = d["records"]
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(1, len(targets), figsize=(4.2 * len(targets), 5.2))
    stats = {}
    for ax, t in zip(np.atleast_1d(axes), targets):
        rt = [r for r in rec if r["target"] == t]
        cols = sorted({r["col"] for r in rt}, key=phase_of_col)
        keys = sorted({(r["source"], r["state"]) for r in rt}, key=lambda k: (NAMES.index(k[0]), k[1]))
        Mx = np.full((len(keys), len(cols)), np.nan)
        ki = {k: i for i, k in enumerate(keys)}
        ci = {c: j for j, c in enumerate(cols)}
        for r in rt:
            Mx[ki[(r["source"], r["state"])], ci[r["col"]]] = float(r["fail"])
        ax.imshow(Mx, cmap=ListedColormap(["#DCE6F2", "#C0392B"]), aspect="auto", vmin=0, vmax=1, interpolation="nearest")
        # 출발 gait 경계와 이름
        srcs = [k[0] for k in keys]
        bounds = [i for i in range(1, len(srcs)) if srcs[i] != srcs[i - 1]]
        for b in bounds:
            ax.axhline(b - 0.5, color="white", lw=1.2)
        ticks, labels = [], []
        start = 0
        for b in bounds + [len(srcs)]:
            ticks.append((start + b - 1) / 2)
            labels.append(srcs[start])
            start = b
        ax.set_yticks(ticks, labels, fontsize=8)
        ax.set_xticks(range(len(cols)), [f"{np.degrees(phase_of_col(c)):.0f}" for c in cols], fontsize=7.5, rotation=90)
        ax.set_xlabel("목표 gait의 후보 위상 (도)")
        # 구조 통계: 행마다 실패 덩어리(원형 연속 구간) 수 vs 무작위 섞기
        runs, runs_sh = [], []
        for row in Mx:
            f = row.astype(int)
            if 0 < f.sum() < len(f):
                runs.append(int(np.sum((f == 1) & (np.roll(f, 1) == 0))))
                runs_sh.append(float(np.mean([np.sum((g == 1) & (np.roll(g, 1) == 0)) for g in (rng.permutation(f) for _ in range(100))])))
        surv = float(1 - np.nanmean(Mx))
        oracle = float(np.mean([np.all(row == 1) for row in Mx]))
        col_fail = np.nanmean(Mx, axis=0)
        stats[t] = dict(states=len(keys), phases=len(cols), survive_frac=surv, no_phase_works=oracle,
                        runs=float(np.mean(runs)) if runs else 0.0, runs_shuffled=float(np.mean(runs_sh)) if runs_sh else 0.0,
                        best_fixed_col_fail=float(col_fail.min()), worst_fixed_col_fail=float(col_fail.max()))
        ax.set_title(f"{t}: 살아남는 칸 {surv:.0%}, 어떤 위상도 안 되는 상태 {oracle:.0%}", fontsize=10)
    np.atleast_1d(axes)[0].set_ylabel("출발 gait별 은행 상태 (행 하나가 상태 하나)")
    fig.suptitle("상태마다 어느 위상이 살아남는가 (빨강 = 150스텝 안에 넘어짐, 연한 파랑 = 살아남음)", fontsize=11)
    save(fig, "F9_phase_raster")
    return stats


# ---------------------------------------------------------------- F8 도식
def closed_curve(n=400, r0=1.0, wob=0.12, k=3, phase=0.0):
    th = np.linspace(0, 2 * np.pi, n)
    r = r0 * (1 + wob * np.sin(k * th + phase))
    return np.c_[r * np.cos(th), r * np.sin(th)], th


def fig_schematic_basin():
    fig, ax = plt.subplots(figsize=(6.4, 5))
    outer, _ = closed_curve(r0=1.42, wob=0.12)
    inner, _ = closed_curve(r0=0.6, wob=0.12)
    ax.add_patch(Polygon(outer, closed=True, fc="#DCE6F2", ec="none"))
    ax.add_patch(Polygon(inner, closed=True, fc="white", ec="none"))
    cyc, th = closed_curve()
    ax.plot(cyc[:, 0], cyc[:, 1], color=NAVY, lw=2.5)
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        rin = 1 + 0.12 * np.sin(3 * a)
        for r_from, r_to in ((rin + 0.32, rin + 0.08), (rin - 0.3, rin - 0.07)):
            ax.annotate("", xy=(r_to * np.cos(a), r_to * np.sin(a)), xytext=(r_from * np.cos(a), r_from * np.sin(a)),
                        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.1))
    for a in np.linspace(0, 2 * np.pi, 14, endpoint=False):
        r = 1 + 0.12 * np.sin(3 * a)
        ax.plot(r * np.cos(a), r * np.sin(a), "o", color=NAVY, ms=4)
    x = np.array([1.05, 0.62])
    ax.plot(*x, "o", color=RED, ms=10, zorder=5)
    ax.text(x[0] + 0.08, x[1] + 0.05, "지금 몸 상태", color=RED, fontsize=10.5, fontweight="bold")
    d = np.linalg.norm(cyc - x, axis=1)
    near = cyc[d.argmin()]
    ax.plot(*near, "s", color=GREEN, ms=10, zorder=5)
    ax.plot([x[0], near[0]], [x[1], near[1]], color=GREEN, lw=2)
    ax.text(near[0] + 0.05, near[1] - 0.2, "가장 가까운 위상\n짧은 점프, 흡인 영역 안", color=GREEN, fontsize=9.5)
    far = cyc[(d.argmin() + 150) % len(cyc)]
    ax.plot(*far, "s", color=ORANGE, ms=10, zorder=5)
    ax.plot([x[0], far[0]], [x[1], far[1]], color=ORANGE, lw=2, ls="--")
    ax.text(far[0] - 0.05, far[1] - 0.22, "먼 위상\n긴 점프, 영역 밖으로 나갈 수 있음", color=ORANGE, fontsize=9.5, ha="right")
    ax.text(0, 1.62, "목표 gait의 주기 궤도 (진한 선)와 흡인 영역 (옅은 띠)", ha="center", fontsize=10.5, color=NAVY)
    ax.text(0, -0.05, "궤도 위의 점 하나가\n시작 위상 하나입니다", ha="center", va="center", fontsize=9.5, color=GRAY)
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-1.75, 1.8)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "F8a_schematic_basin")


def fig_schematic_initiation():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    src, _ = closed_curve(r0=0.9, wob=0.1, k=2)
    src = src + np.array([-1.7, 0])
    tgt, _ = closed_curve(r0=0.9, wob=0.1, k=3)
    tgt = tgt + np.array([1.4, 0])
    big, _ = closed_curve(r0=1.55, wob=0.18, k=4, phase=1.0)
    big = big + np.array([1.4, 0])
    small, _ = closed_curve(r0=1.15, wob=0.12, k=3, phase=0.5)
    small = small + np.array([1.4, 0])
    ax.add_patch(Polygon(big, closed=True, fc="#EEF3FA", ec=BLUE, ls="--", lw=1.4))
    ax.add_patch(Polygon(small, closed=True, fc="#DCE6F2", ec="none"))
    ax.plot(src[:, 0], src[:, 1], color=GRAY, lw=2.2)
    ax.plot(tgt[:, 0], tgt[:, 1], color=NAVY, lw=2.5)
    p = src[60]
    ax.plot(*p, "o", color=RED, ms=9, zorder=5)
    d = np.linalg.norm(tgt - p, axis=1)
    q = tgt[d.argmin()]
    ax.plot(*q, "s", color=GREEN, ms=9, zorder=5)
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="->", color=GREEN, lw=2))
    ax.text(-1.7, -1.35, "출발 gait의 궤도\n(이 위를 돌던 몸)", ha="center", fontsize=9.5, color=GRAY)
    ax.text(1.4, -1.35, "목표 gait의 궤도", ha="center", fontsize=9.5, color=NAVY)
    ax.text(p[0] - 0.12, p[1] + 0.12, "전환 순간의 몸 상태", ha="right", fontsize=9.5, color=RED)
    ax.text(0.15, 0.55, "규칙이 고른 시작 위상", fontsize=9.5, color=GREEN)
    ax.text(1.4, 1.02, "시작 집합 (지금)", ha="center", fontsize=9.5, color=NAVY)
    ax.text(1.4, 1.72, "인계 시작 학습으로 넓어지는 시작 집합", ha="center", fontsize=9.5, color=BLUE)
    ax.set_xlim(-3.0, 3.4)
    ax.set_ylim(-1.75, 2.05)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "F8b_schematic_initiation")


if __name__ == "__main__":
    which = sys.argv[1:] or ["all"]
    bank = load_bank(str(ROOT / "runs/moving_state_bank/bank_iter1.npz"))
    table = OrbitTable(bank)
    info = {}
    if "all" in which or "f1" in which:
        fig_serpenoid_sign()
    if "all" in which or "f2" in which:
        fig_delta180()
    if "all" in which or "f3" in which:
        fig_agreement_heatmap()
    if "all" in which or "f4" in which:
        info["axes"] = {str(k): v for k, v in fig_robot_joints(bank).items()}
    if "all" in which or "f5" in which:
        info["picks"] = fig_phase_portrait(bank, table)
    if "all" in which or "f8" in which:
        fig_schematic_basin()
        fig_schematic_initiation()
    if "all" in which or "f6" in which:
        info["exp"] = fig_experiment(ROOT / "runs/moving_state_bank/eval_phase_rules.json")
    if "all" in which or "f9" in which:
        info["raster"] = fig_phase_raster(ROOT / "runs/moving_state_bank/eval_phase_rules_all.json")
    json.dump(info, open(OUT / "figure_info.json", "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(info, ensure_ascii=False, default=str)[:1500])
