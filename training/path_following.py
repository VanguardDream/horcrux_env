"""전문가 스위칭 + pure-pursuit식 웨이포인트 추종 데모.

학습된 10명의 방위 전문가(8방위 + 회전 2종)를 상위 추종기가 스위칭하며
사전 계획 경로(직선/사각형/별)를 주행한다. 통합 환경의 set_command()가
명령 전환 시 gait를 위상 보존으로 동기 교체한다.

산출물 (runs/path_follow_demo/<태그>/):
  - trajectory.png  계획 경로 vs 실제 COM 궤적 (명령 구간 색상)
  - path_demo.mp4   ceiling 카메라 녹화
  - result.txt      실험 요약(경로·설정·전환방식) + cross-track 오차/완주/전환 통계

사용:
  python training/path_following.py --path square --scale 2.0
  python training/path_following.py --path star --scale 1.5
  # 통합 정책(증류+전환 학습 계보) 단독 주행 — 전환은 정책이 처리
  python training/path_following.py --path gauntlet --scale 1.4 --policy unified \
      --model runs/.../final_model.zip --vecnorm runs/.../vecnormalize.pkl
"""
from __future__ import annotations

import argparse
import pickle
import time
from pathlib import Path

import gymnasium as gym
import imageio
import mujoco
import numpy as np

import horcrux_env  # noqa: F401
from horcrux_env.envs.gait_provider import VALIDATED_COMMANDS
from stable_baselines3 import PPO

ROOT = Path(__file__).resolve().parents[1]

# 명령 이름 -> 대표 전문가 (evaluation/best 조합)
EXPERT_PATHS = {
    "forward":  "policies/path_tracking/forward/03_forward_delta0_continue_stage3",
    "left":     "policies/path_tracking/left/03_left_continue_stage3",
    "right":    "policies/path_tracking/right/03_right_continue_stage3",
    "backward": "policies/path_tracking/backward/03_gaitrev_delta0_stage3",
    "diag_fl":  "policies/path_tracking/diag_forward_left/03_diag_fl_continue_stage3",
    "diag_fr":  "policies/path_tracking/diag_forward_right/03_diag_fr_continue_stage3",
    "diag_bl":  "policies/path_tracking/diag_backward_left/03_diag_bl_continue_stage3",
    "diag_br":  "policies/path_tracking/diag_backward_right/03_diag_br_continue_stage3",
    "ccw":      "policies/rotation/ccw/05_ccw_v2_stage5",
    "cw":       "policies/rotation/cw/05_cw_v2_stage5",
}
LINEAR_COMMANDS = [i for i, c in enumerate(VALIDATED_COMMANDS) if c[1][2] == 0.0]
_NAME2ID = {c[0]: i for i, c in enumerate(VALIDATED_COMMANDS)}
# 명령 전환 (2026-09-08 최종):
#   - 기본: 즉시 k=0 전환 — 전문가가 k=0 학습이라 안전 쌍엔 이게 최적
#     (전체 사각형 A/B: k=0 0.193 vs 위상정렬 0.448).
#   - 위험 3쌍(역재생 후진대각 -> 순재생 계열)만 위상 정렬 전환: 새 gait를
#     현재 motion vector와 부호 유사도 최대 위상에서 시작해 부호 충돌 붕괴를
#     차단(152/61/156도 -> 1.0/0.5/3.1도). 소프트 페이드보다 우수 —
#     시간 지연·감속 표류가 전혀 없다.
ALIGN_PAIRS = {
    (_NAME2ID["diag_bl"], _NAME2ID["right"]),
    (_NAME2ID["diag_bl"], _NAME2ID["diag_fr"]),
    (_NAME2ID["diag_br"], _NAME2ID["diag_fl"]),
}
# 위험 쌍 전환의 매끄러움용 행동 크로스페이드 길이(스텝). 2026-09-08 계측:
# align+xfade가 위험쌍 acc_spike 142->89, jerk_head 120->98로 개선(안정성 동일).
XFADE_STEPS = 12


class UnifiedPolicy:
    """단일 명령 조건부 통합 정책 (증류 + 전환 학습 계보) + 통합 정규화 통계.

    act()의 command_id는 무시한다 — 명령은 관측(joy, motion vector)에 들어 있다.
    전환은 학습과 동일하게 env.set_command(align_phase=True) 뒤 관측을 즉시
    재생성해 정책이 새 gait/명령을 바로 보게 한다 (크로스페이드 없음).
    """

    def __init__(self, model_path: Path, vecnorm_path: Path) -> None:
        self._model = PPO.load(str(model_path), device="cpu")
        with open(vecnorm_path, "rb") as f:
            vn = pickle.load(f)
        self._mean = vn.obs_rms.mean.copy()
        self._std = np.sqrt(vn.obs_rms.var + vn.epsilon)
        self._clip = float(vn.clip_obs)

    def act(self, command_id: int, raw_obs: np.ndarray) -> np.ndarray:
        obs = np.clip((raw_obs - self._mean) / self._std, -self._clip, self._clip).astype(np.float32)
        a, _ = self._model.predict(obs, deterministic=True)
        return np.clip((a + 1.0) * 1.35, 0.0, 2.7)


class ExpertBank:
    """전문가 정책 + 각자의 관측 정규화 통계.

    overrides: {명령이름: (model.zip 경로, vecnormalize.pkl 경로)} — 특정 전문가를
    새 체크포인트로 교체 (예: 인계 시작 이어 학습 결과 비교). 반드시 쌍으로.
    """

    def __init__(self, overrides: dict | None = None) -> None:
        self._models = {}
        self._norms = {}
        overrides = overrides or {}
        for idx, (name, _joy, _gp) in enumerate(VALIDATED_COMMANDS):
            if name in overrides:
                model_path, vn_path = overrides[name]
            else:
                base = ROOT / EXPERT_PATHS[name] / "evaluation"
                model_path, vn_path = base / "best_model.zip", base / "best_model_vecnormalize.pkl"
            self._models[idx] = PPO.load(str(model_path), device="cpu")
            with open(vn_path, "rb") as f:
                vn = pickle.load(f)
            self._norms[idx] = (
                vn.obs_rms.mean.copy(), np.sqrt(vn.obs_rms.var + vn.epsilon),
                float(vn.clip_obs),
            )

    def act(self, command_id: int, raw_obs: np.ndarray) -> np.ndarray:
        mean, std, clip = self._norms[command_id]
        obs = np.clip((raw_obs - mean) / std, -clip, clip).astype(np.float32)
        a, _ = self._models[command_id].predict(obs, deterministic=True)
        # NormalizeAction 역변환: [-1,1] -> [0, 2.7]
        return np.clip((a + 1.0) * 1.35, 0.0, 2.7)


def heading_matrix(yaw_deg: float) -> np.ndarray:
    """xy 평면 방위(yaw)를 가리키는 마커용 회전행렬(3x3 평탄화).

    MuJoCo 화살표 geom은 pos에서 시작해 로컬 +z 축으로 뻗으므로, z축을
    방위 벡터로, y축을 세계 +Z로 두고 x = y x z 로 오른손 좌표계를 만든다.
    (2026-09-09 렌더 실증: 0/90/180도 -> +X/+Y/-X 정확.)
    """
    th = np.radians(yaw_deg)
    z = np.array([np.cos(th), np.sin(th), 0.0])
    y = np.array([0.0, 0.0, 1.0])
    return np.column_stack([np.cross(y, z), y, z]).flatten()


def with_tangent_headings(pts: np.ndarray, start: np.ndarray) -> np.ndarray:
    """(N,2) 웨이포인트에 목표 방위 열을 붙여 (N,3) [x, y, yaw_deg]로 만든다.

    기본 방위 = 접선: 각 웨이포인트에서 다음 웨이포인트를 향하는 방향.
    마지막 점은 직전 세그먼트 방향(도착 방향), 단일 점은 start->점 방향.
    """
    nodes = np.vstack([start[None, :], pts])
    seg = np.diff(nodes, axis=0)                      # i번째 = 노드 i -> i+1
    depart = np.vstack([seg[1:], seg[-1:]])           # 점 i에서 출발 방향, 마지막은 도착 방향
    yaw = np.degrees(np.arctan2(depart[:, 1], depart[:, 0]))
    return np.column_stack([pts, yaw])


PATH_KINDS = ("line", "square", "star", "gauntlet", "zigzag", "scurve", "octagon", "serpentine", "uturn", "random")


def make_path(kind: str, scale: float, start: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
    """계획 경로 (N,3): [x, y, yaw_deg]. yaw는 웨이포인트 목표 방위(접선 기본).

    2026-09-14 추가 (다양한 웨이포인트 검증용, 구간 길이는 판정·동결 반경보다 넉넉하게 ≥ 1.2 m):
      zigzag    좌우로 62도씩 꺾이는 지그재그 4구간 — 대각 명령 반복 전환
      scurve    완만한 S자 8점 — 작은 방향 오차가 쌓이는 양자화 드리프트
      octagon   45도씩 도는 팔각형 — 여덟 방향 명령을 차례로 모두 사용
      serpentine 90도로 좌우 번갈아 꺾는 굽이길 5구간 — 같은 집안 안의 직각 전환 반복
      uturn     168도로 거의 되돌아오는 4구간 — 전진↔후진(역재생) 전환
      random    시드로 정한 무작위 6점 (방향 변화 ±120도, 길이 1.0~1.5 scale) — 예상 밖의 전환 조합
    """
    if kind == "line":
        pts = [(scale, 0.0)]
    elif kind == "zigzag":
        s = scale
        pts = [(0.9 * s, 0.55 * s), (1.8 * s, 0.0), (2.7 * s, 0.55 * s), (3.6 * s, 0.0)]
    elif kind == "scurve":
        s = scale
        pts = [(0.6 * s * (k + 1), 0.5 * s * np.sin((k + 1) * np.pi / 4)) for k in range(8)]
    elif kind == "octagon":
        s = scale
        pts, acc = [], np.zeros(2)
        for k in range(8):
            th = np.radians(45.0 * k)
            acc = acc + s * np.array([np.cos(th), np.sin(th)])
            pts.append(tuple(acc))
    elif kind == "serpentine":
        s = scale
        pts = [(s, 0.0), (s, 0.7 * s), (0.0, 0.7 * s), (0.0, 1.4 * s), (s, 1.4 * s)]
    elif kind == "uturn":
        s = scale
        pts = [(1.2 * s, 0.0), (0.0, 0.25 * s), (1.2 * s, 0.5 * s), (0.0, 0.75 * s)]
    elif kind == "random":
        r = rng if rng is not None else np.random.default_rng(0)
        pts, acc, th = [], np.zeros(2), 0.0
        for _ in range(6):
            th += np.radians(r.uniform(-120.0, 120.0))
            acc = acc + r.uniform(1.0, 1.5) * scale * np.array([np.cos(th), np.sin(th)])
            pts.append(tuple(acc))
    elif kind == "square":
        s = scale
        pts = [(s, 0.0), (s, s), (0.0, s), (0.0, 0.0)]
    elif kind == "gauntlet":
        # 페이드 3쌍을 모두 강제 발동시키는 검증 경로:
        # ↖(diag_bl) -> ↓(right) -> ↙(diag_br) -> ↗(diag_fl) -> ↖(diag_bl) -> ↘(diag_fr)
        u_ = scale
        offs = [(-u_, u_), (0.0, -1.4 * u_), (-u_, -u_), (u_, u_), (-u_, u_), (u_, -u_)]
        pts, acc = [], np.zeros(2)
        for o in offs:
            acc = acc + np.asarray(o)
            pts.append(tuple(acc))
    elif kind == "star":
        # 5각 별 한붓그리기: 외접원 위 꼭짓점 0-2-4-1-3-0
        r = scale
        verts = [(r * np.cos(np.pi / 2 + k * 2 * np.pi / 5),
                  r * np.sin(np.pi / 2 + k * 2 * np.pi / 5)) for k in range(5)]
        order = [0, 2, 4, 1, 3, 0]
        pts = [verts[k] for k in order[1:]]
    else:
        raise ValueError(kind)
    return with_tangent_headings(start[None, :] + np.asarray(pts, dtype=np.float64), start)


class WaypointCommander:
    """웨이포인트 순차 추종 + 8-명령 양자화 (제어 주기 control_period 스텝, 기본 5 = 0.25초; 수직면 도착 판정 기본 켬)."""

    def __init__(self, waypoints: np.ndarray, capture_radius: float = 0.35,
                 control_period: int = 5, close_freeze_radius: float = 0.45,
                 plane_capture: bool = True, start: np.ndarray | None = None,
                 hysteresis_deg: float = 34.0, lookahead: float = 0.0, lookahead_deadband: float = 0.0) -> None:
        # 앞보기 불감대(lookahead_deadband, 2026-09-14): 양수면 옆 오차가 이 값 이상일 때만 앞보기 점을 겨냥하고
        # (되돌림 모드), 옆 오차가 절반 아래로 줄면 다시 웨이포인트를 겨냥한다. 앞보기만 쓰면 옆 오차는
        # ≈0.2×lookahead 로 묶이지만 전환이 늘어 시간이 길어지므로(0.5 m: 오차 −22%, 시간 +20%), 선 근처에서는
        # 전환을 아끼고 벗어났을 때만 되돌리는 절충안. 0이면 앞보기 점을 항상 겨냥(lookahead>0일 때).
        self.lookahead_deadband = float(lookahead_deadband)
        self._pullback = False
        # 앞보기 점(lookahead, 2026-09-14 자율 캠페인): 0이면 예전처럼 웨이포인트 자체를 겨냥한다.
        # 양수면 이전 노드→웨이포인트 선분 위, 로봇의 수선 발에서 lookahead m 앞의 점(선분 끝을 넘지 않음)을 겨냥한다.
        # 근거: 검증 90번의 최대 오차 22개(0.6 m 초과) 중 20개가 마지막 코너 뒤 3초 이후 구간 중간에서 났다.
        # 웨이포인트를 겨냥하면 34도 히스테리시스가 남은 거리에 비례한 옆 오차를 허용하므로 겨냥점을 선분 위
        # 가까운 점으로 바꾼다. 검토(2026-09-15) 결과 실제 옆 오차는 이 기하 허용치보다 2~3배 크고(로봇이 명령 방향에서
        # 34도 넘게 벗어나 움직인 시간이 15%), 앞보기 0.5 m의 실제 최대 오차 평균은 0.41 m다. 효과(90쌍, S3+lat):
        # 0.35/0.5/0.65/0.8 m → 오차 −31/−22/−15/−11%, 시간 +29/+20/+12/+8% (맞바꿈). 기본값 0은 사용자 결정 대기.
        self.lookahead = float(lookahead)
        # 근접 동결 반지름 기본값 0.85 → 0.45 m (2026-09-14 자율 캠페인, 사전 승인된 채택 규칙 충족):
        # S3+lat, 경로 9 × 시드 10 짝지음에서 평균 오차 50/20/20 이김 (Δ −0.024 m, p<0.001), 9경로 중 7개 개선·
        # 악화 없음, 시간 손실 없음(30/38). 0.35는 0.45와 동률, 히스테리시스 축소(25·30도)는 전환이 늘어 시간이 나빠짐.
        # 히스테리시스 각도(기본 34도)를 인자로 — 커맨더 매개변수 탐색용 (2026-09-14). 기본값은 예전과 같다.
        self.hysteresis_cos = float(np.cos(np.radians(hysteresis_deg)))
        # 기본값 변경 (2026-09-14, 사용자 결정): 갱신 주기 25 → 5스텝(0.25초), 수직면 도착 판정 켬.
        # 근거: 주기 25/10/5/2/1 × 원/수직면, 경로 3 × 시드 10 짝지은 비교에서 5스텝+수직면이
        # 평균 오차 0.29~0.32 → 0.16~0.21 m, 최대 오차 1.0~1.3 → 0.5~0.8 m (30쌍 중 27쌍 개선),
        # 더 짧은 주기는 평균 오차·시간 이득 없이 전환만 늘었다. 예전 동작은 control_period=25, plane_capture=False.
        waypoints = np.asarray(waypoints, dtype=np.float64)
        self.waypoints = waypoints[:, :2]
        # 수직면 도착 판정 (2026-09-13): 이전 노드→웨이포인트 구간 방향으로 웨이포인트의 수직면을 지나면
        # 옆 오차와 무관하게 도착으로 친다. 판정 원(반지름 capture_radius)을 옆으로 벗어나 놓친 뒤
        # 근접 동결 구간에서 지나쳐 가는 일을 없애기 위한 것. 기본 꺼짐(예전 동작 유지).
        self.plane_capture = bool(plane_capture)
        self.start = None if start is None else np.asarray(start, dtype=np.float64)[:2]
        # 목표 방위(도). 현재(1단계)는 렌더 표시용 — 크랩워크 추종은 몸통 yaw를
        # 제어하지 않는다. 2단계에서 회전 전문가(cw/ccw) 추종 대상이 된다.
        self.headings = waypoints[:, 2] if waypoints.shape[1] > 2 else np.zeros(len(waypoints))
        self.capture_radius = capture_radius
        # 근접 동결: 웨이포인트에 이 거리 이내로 접근하면 방향 교정을 멈춘다.
        # 코너 직전엔 작은 횡오차도 큰 방향각으로 증폭돼 명령이 채터링하는데,
        # 어차피 capture가 곧 다음 세그먼트로 넘긴다. (전환 메커니즘과 무관한
        # 커맨더 안정화 — 위상 정렬 전환에서도 필요.)
        self.close_freeze_radius = close_freeze_radius
        self.control_period = control_period
        self.wp_index = 0
        self._joys = np.array([VALIDATED_COMMANDS[i][1][:2] for i in LINEAR_COMMANDS])

    @property
    def done(self) -> bool:
        return self.wp_index >= len(self.waypoints)

    HYSTERESIS_COS = np.cos(np.radians(34.0))  # 양자화 반섹터(22.5도)+여유만 유지 (채터링 방지, 교정은 허용)

    def command(self, com_xy: np.ndarray, yaw_deg: float, active: int | None = None) -> int | None:
        """다음 명령 인덱스, 완주면 None.

        각도 히스테리시스: 현재(active) 명령의 방향이 목표 방향과 34도
        이내면 굳이 바꾸지 않는다. 8-명령 양자화 경계(22.5도)에서의
        진동을 없애면서, 코너(90도 이상 변화)는 즉시 전환된다.
        """
        while not self.done:
            wp = self.waypoints[self.wp_index]
            if np.linalg.norm(wp - com_xy) < self.capture_radius:
                self.wp_index += 1
                self._pullback = False
                continue
            if self.plane_capture:
                prev = self.start if (self.wp_index == 0 and self.start is not None) else (
                    self.waypoints[self.wp_index - 1] if self.wp_index > 0 else None)
                if prev is not None and float((com_xy - wp) @ (wp - prev)) >= 0.0:
                    self.wp_index += 1   # 웨이포인트의 수직면을 지남
                    self._pullback = False
                    continue
            break
        if self.done:
            return None
        target = self.waypoints[self.wp_index]
        dist = float(np.linalg.norm(target - com_xy))
        if active is not None and dist < self.close_freeze_radius:
            return active  # 근접 동결 (웨이포인트까지의 거리 기준, 앞보기 점과 무관)
        if self.lookahead > 0.0:
            prev = self.start if (self.wp_index == 0 and self.start is not None) else (
                self.waypoints[self.wp_index - 1] if self.wp_index > 0 else None)
            if prev is not None:
                ab = target - prev
                seg_len = float(np.linalg.norm(ab))
                if seg_len > 1e-6:
                    u_dir = ab / seg_len
                    rel = com_xy - prev
                    s_along = float(np.clip(rel @ u_dir, 0.0, seg_len))
                    use_carrot = True
                    if self.lookahead_deadband > 0.0:
                        e_lat = abs(float(rel[0] * u_dir[1] - rel[1] * u_dir[0]))   # 선분에서 옆으로 벗어난 거리
                        if self._pullback and e_lat <= 0.5 * self.lookahead_deadband:
                            self._pullback = False
                        elif (not self._pullback) and e_lat >= self.lookahead_deadband:
                            self._pullback = True
                        use_carrot = self._pullback
                    if use_carrot:
                        target = prev + min(s_along + self.lookahead, seg_len) * u_dir
        d_world = target - com_xy
        d_world = d_world / (np.linalg.norm(d_world) + 1e-9)
        th = np.radians(yaw_deg)
        rot = np.array([[np.cos(-th), -np.sin(-th)], [np.sin(-th), np.cos(-th)]])
        d_body = rot @ d_world
        if active is not None and active in LINEAR_COMMANDS:
            a_dir = self._joys[LINEAR_COMMANDS.index(active)]
            if float(a_dir @ d_body) >= self.hysteresis_cos:
                return active
        return LINEAR_COMMANDS[int(np.argmax(self._joys @ d_body))]


def cross_track_errors(traj: np.ndarray, waypoints: np.ndarray, start: np.ndarray) -> np.ndarray:
    """궤적 각 점에서 경로 폴리라인까지의 최단 거리."""
    nodes = np.vstack([start[None, :], waypoints])
    errs = np.full(len(traj), np.inf)
    for a, b in zip(nodes[:-1], nodes[1:]):
        ab = b - a
        t = np.clip(((traj - a) @ ab) / (ab @ ab + 1e-12), 0.0, 1.0)
        proj = a + t[:, None] * ab
        errs = np.minimum(errs, np.linalg.norm(traj - proj, axis=1))
    return errs


WP_ARROW_LEN = 0.45     # 웨이포인트 방위 화살표 길이(m)
ROBOT_ARROW_LEN = 0.45  # 로봇 현재 방위 화살표 길이(m) — 몸체에 가리지 않게 z=0.22


def add_scene_markers(viewer, waypoints: np.ndarray, headings: np.ndarray, reached_upto: int,
                      trail: list, current_seg: int,
                      com: np.ndarray | None = None, yaw_deg: float | None = None) -> None:
    """녹화 프레임에 계획 경로·주행 궤적·방위 마커를 주입한다 (렌더마다 호출).

    - 웨이포인트: 형광 초록 화살표(밑동 = 위치, 방향 = 목표 방위) + 작은 밑동 구.
      도달한 것은 어둡게, 현재 목표는 가장 밝게.
    - 로봇 방위: CoM 위 파란 화살표(몸통 yaw). 목표 화살표와의 각도 차가
      곧 방위 오차라서 회전 개입 필요 여부가 영상에서 바로 읽힌다.
    - 궤적: 빨간 점열. 현재 진행 중 세그먼트는 불투명하게, 지난 세그먼트는
      투명도를 높여 흐리게.
    """
    for i, (wp, yaw) in enumerate(zip(waypoints, headings)):
        if i < reached_upto:
            rgba = [0.05, 0.35, 0.08, 0.35]   # 도달: 어두운 초록
        elif i == reached_upto:
            rgba = [0.45, 1.0, 0.35, 0.85]    # 현재 목표: 가장 밝게
        else:
            rgba = [0.25, 1.0, 0.30, 0.55]    # 대기: 형광 초록
        pos = [float(wp[0]), float(wp[1]), 0.12]
        viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_ARROW,
                          size=[0.045, 0.045, WP_ARROW_LEN],
                          pos=pos, mat=heading_matrix(float(yaw)), rgba=rgba, label="")
        viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_SPHERE,
                          size=[0.06, 0.06, 0.06], pos=pos, rgba=rgba, label="")
    if com is not None and yaw_deg is not None:
        viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_ARROW,
                          size=[0.045, 0.045, ROBOT_ARROW_LEN],
                          pos=[float(com[0]), float(com[1]), 0.22],
                          mat=heading_matrix(float(yaw_deg)),
                          rgba=[0.25, 0.55, 1.0, 0.9], label="")
    # 씬 geom 한도(기본 1000) 보호: 궤적 마커를 균등 데시메이션
    MAX_TRAIL = 550
    if len(trail) > MAX_TRAIL:
        stride = int(np.ceil(len(trail) / MAX_TRAIL))
        trail = trail[::stride]
    for xy, seg in trail:
        rgba = [1.0, 0.12, 0.10, 0.80] if seg == current_seg else [1.0, 0.18, 0.15, 0.22]
        viewer.add_marker(type=mujoco.mjtGeom.mjGEOM_SPHERE,
                          size=[0.028, 0.028, 0.028],
                          pos=[float(xy[0]), float(xy[1]), 0.03],
                          rgba=rgba, label="")


def run(kind: str, scale: float, max_steps: int, record_every: int, out_root: Path,
        cam_fovy: float = 80.0, policy: str = "experts",
        model_path: Path | None = None, vecnorm_path: Path | None = None,
        expert_overrides: dict | None = None, tag_suffix: str = "", align_rule: str = "sign",
        align_all: bool = False, seed: int = 42, no_video: bool = False,
        start_noise: float = 0.0, path_rotate_deg: float = 0.0,
        control_period: int = 5, capture_radius: float = 0.35, plane_capture: bool = True,
        freeze_radius: float = 0.45, hysteresis_deg: float = 34.0, lookahead: float = 0.0,
        lookahead_deadband: float = 0.0) -> None:
    unified = policy == "unified"
    tag = time.strftime("%Y%m%d-%H%M%S") + f"_{kind}" + ("_unified" if unified else "") + tag_suffix
    out = out_root / tag
    out.mkdir(parents=True, exist_ok=True)

    env = gym.make(
        "horcrux_env/plane-unified-v0",
        render_mode="rgb_array",
        terminate_when_unhealthy=False,
        use_friction_chg=False,
        align_rule=align_rule,   # 전환 시작 위상 규칙: sign(현행) / lat(가로 부호 우선)
    )
    u = env.unwrapped
    if unified:
        if model_path is None or vecnorm_path is None:
            raise ValueError("--policy unified 에는 --model 과 --vecnorm 이 필요합니다 (반드시 쌍으로).")
        bank = UnifiedPolicy(model_path, vecnorm_path)
    else:
        bank = ExpertBank(expert_overrides)

    # 카메라: 광각화 + CoM 동적 추적 (모델 필드 직접 조작)
    cam_id = u.model.camera("ceiling").id
    u.model.cam_fovy[cam_id] = cam_fovy
    cam_z = float(u.model.cam_pos[cam_id][2])
    viewer = u.mujoco_renderer._get_viewer("rgb_array")

    obs, info = env.reset(seed=seed)
    # reset 추첨과 무관하게 전방 명령으로 시작
    u.set_command(VALIDATED_COMMANDS[0][1])
    # 반복 조건 (2026-09-13): 이 환경의 reset은 잡음이 0이라 시드만으로는 시작 상태가 바뀌지 않는다.
    # 시드로 정한 난수로 (1) 관절 각도에 작은 잡음을 주고 (2) 경로를 조금 회전시켜, 같은 시드면
    # 모든 조합이 같은 조건을 받도록(짝지은 비교) 한다. 둘 다 0이면 예전과 같다.
    rng = np.random.default_rng(seed)
    if start_noise > 0:
        qpos, qvel = u.data.qpos.copy(), u.data.qvel.copy()
        qpos[7:] += rng.uniform(-start_noise, start_noise, size=qpos.shape[0] - 7)   # 자유 관절(7) 뒤 14개 관절 각도
        u.set_state(qpos, qvel)
    rot_deg = float(rng.uniform(-path_rotate_deg, path_rotate_deg)) if path_rotate_deg > 0 else 0.0
    # 결함 수정 (2026-09-13): 명령을 바꾼 뒤에는 관측을 다시 만든다. 예전에는 reset의 낡은 관측(무작위 명령)이
    # 첫 행동에 쓰였고, 전문가는 joy 정규화 폭이 작아 이 한 스텝의 입력이 크게 포화됐다.
    obs = u.current_observation()
    active = 0
    start = np.asarray(u.get_robot_com()[:2], dtype=np.float64)
    # 전면 페이드 모드는 전환마다 제동 거리(감쇠 관성+정지)가 생기므로
    # capture 반경에 선반영한다 (즉시 전환 모드는 0.35로 충분).
    path = make_path(kind, scale, start, rng=rng)
    if rot_deg != 0.0:
        th = np.radians(rot_deg)
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        path[:, :2] = start + (path[:, :2] - start) @ R.T
        path[:, 2] += rot_deg
    commander = WaypointCommander(path, capture_radius=capture_radius, control_period=control_period,
                                  plane_capture=plane_capture, start=start, close_freeze_radius=freeze_radius,
                                  hysteresis_deg=hysteresis_deg, lookahead=lookahead, lookahead_deadband=lookahead_deadband)
    capture_events = []   # (스텝, 도착한 웨이포인트 번호, 그때 COM) — 놓침/오버슛 분석용 (2026-09-13)
    last_wp = 0

    traj, cmd_log, frames, switches = [], [], [], 0
    trail = []
    raw_obs = obs
    com, yaw_deg = start.copy(), 0.0  # step info(com_pos/com_ypr)로 갱신됨
    step_count = [0]

    def do_step(action):
        """물리 스텝 + 카메라 추적 + 궤적/영상 기록 (페이드 구간 포함 공통)."""
        u.model.cam_pos[cam_id][0], u.model.cam_pos[cam_id][1] = com[0], com[1]
        u.model.cam_pos[cam_id][2] = cam_z
        raw, r, te, tr, info_ = env.step(np.asarray(action, dtype=np.float32))
        c = np.asarray(info_["com_pos"][:2], dtype=np.float64)
        traj.append(c.copy())
        cmd_log.append(active)
        if step_count[0] % 4 == 0:
            trail.append((c.copy(), commander.wp_index))
        if not no_video and step_count[0] % record_every == 0:
            add_scene_markers(viewer, commander.waypoints, commander.headings, commander.wp_index,
                              trail, commander.wp_index,
                              com=c, yaw_deg=float(info_["com_ypr"][0]))
            frames.append(env.render())
        step_count[0] += 1
        return raw, c, float(info_["com_ypr"][0]), info_

    # 제어 틱은 실제 물리 스텝 수(step_count) 기준. 페이드가 55스텝을
    # 소모해도 정렬이 유지된다. 코너 오버슈트 방지는 디바운스가 아니라
    # capture 반경의 제동 거리 선반영(0.55m)으로 해결한다 — 페이드의
    # 감쇠 관성(~0.25m)+정지+상승을 코너 도착 전에 시작시킨다.
    next_control = 0
    while step_count[0] < max_steps:
        if step_count[0] >= next_control:
            next_control = step_count[0] + commander.control_period
            cmd = commander.command(com, yaw_deg, active)
            if commander.wp_index > last_wp:
                capture_events.append((step_count[0], commander.wp_index, com.copy()))
                last_wp = commander.wp_index
            if cmd is None:
                break
            if cmd != active:
                if unified:
                    # 학습(전환 커리큘럼)과 동일: 모든 전환을 위상 정렬로, 관측을 즉시
                    # 재생성해 정책이 새 gait/명령을 바로 본다. 전환 처리는 정책 몫.
                    u.set_command(VALIDATED_COMMANDS[cmd][1], align_phase=True)
                    raw_obs = u.current_observation()
                elif align_all or (active, cmd) in ALIGN_PAIRS:
                    # 위험 쌍: 위상 정렬(안정) + 짧은 행동 크로스페이드(매끄러움).
                    # 크로스페이드는 위상 정렬 위에서만 유효하다 — 정렬로 gait
                    # 부호 문맥이 일치해야 두 정책 행동의 선형 결합이 의미를
                    # 갖는다. 정렬 없이 섞으면(과거 실험) 오히려 붕괴했다.
                    # 안전 쌍엔 쓰지 않는다: 진폭 변조가 정상 전환을 약화시킴.
                    # align_all(2026-09-12): 모든 전환에 정렬 규칙(--align-rule)을 쓰되,
                    # 크로스페이드는 여전히 위험 쌍에만 — 나머지는 정렬 + 관측 즉시 재생성.
                    a_prev = bank.act(active, raw_obs)
                    u.set_command(VALIDATED_COMMANDS[cmd][1], align_phase=True)
                    # 결함 수정 (2026-09-13): 새 명령·위상의 관측을 즉시 만든다. 예전에는 크로스페이드 첫 스텝이
                    # 전환 전 관측(옛 명령·옛 모션 벡터)으로 새 전문가의 행동을 계산했다.
                    raw_obs = u.current_observation()
                    if (active, cmd) in ALIGN_PAIRS:
                        for k in range(XFADE_STEPS):
                            w = (k + 1) / XFADE_STEPS
                            a = (1 - w) * a_prev + w * bank.act(cmd, raw_obs)
                            raw_obs, com, yaw_deg, info = do_step(a)
                else:
                    u.set_command(VALIDATED_COMMANDS[cmd][1], align_phase=False)  # 안전: 즉시 k=0
                    raw_obs = u.current_observation()   # 결함 수정 (2026-09-13): 즉시 전환도 관측 재생성
                active = cmd
                switches += 1
        raw_obs, com, yaw_deg, info = do_step(bank.act(active, raw_obs))

    env.close()

    traj = np.asarray(traj)
    completed = commander.done
    errs = cross_track_errors(traj, commander.waypoints, start)
    # ---- 놓침·되돌아감 지표 (2026-09-13): 웨이포인트별 궤적 최근접 거리, 판정 원 밖으로 지나간 수,
    #      방향이 90도 넘게 꺾인(되돌아간) 전환 수. 원시 궤적과 명령 기록은 npz로 저장.
    wp_min_dist = np.array([np.linalg.norm(traj - wp, axis=1).min() for wp in commander.waypoints])
    n_missed_circle = int((wp_min_dist >= capture_radius).sum())
    cmd_arr = np.asarray(cmd_log)
    change_idx = np.flatnonzero(cmd_arr[1:] != cmd_arr[:-1]) + 1
    joy2 = {i: np.asarray(VALIDATED_COMMANDS[i][1][:2], dtype=np.float64) for i in range(len(VALIDATED_COMMANDS))}
    n_backward = int(sum(1 for i in change_idx if float(joy2[int(cmd_arr[i - 1])] @ joy2[int(cmd_arr[i])]) < -1e-9))
    np.savez_compressed(out / "trajectory.npz", traj=traj, cmd=cmd_arr, waypoints=commander.waypoints, start=start,
                        capture_steps=np.array([e[0] for e in capture_events], dtype=int),
                        capture_wp=np.array([e[1] for e in capture_events], dtype=int),
                        capture_com=np.array([e[2] for e in capture_events]).reshape(-1, 2), wp_min_dist=wp_min_dist)

    # ---- Figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nodes = np.vstack([start[None, :], commander.waypoints])
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot(nodes[:, 0], nodes[:, 1], "k--o", lw=1.5, ms=7, label="planned path")
    hd = np.radians(commander.headings)
    ax.quiver(commander.waypoints[:, 0], commander.waypoints[:, 1], np.cos(hd), np.sin(hd),
              color="tab:green", scale=12, width=0.008, zorder=6, label="target heading")
    sc = ax.scatter(traj[:, 0], traj[:, 1], c=cmd_log, cmap="tab10", s=3, label="COM trajectory")
    ax.scatter(*start, marker="s", c="g", s=90, zorder=5, label="start")
    ax.scatter(*traj[-1], marker="*", c="r", s=140, zorder=5, label="end")
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.legend()
    ax.set_title(f"{kind} (scale {scale} m) | completed={completed} | "
                 f"CTE mean {errs.mean():.3f} m / max {errs.max():.3f} m | switches {switches}")
    cb = fig.colorbar(sc, ax=ax, shrink=0.8); cb.set_label("command id")
    fig.savefig(out / "trajectory.png", dpi=140, bbox_inches="tight")

    # ---- Video
    if frames:
        imageio.mimsave(out / "path_demo.mp4", frames, fps=int(20 / record_every * 1) or 7)

    n_align = len(ALIGN_PAIRS)
    bar = "=" * 60
    lines = [
        bar,
        f"[실험] 전문가 스위칭 경로 추종 — '{kind}' 경로 (scale {scale} m)",
        f"[일시] {tag[:15]}",
        (f"[설정] 통합 정책 1개 ({model_path}), 명령 양자화 추종." if unified
         else "[설정] 전문가 10명(8방위+회전2) 스위칭, 명령 양자화 추종."),
        (f"       전환: 전부 위상정렬({align_rule}) + 관측 즉시 재생성 (정책이 전환 처리). fovy {cam_fovy:.0f}." if unified
         else (f"       전환: 전부 위상정렬({align_rule}), 위험 {n_align}쌍은 +크로스페이드({XFADE_STEPS}). fovy {cam_fovy:.0f}." if align_all
               else f"       전환: 안전=즉시k0, 위험 {n_align}쌍=위상정렬({align_rule})+크로스페이드({XFADE_STEPS}). fovy {cam_fovy:.0f}.")),
        f"[반복 조건] 시드 {seed}, 시작 관절 잡음 ±{start_noise} rad, 경로 회전 ±{path_rotate_deg}도 (실제 {rot_deg:+.1f}도)",
        f"[커맨더] 갱신 주기 {control_period}스텝 ({control_period * 0.05:.2f}초), 판정 반지름 {capture_radius} m, 수직면 판정 {'켬' if plane_capture else '끔'}, 동결 반지름 {freeze_radius} m, 히스테리시스 {hysteresis_deg}도, 앞보기 {lookahead} m{' (끔: 웨이포인트 겨냥)' if lookahead <= 0 else (f' (옆 오차 {lookahead_deadband} m 이상일 때만 앞보기 점 겨냥, 절반 아래면 해제)' if lookahead_deadband > 0 else ' (선분 위 앞보기 점 겨냥)')}",
        "-" * 60,
        f"[결과] 완주={completed}  웨이포인트 {commander.wp_index}/{len(commander.waypoints)}",
        f"[놓침] 판정 원 밖 통과 {n_missed_circle}/{len(commander.waypoints)} (웨이포인트별 최근접 거리 {' '.join(f'{d:.2f}' for d in wp_min_dist)} m) | 되돌아간 전환 {n_backward}회",
        f"       cross-track 오차: 평균 {errs.mean():.3f} m / 최대 {errs.max():.3f} m",
        f"       명령 전환 {switches}회 | 주행 {len(traj)} 스텝 ({len(traj)*0.05:.1f} s)",
        bar,
    ]
    summary = "\n".join(lines) + "\n"
    (out / "result.txt").write_text(summary, encoding="utf-8")
    print(summary)
    print("산출물:", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", choices=PATH_KINDS, default="square")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--max-steps", type=int, default=6000)
    ap.add_argument("--record-every", type=int, default=3)
    ap.add_argument("--cam-fovy", type=float, default=80.0)
    ap.add_argument("--out", type=Path, default=ROOT / "runs" / "path_follow_demo")
    ap.add_argument("--policy", choices=("experts", "unified"), default="experts",
                    help="experts: 전문가 10명 스위칭(기본) / unified: 통합 정책 1개 (--model, --vecnorm 필요)")
    ap.add_argument("--model", type=Path, default=None, help="통합 정책 PPO zip")
    ap.add_argument("--vecnorm", type=Path, default=None, help="통합 정책과 쌍인 VecNormalize pkl")
    ap.add_argument("--expert-override", action="append", default=[],
                    help="전문가 교체: name=model.zip:vecnormalize.pkl (반복 가능, 전문가 모드 전용)")
    ap.add_argument("--tag-suffix", default="", help="산출 폴더 이름 접미사 (예: _iter1)")
    ap.add_argument("--align-rule", choices=("sign", "lat"), default="sign",
                    help="전환 시작 위상 규칙: sign=현행 부호 정렬 / lat=가로 부호 우선 (2026-09-11 검증)")
    ap.add_argument("--align-all", action="store_true",
                    help="전문가 모드에서 위험 3쌍뿐 아니라 모든 전환에 위상 정렬을 적용 (크로스페이드는 위험 쌍만)")
    ap.add_argument("--seed", type=int, default=42, help="환경 reset 시드 (기본 42)")
    ap.add_argument("--no-video", action="store_true", help="영상을 만들지 않고 result.txt와 궤적 그림만 남긴다 (다중 시드 통계용)")
    ap.add_argument("--start-noise", type=float, default=0.0, help="시작 관절 각도 잡음 폭 (rad, 시드로 결정). 0이면 없음")
    ap.add_argument("--path-rotate-deg", type=float, default=0.0, help="경로 회전 폭 (도, 시드로 결정). 0이면 없음")
    ap.add_argument("--control-period", type=int, default=5, help="커맨더 갱신 주기 (스텝, 0.05초 단위). 기본 5 (2026-09-14 변경, 예전 25)")
    ap.add_argument("--capture-radius", type=float, default=0.35, help="웨이포인트 도착 판정 반지름 (m). 기본 0.35")
    ap.add_argument("--plane-capture", action=argparse.BooleanOptionalAction, default=True,
                    help="웨이포인트의 수직면을 지나면 도착으로 친다 (기본 켬, 2026-09-14 변경; --no-plane-capture 로 끔)")
    ap.add_argument("--freeze-radius", type=float, default=0.45, help="근접 동결 반지름 (m). 이 안에서는 방향 교정을 멈춤. 기본 0.45 (2026-09-14 변경, 예전 0.85)")
    ap.add_argument("--hysteresis-deg", type=float, default=34.0, help="방향 교정 히스테리시스 각도 (도). 기본 34")
    ap.add_argument("--lookahead", type=float, default=0.0,
                    help="앞보기 거리 (m). 0이면 웨이포인트 자체를 겨냥(기본, 예전 동작). 양수면 선분 위 이 거리 앞의 점을 겨냥")
    ap.add_argument("--lookahead-deadband", type=float, default=0.0,
                    help="앞보기 불감대 (m). 양수면 옆 오차가 이 값 이상일 때만 앞보기 점을 겨냥하고 절반 아래로 줄면 해제. 0이면 항상 앞보기 점")
    a = ap.parse_args()
    overrides = {}
    for o in a.expert_override:
        name, rest = o.split("=", 1)
        m, vn = rest.split(":", 1)
        overrides[name] = (Path(m), Path(vn))
    run(a.path, a.scale, a.max_steps, a.record_every, a.out, cam_fovy=a.cam_fovy,
        policy=a.policy, model_path=a.model, vecnorm_path=a.vecnorm,
        expert_overrides=overrides or None, tag_suffix=a.tag_suffix, align_rule=a.align_rule, align_all=a.align_all,
        seed=a.seed, no_video=a.no_video, start_noise=a.start_noise, path_rotate_deg=a.path_rotate_deg,
        control_period=a.control_period, capture_radius=a.capture_radius, plane_capture=a.plane_capture,
        freeze_radius=a.freeze_radius, hysteresis_deg=a.hysteresis_deg, lookahead=a.lookahead,
        lookahead_deadband=a.lookahead_deadband)
