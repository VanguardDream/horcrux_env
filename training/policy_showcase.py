"""통합 정책 성능 시각화 영상 (명령 투어 · 전환 클로즈업 · 경로 추종 오버레이).

정책 하나가 10개 명령을 수행하고 그 사이를 전환하는 모습을 렌더링한다. 전환 규약은
학습(전환 커리큘럼)과 동일: env.set_command(align_phase=True) 뒤 current_observation()으로
관측을 즉시 재생성. 오버레이(명령·목표 방향·전환 경과·행동 진폭 바)는 프레임 후처리(PIL)라
환경 코드를 건드리지 않는다. 마커(궤적·전환 지점·로봇 yaw 화살표)는 path_following의
렌더 관례를 재사용한다.

산출물 (runs/policy_showcase/<태그>/):
  - command_tour.mp4          10개 명령 순차 전환 (세그먼트 6 s)
  - closeup_<from>_<to>.mp4   위험 전환 슬로모션(1/2 배속) + 진폭 바
  - path_<kind>.mp4 / _trajectory.png / result.txt   경로 추종 (오버레이 포함)
  - summary.txt

사용:
  python training/policy_showcase.py --model runs/.../final_model.zip --vecnorm runs/.../vecnormalize.pkl --tag S3final
"""
from __future__ import annotations

import argparse
import glob
import time
from pathlib import Path

import gymnasium as gym
import imageio
import mujoco
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

import horcrux_env  # noqa: F401
from horcrux_env.envs.gait_provider import VALIDATED_COMMANDS
from path_following import (UnifiedPolicy, WaypointCommander, cross_track_errors, heading_matrix,
                            make_path, add_scene_markers)

ROOT = Path(__file__).resolve().parents[1]
NAMES = [c[0] for c in VALIDATED_COMMANDS]
NAME2ID = {n: i for i, n in enumerate(NAMES)}
KOR = {"forward": "전진", "left": "좌측", "right": "우측", "diag_fl": "전진-좌 대각", "diag_fr": "전진-우 대각",
       "backward": "후진", "diag_bl": "후진-좌 대각", "diag_br": "후진-우 대각", "ccw": "반시계 회전", "cw": "시계 회전"}
TOUR = ["forward", "diag_fr", "right", "diag_br", "backward", "diag_bl", "left", "diag_fl", "ccw", "cw"]
CLOSEUPS = [("forward", "diag_fr"), ("left", "diag_fr"), ("backward", "diag_bl"), ("diag_br", "diag_bl"), ("forward", "ccw")]
DT = 0.05


def _font(size: int, bold: bool = False):
    cands = glob.glob(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{'Bold' if bold else 'Regular'}.ttc") + \
        glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True) + glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
    for c in cands:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


F_BIG, F_MID, F_SMALL = _font(30, True), _font(22), _font(17)


def env_kwargs_from_config(path: Path) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    kw = dict(cfg["environment"].get("kwargs", {}))
    kw.update(switch_enabled=False, random_init_phase=False, terminate_when_unhealthy=False)
    return kw


def overlay(frame: np.ndarray, cmd: int, yaw_deg: float, t_since: float, n_switch: int, action: np.ndarray,
            title: str, fallen: bool, flash: bool = False, extra: str | None = None) -> np.ndarray:
    """프레임 위에 상태 패널을 그린다 (좌상단: 명령·방향, 좌하단: 행동 진폭 바)."""
    img = Image.fromarray(frame).convert("RGBA")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    W, H = img.size
    # 상단 패널
    d.rounded_rectangle([14, 14, 470, 150], radius=12, fill=(10, 20, 40, 175))
    d.text((28, 20), title, font=F_SMALL, fill=(180, 200, 230, 255))
    name = NAMES[cmd]
    d.text((28, 46), f"{KOR[name]}  ({name})", font=F_BIG, fill=(255, 255, 255, 255))
    d.text((28, 92), f"전환 후 {t_since:4.1f} s   ·   전환 {n_switch}회", font=F_MID, fill=(220, 230, 245, 255))
    if extra:
        d.text((28, 120), extra, font=F_SMALL, fill=(200, 215, 235, 255))
    # 목표 방향 나침반 (세계 좌표: 카메라가 천장 고정 방향이라 화면 = 세계 xy)
    cx, cy, r = 415, 82, 38
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 215, 235, 220), width=2)
    joy = np.asarray(VALIDATED_COMMANDS[cmd][1], dtype=float)
    if abs(joy[2]) > 0.5:
        d.text((cx - 16, cy - 16), "↻" if joy[2] < 0 else "↺", font=F_BIG, fill=(120, 255, 190, 255))
    else:
        th = np.radians(yaw_deg)
        wx, wy = np.cos(th) * joy[0] - np.sin(th) * joy[1], np.sin(th) * joy[0] + np.cos(th) * joy[1]
        # 화면 y는 아래가 +이므로 세계 +y는 위쪽 (천장 카메라 기본 방향과 정합)
        ex, ey = cx + wx * (r - 6), cy - wy * (r - 6)
        d.line([cx, cy, ex, ey], fill=(120, 255, 190, 255), width=4)
        ang = np.arctan2(-(ey - cy), ex - cx)
        for s_ in (+2.6, -2.6):
            d.line([ex, ey, ex - 12 * np.cos(ang + s_), ey + 12 * np.sin(ang + s_)], fill=(120, 255, 190, 255), width=4)
        d.text((cx + r + 6, cy - 12), "목표", font=F_SMALL, fill=(180, 200, 230, 255))
    # 행동 진폭 바 (14관절, 0~2.7)
    bx, by, bw, bh = 14, H - 96, 300, 82
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(10, 20, 40, 165))
    d.text((bx + 10, by + 4), "행동 진폭 (14관절, 0~2.7)", font=F_SMALL, fill=(180, 200, 230, 255))
    a = np.clip(np.asarray(action, dtype=float), 0, 2.7) / 2.7
    for i, v in enumerate(a):
        x0 = bx + 12 + i * 20
        d.rectangle([x0, by + bh - 8 - v * 46, x0 + 14, by + bh - 8], fill=(110, 190, 255, 230))
    if fallen:
        d.rounded_rectangle([W - 190, 14, W - 14, 60], radius=10, fill=(200, 40, 50, 200))
        d.text((W - 170, 22), "불건강(낙상)", font=F_MID, fill=(255, 255, 255, 255))
    if flash:
        d.rounded_rectangle([W // 2 - 110, 20, W // 2 + 110, 70], radius=12, fill=(255, 190, 40, 220))
        d.text((W // 2 - 62, 28), "명령 전환", font=F_MID, fill=(20, 20, 20, 255))
    return np.asarray(Image.alpha_composite(img, ov).convert("RGB"))


class Renderer:
    """env 생성 + 카메라 추적 + 마커(궤적·전환 지점·yaw 화살표) 공통."""

    def __init__(self, env_kwargs: dict, policy: UnifiedPolicy):
        self.env = gym.make("horcrux_env/plane-unified-v0", render_mode="rgb_array", **env_kwargs)
        self.u = self.env.unwrapped
        self.pol = policy
        self.cam = self.u.model.camera("ceiling").id
        self.u.model.cam_fovy[self.cam] = 80.0
        self.cam_z = float(self.u.model.cam_pos[self.cam][2])
        self.viewer = self.u.mujoco_renderer._get_viewer("rgb_array")

    def reset(self, seed: int, first_cmd: int):
        obs, _ = self.env.reset(seed=seed)
        self.u.set_command(VALIDATED_COMMANDS[first_cmd][1], align_phase=False)
        self.raw = self.u.current_observation()
        self.cmd = first_cmd
        self.com = np.asarray(self.u.get_robot_com()[:2], dtype=float)
        self.yaw = 0.0
        self.trail, self.switch_pts = [], []
        self.t_switch = 0
        self.n_switch = 0
        self.step_i = 0
        self.seg_fn = None
        return self.raw

    def switch(self, cmd: int):
        self.u.set_command(VALIDATED_COMMANDS[cmd][1], align_phase=True)
        self.raw = self.u.current_observation()
        self.cmd = cmd
        self.t_switch = self.step_i
        self.n_switch += 1
        self.switch_pts.append(self.com.copy())

    def step(self, action=None):
        a = self.pol.act(self.cmd, self.raw) if action is None else action
        self.u.model.cam_pos[self.cam][0], self.u.model.cam_pos[self.cam][1] = self.com
        self.u.model.cam_pos[self.cam][2] = self.cam_z
        self.raw, r, te, tr, info = self.env.step(np.asarray(a, dtype=np.float32))
        self.com = np.asarray(info["com_pos"][:2], dtype=float)
        self.yaw = float(info["com_ypr"][0])
        if self.step_i % 4 == 0:
            # 궤적 세그먼트 id: 기본은 전환 횟수, 경로 추종에서는 현재 웨이포인트 인덱스
            self.trail.append((self.com.copy(), self.seg_fn() if self.seg_fn else self.n_switch))
        self.step_i += 1
        return a, r, info

    def render(self, waypoints=None, headings=None, wp_index=0):
        if waypoints is not None:
            add_scene_markers(self.viewer, waypoints, headings, wp_index, self.trail, wp_index, com=self.com, yaw_deg=self.yaw)
        else:
            trail = self.trail[-550:]
            for xy, seg in trail:
                rgba = [1.0, 0.12, 0.10, 0.80] if seg == self.n_switch else [1.0, 0.18, 0.15, 0.25]
                self.viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_SPHERE, size=[0.028] * 3, pos=[float(xy[0]), float(xy[1]), 0.03], rgba=rgba, label="")
            for p in self.switch_pts:
                self.viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.06, 0.06, 0.02], pos=[float(p[0]), float(p[1]), 0.05], rgba=[1.0, 0.85, 0.2, 0.9], label="")
            self.viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_ARROW, size=[0.045, 0.045, 0.45],
                                   pos=[float(self.com[0]), float(self.com[1]), 0.22], mat=heading_matrix(self.yaw), rgba=[0.25, 0.55, 1.0, 0.9], label="")
        return self.env.render()

    @property
    def fallen(self) -> bool:
        return bool(self.u.is_terminated)

    def close(self):
        self.env.close()


def command_tour(R: Renderer, out: Path, seg_steps: int, title: str) -> str:
    frames, notes = [], []
    R.reset(seed=7, first_cmd=NAME2ID[TOUR[0]])
    fall_flags = []
    for si, name in enumerate(TOUR):
        if si > 0:
            R.switch(NAME2ID[name])
        seg_fall = 0
        for k in range(seg_steps):
            a, r, info = R.step()
            seg_fall += int(R.fallen)
            if R.step_i % 3 == 0:
                fr = R.render()
                frames.append(overlay(fr, R.cmd, R.yaw, (R.step_i - R.t_switch) * DT, R.n_switch, a, title, R.fallen,
                                      flash=(R.step_i - R.t_switch) < 12 and si > 0, extra=f"세그먼트 {si+1}/{len(TOUR)}"))
        fall_flags.append(seg_fall)
        notes.append(f"{si+1:2d}. {name:9s} 불건강 스텝 {seg_fall:3d}/{seg_steps}")
    imageio.mimsave(out / "command_tour.mp4", frames, fps=20)
    return "\n".join(notes)


def closeup(R: Renderer, out: Path, src: str, dst: str, pre: int, post: int, title: str) -> str:
    frames = []
    R.reset(seed=11, first_cmd=NAME2ID[src])
    for k in range(pre):
        a, r, info = R.step()
        if k >= pre - 60:  # 전환 3 s 전부터 기록
            frames.append(overlay(R.render(), R.cmd, R.yaw, 0.0, 0, a, title, R.fallen, extra="전환 전"))
    R.switch(NAME2ID[dst])
    fall = 0
    for k in range(post):
        a, r, info = R.step()
        fall += int(R.fallen)
        frames.append(overlay(R.render(), R.cmd, R.yaw, (k + 1) * DT, 1, a, title, R.fallen, flash=k < 12, extra="전환 후 (1/2 배속)"))
    imageio.mimsave(out / f"closeup_{src}_to_{dst}.mp4", frames, fps=10)  # 매 스텝 기록 + 10 fps = 1/2 배속
    return f"{src}→{dst}: 전환 후 {post}스텝 중 불건강 {fall}"


def path_demo(R: Renderer, out: Path, kind: str, scale: float, max_steps: int, title: str) -> str:
    R.reset(seed=42, first_cmd=0)
    start = R.com.copy()
    commander = WaypointCommander(make_path(kind, scale, start))
    R.seg_fn = lambda: commander.wp_index
    traj, frames, next_control, active = [], [], 0, 0
    while R.step_i < max_steps:
        if R.step_i >= next_control:
            next_control = R.step_i + commander.control_period
            cmd = commander.command(R.com, R.yaw, active)
            if cmd is None:
                break
            if cmd != active:
                R.switch(cmd)
                active = cmd
        a, r, info = R.step()
        traj.append(R.com.copy())
        if R.step_i % 3 == 0:
            fr = R.render(commander.waypoints, commander.headings, commander.wp_index)
            frames.append(overlay(fr, R.cmd, R.yaw, (R.step_i - R.t_switch) * DT, R.n_switch, a, title, R.fallen,
                                  flash=(R.step_i - R.t_switch) < 12 and R.n_switch > 0,
                                  extra=f"웨이포인트 {min(commander.wp_index + 1, len(commander.waypoints))}/{len(commander.waypoints)}"))
    imageio.mimsave(out / f"path_{kind}.mp4", frames, fps=20)
    traj = np.asarray(traj)
    errs = cross_track_errors(traj, commander.waypoints, start)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nodes = np.vstack([start[None, :], commander.waypoints])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(nodes[:, 0], nodes[:, 1], "k--o", lw=1.5, ms=6, label="planned path")
    ax.scatter(traj[:, 0], traj[:, 1], c=np.arange(len(traj)), cmap="viridis", s=3, label="COM trajectory (time)")
    for p in R.switch_pts:
        ax.scatter(*p, marker="D", c="orange", s=30, zorder=5)
    ax.scatter(*start, marker="s", c="g", s=80, zorder=5, label="start")
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_title(f"{kind} | completed={commander.done} | CTE {errs.mean():.3f} m | switches {R.n_switch} | {len(traj)*DT:.1f} s")
    fig.savefig(out / f"path_{kind}_trajectory.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    line = f"{kind:9s} 완주={commander.done} CTE 평균 {errs.mean():.3f} m / 최대 {errs.max():.3f} m | 전환 {R.n_switch}회 | {len(traj)} 스텝 ({len(traj)*DT:.1f} s)"
    (out / f"path_{kind}_result.txt").write_text(line + "\n", encoding="utf-8")
    return line


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--vecnorm", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=ROOT / "training/configs/ppo_unified_transition_stage3.yaml")
    ap.add_argument("--tag", default="policy")
    ap.add_argument("--seg-steps", type=int, default=120)
    ap.add_argument("--skip-paths", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "runs" / "policy_showcase")
    a = ap.parse_args()
    out = a.out / (time.strftime("%Y%m%d-%H%M%S") + f"_{a.tag}")
    out.mkdir(parents=True, exist_ok=True)
    title = f"통합 정책 · {a.tag}"
    R = Renderer(env_kwargs_from_config(a.config), UnifiedPolicy(a.model, a.vecnorm))
    lines = [f"정책: {a.model}", f"정규화: {a.vecnorm}", ""]
    print("[1/3] 명령 투어", flush=True)
    lines += ["[명령 투어] 세그먼트당 %d스텝 (%.0f s)" % (a.seg_steps, a.seg_steps * DT), command_tour(R, out, a.seg_steps, title), ""]
    print("[2/3] 전환 클로즈업", flush=True)
    lines.append("[전환 클로즈업] 전환 후 150스텝, 1/2 배속")
    for src, dst in CLOSEUPS:
        lines.append("  " + closeup(R, out, src, dst, pre=200, post=150, title=title))
    if not a.skip_paths:
        print("[3/3] 경로 추종", flush=True)
        lines.append("")
        lines.append("[경로 추종]")
        for kind, scale, ms in (("square", 2.0, 6000), ("star", 1.5, 8000), ("gauntlet", 1.4, 10000)):
            lines.append("  " + path_demo(R, out, kind, scale, ms, title))
    R.close()
    (out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("산출물:", out)


if __name__ == "__main__":
    main()
