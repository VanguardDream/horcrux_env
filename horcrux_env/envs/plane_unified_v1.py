"""10-명령 통합 환경 (8방위 이동 + CW/CCW 제자리 회전).

PlaneJoyDirWorld를 상속해 물리·관측·행동을 그대로 쓰되:
  - reset마다 검증된 10개 명령 중 하나를 추첨(command_weights로 조정 가능)
    하고 GaitProvider가 대응 gait를 적용한다. 에피소드 중 전환은 set_command
    이 담당하며, 위험 gait 쌍은 align_phase=True로 위상 정렬 전환한다.
  - 보상은 명령 조건부로 전환된다: 선형 명령이면 부모(방위)의 보상,
    yaw 명령이면 회전 v2 안정 우선 보상(목표 속도 포화 + 과속 페널티 +
    앵커 비용). straightness_cost의 0-나눗셈 함정은 회전 분기에서 원천
    회피된다.
  - 건강/종료도 명령 조건부다: 회전 명령에서만 앵커 반경(0.2m) 이탈이
    불건강 조건에 추가되고, 복구 시간은 rotation_recovery_steps(기본 60,
    2026-09-07 앵커 표류 진단의 처방)를 쓴다. 카운터는 스텝당 1회 갱신
    (부모의 이중 호출 결함 수정판 — plane_rotation_v1과 동일).

능동 gait 인터페이스 (사전 정의 패턴을 넘어서는 확장 지점):
  - set_gait(params, align_phase=True): 에피소드 중 임의 시점 gait 교체.
    새 gait 주기 중 현재 motion vector와 부호 일치도 최대인 위상에서 시작해
    전환을 매끄럽게 한다 (2026-09-08: 소프트 페이드를 대체한 근본책).
  - set_command(joy, switch_gait=True): 명령 교체(+선택적 gait 전환).
  - 정책 관측 계약 불변: motion_vector가 매 스텝 현재 gait를 노출하므로
    중간 교체도 정책이 관측한다. 추후 상위 정책이 이 API로 gait를
    행동화하는 계층적 RL로 확장 가능.

전환 커리큘럼 (2026-09-09, 전환 학습용 — switch_enabled=True일 때만):
  - reset마다 전환 횟수 n∈switch_count_range, 전환 시점을 최소 체류
    switch_min_dwell 간격으로 에피소드 안에 균등 무작위 배치한다.
  - 전환 시 다음 명령은 현재 명령을 제외한 나머지에서 추첨한다
    (switch_pair_weights (n,n) 행렬로 from->to 가중 가능, 기본 균등 → 90 순서쌍).
  - 전환은 물리 스텝 뒤·관측 반환 전에 적용해, 정책이 그 스텝의 관측에서
    새 motion vector와 joy를 바로 본다 (1스텝 불일치 없음). 해당 스텝의
    보상은 옛 명령 기준 — 그 행동은 옛 명령을 위해 낸 것이므로 정합하다.
  - switch_mode: "align"(위상 정렬) | "k0"(즉시 재시작) | "random"(50:50).
  - random_init_phase=True: 초기 gait 위상 k도 무작위 → 전환 순간의 몸 상태와
    위상이 다양해진다. episode_horizon으로 부모의 6000스텝 truncation을
    짧게 덮어쓴다 (gym.make의 max_episode_steps와 이름이 겹치면 env에
    전달되지 않으므로 다른 이름을 쓴다 — 2026-09-09 스모크에서 발견).
"""
from typing import Optional, Sequence, Tuple

import numpy as np

from horcrux_env.envs.gait_provider import CommandGaitTable, GaitProvider
from horcrux_env.envs.phase_align import RULES as ALIGN_RULES, start_k
from horcrux_env.envs.plane_v3 import PlaneJoyDirWorld


class PlaneUnifiedWorld(PlaneJoyDirWorld):
    def __init__(
        self,
        command_weights: Optional[Sequence[float]] = None,
        gait_provider: Optional[GaitProvider] = None,
        # 회전 명령 전용 보상/건강 파라미터 (plane_rotation_v1 v2 + v3 처방)
        rotation_target_rate: float = 0.5,
        rotation_overspeed_tolerance: float = 0.15,
        rotation_overspeed_weight: float = 45.0,
        anchor_cost_weight: float = 50.0,
        anchor_dead_zone: float = 0.0,
        anchor_cost_cap: float = 2.0,
        anchor_healthy_radius: float = 0.2,
        rotation_recovery_steps: int = 60,
        rotation_unhealthy_cost_weight: float = 1000.0,
        # 앵커 처리 방식 (2026-09-09 전환 학습 설계): 기본값은 회전 계보와 동일한
        # "이탈 = 불건강(종료)". anchor_terminate=False면 종료 대신 근접 보상
        # w·max(0, 1 − d/r)로 앵커 유지를 유도한다 — 전환 직후 관성 미끄러짐이
        # 치명이 아니라 학습 가능한(진폭 조절로 줄이는) 손실이 되도록.
        anchor_terminate: bool = True,
        anchor_proximity_reward_weight: float = 0.0,
        anchor_proximity_radius: float = 0.2,
        # 전환 커리큘럼 (기본 꺼짐 → 기존 동작 보존)
        switch_enabled: bool = False,
        switch_count_range: Sequence[int] = (1, 4),
        switch_min_dwell: int = 100,
        switch_mode: str = "align",
        switch_pair_weights: Optional[Sequence[Sequence[float]]] = None,
        random_init_phase: bool = False,
        episode_horizon: Optional[int] = None,
        # 전환 시작 위상 규칙 (phase_align.py): 'sign' = 현행 부호 정렬, 'lat' = 가로 부호 우선 (2026-09-11 검증)
        align_rule: str = "sign",
        **kwargs,
    ) -> None:
        assert align_rule in ALIGN_RULES, f"align_rule 오류: {align_rule} (가능: {ALIGN_RULES})"
        self._align_rule = str(align_rule)
        self._provider = gait_provider or CommandGaitTable()
        n = len(self._provider)
        if command_weights is None:
            self._command_weights = np.full(n, 1.0 / n)
        else:
            w = np.asarray(command_weights, dtype=np.float64)
            assert len(w) == n and w.sum() > 0, "command_weights 길이/합 오류"
            self._command_weights = w / w.sum()

        assert switch_mode in ("align", "k0", "random"), f"switch_mode 오류: {switch_mode}"
        self._switch_enabled = bool(switch_enabled)
        self._switch_count_range = (int(switch_count_range[0]), int(switch_count_range[1]))
        self._switch_min_dwell = int(switch_min_dwell)
        self._switch_mode = switch_mode
        if switch_pair_weights is None:
            pw = np.ones((n, n), dtype=np.float64)
        else:
            pw = np.asarray(switch_pair_weights, dtype=np.float64)
            assert pw.shape == (n, n), "switch_pair_weights는 (n,n) from->to 행렬"
        np.fill_diagonal(pw, 0.0)  # 자기 자신으로의 전환은 없음
        assert np.all(pw.sum(axis=1) > 0), "각 명령에서 갈 수 있는 다음 명령이 있어야 함"
        self._switch_pair_weights = pw / pw.sum(axis=1, keepdims=True)
        self._random_init_phase = bool(random_init_phase)
        self._episode_horizon = None if episode_horizon is None else int(episode_horizon)
        self._switch_times: list[int] = []
        self._switch_ptr = 0
        self._switch_count = 0
        self._last_switch_step = -1

        self._rotation_target_rate = rotation_target_rate
        self._rotation_overspeed_tolerance = rotation_overspeed_tolerance
        self._rotation_overspeed_weight = rotation_overspeed_weight
        self._anchor_cost_weight = anchor_cost_weight
        self._anchor_dead_zone = anchor_dead_zone
        self._anchor_cost_cap = anchor_cost_cap
        self._anchor_healthy_radius = anchor_healthy_radius
        self._rotation_recovery_steps = int(rotation_recovery_steps)
        self._rotation_unhealthy_cost_weight = rotation_unhealthy_cost_weight
        self._anchor_terminate = bool(anchor_terminate)
        self._anchor_proximity_reward_weight = float(anchor_proximity_reward_weight)
        self._anchor_proximity_radius = float(anchor_proximity_radius)

        self._command_id = 0
        self._current_anchor_distance = 0.0
        self._health_eval_step = -1
        self._is_done_cache = False

        # 방위 계보 공통값을 기본으로 (부모 기본 0.5는 미검증 값)
        kwargs.setdefault("rotation_norm_cost_weight", 10.0)
        kwargs.setdefault("proj_dist_cost_weight", 0.0)
        # 명령 추첨은 이 클래스가 담당 — 부모의 (전방 전용) 무작위화는 끈다
        kwargs["joy_input_random"] = False
        kwargs.setdefault("joy_input", (1.0, 0.0, 0.0))
        kwargs.setdefault("gait_params", tuple(self._provider.params_for((1.0, 0.0, 0.0))))
        super().__init__(**kwargs)

    # ------------------------------------------------------------------ 명령/gait API
    @property
    def command_id(self) -> int:
        return self._command_id

    @property
    def is_rotation_command(self) -> bool:
        return abs(float(self._joy_input[2])) > 0.5

    def set_command(self, joy_input: Sequence[float], switch_gait: bool = True, align_phase: bool = False) -> None:
        """에피소드 중 명령 교체 (능동 제어/커리큘럼용).

        회전 명령으로 진입하면 앵커를 '현재 COM'으로 재설정한다 — 앵커가
        에피소드 시작점에 남아 있으면 중간 전환 시 즉시 이탈 판정되는
        낡은 기준점이 되기 때문이다 (2026-09-08 설계 검토에서 수정).
        불건강 카운터도 명령 전환 시 초기화한다.
        """
        was_rotation = self.is_rotation_command
        self._joy_input = np.asarray(joy_input, dtype=np.float64)
        self._command_id = self._provider.command_index(self._joy_input)
        if self.is_rotation_command and not was_rotation:
            self._initial_com = self.get_robot_com().copy()
            self._current_anchor_distance = 0.0
        self._unhealth_steps = 0
        if switch_gait:
            self.set_gait(self._provider.params_for(self._joy_input), align_phase=align_phase)

    def current_observation(self) -> np.ndarray:
        """현재 gait 위상·명령 기준으로 관측을 다시 만든다 (동작 변경 없음).

        외부에서 set_command()로 명령을 바꾼 직후, 정책이 학습 때(전환 커리큘럼)와
        같이 새 motion vector/joy를 바로 보게 하려면 이 관측으로 행동을 결정한다.
        """
        return self._get_obs(self._motion_vector)

    def set_gait(self, params: Sequence[float], align_phase: bool = False) -> None:
        """에피소드 중 gait 교체.

        align_phase=False(기본): k=0 재시작 — 전문가가 모두 k=0에서 학습돼서
        안전한 전환(부호 충돌 없음)에는 이 익숙한 초기 위상이 최적이다
        (전체 사각형 A/B: k=0 CTE 0.193 vs 위상정렬 0.448).

        align_phase=True: 새 gait 주기 중 현재 motion vector와 부호 일치도
        최대인 위상 k에서 시작 — 부호가 충돌하는 위험 gait 쌍(역재생↔순재생
        등)에서만 이득이다. 위험 3쌍 152/61/156도 -> 1.0/0.5/3.1도, 시간
        지연·감속 표류 없이 소프트 페이드를 대체한다. 안전 쌍엔 쓰지 않는다.
        """
        new_params = tuple(params)
        cur_mvec = self._motion_vector.copy() if getattr(self, "_motion_vector", None) is not None else None
        self._gait_params = new_params
        self._gait.reset(params=new_params, frame_skip=self.frame_skip)
        if align_phase and cur_mvec is not None and np.any(cur_mvec):
            # 시작 위상 규칙은 phase_align.py 공유: 'sign' = 현행 부호 정렬(내적 최대),
            # 'lat' = 가로 부호 우선(2026-09-11 검증). getMvec(k)는 역재생 gait면 열 -k를
            # 돌려주므로 start_k가 k = -col 로 뒤집는다 (2026-09-09 발견).
            self._k = start_k(self._gait, cur_mvec, getattr(self, "_align_rule", "sign"))
        else:
            self._k = 0
        self._motion_vector = self._gait.getMvec(self._k).copy()

    # ------------------------------------------------------------------ reset
    def reset_model(self):
        idx = int(self.np_random.choice(len(self._provider), p=self._command_weights))
        self._command_id = idx
        self._joy_input = np.asarray(self._provider.joy(idx), dtype=np.float64)
        self._gait_params = tuple(self._provider.params(idx))
        self._gait.reset(params=self._gait_params, frame_skip=self.frame_skip)
        self._current_anchor_distance = 0.0
        self._health_eval_step = -1
        self._is_done_cache = False
        # 부모가 상태/필터 리셋(새 gait 주기 기준)과 관측 생성을 수행한다.
        observation = super().reset_model()
        # 부모는 reset에서 _motion_vector를 갱신하지 않아 이전 에피소드의 벡터가
        # 첫 스텝에 잔존한다 (첫 에피소드는 0 벡터). 통합 env는 gait가 에피소드마다
        # 바뀌므로 반드시 현재 gait의 위상 k 벡터로 명시 초기화한다.
        if self._random_init_phase:
            self._k = int(self.np_random.integers(self._gait.Mvecs))
            self._motion_vector = self._gait.getMvec(self._k).copy()
            observation = self._get_obs(self._motion_vector)
        else:
            self._motion_vector = self._gait.getMvec(self._k).copy()
        self._schedule_switches()
        return observation

    # ------------------------------------------------------------------ 전환 커리큘럼
    def _schedule_switches(self) -> None:
        self._switch_ptr = 0
        self._switch_count = 0
        self._last_switch_step = -1
        self._switch_times = []
        if not self._switch_enabled:
            return
        horizon = self._episode_horizon if self._episode_horizon is not None else 6000
        lo, hi = self._switch_min_dwell, horizon - self._switch_min_dwell
        if hi <= lo:
            return
        n = int(self.np_random.integers(self._switch_count_range[0], self._switch_count_range[1] + 1))
        candidates = np.sort(self.np_random.integers(lo, hi, size=n))
        last = -np.inf
        for t in candidates:  # 최소 체류 간격 위반 후보는 버린다 (횟수는 n 이하가 됨)
            if t - last >= self._switch_min_dwell:
                self._switch_times.append(int(t))
                last = t

    def _draw_next_command(self, current: int) -> int:
        return int(self.np_random.choice(len(self._provider), p=self._switch_pair_weights[current]))

    def _apply_scheduled_switch(self, info: dict) -> Optional[np.ndarray]:
        """예약된 전환 시점이면 명령을 교체하고 새 관측을 돌려준다 (아니면 None)."""
        if not self._switch_enabled or self._switch_ptr >= len(self._switch_times):
            return None
        if self._n_step < self._switch_times[self._switch_ptr]:
            return None
        prev = self._command_id
        nxt = self._draw_next_command(prev)
        if self._switch_mode == "align":
            align = True
        elif self._switch_mode == "k0":
            align = False
        else:
            align = bool(self.np_random.random() < 0.5)
        self.set_command(self._provider.joy(nxt), switch_gait=True, align_phase=align)
        self._switch_ptr += 1
        self._switch_count += 1
        self._last_switch_step = self._n_step
        info.update(switched=True, switch_from=prev, switch_to=nxt, switch_aligned=align)
        return self._get_obs(self._motion_vector)

    def step(self, action):
        observation, reward, terminated, truncated, info = super().step(action)
        info.setdefault("switched", False)
        new_obs = self._apply_scheduled_switch(info)
        if new_obs is not None:
            observation = new_obs
            # 관측 파생 항목도 새 gait/명령 기준으로 갱신
            info["motion_vector"] = observation[-17:-3].copy()
            info["joy_input"] = observation[-3:].copy()
        info["switch_count"] = self._switch_count
        info["steps_since_switch"] = (
            self._n_step - self._last_switch_step if self._last_switch_step >= 0 else -1
        )
        if self._episode_horizon is not None and self._n_step >= self._episode_horizon:
            truncated = True
        return observation, reward, terminated, truncated, info

    # ------------------------------------------------------------------ 보상 (명령 조건부)
    def _get_rew(self, x_vel, y_vel, joy_x, joy_y, action, cur_ypr, yaw_vel, joy_r, com_pos_after):
        if abs(joy_r) > 0.5:
            reward, info = self._rotation_rew(action, yaw_vel, joy_r, com_pos_after)
        else:
            # 선형 명령: 방위 계보와 동일한 부모 보상 (joy 선형부가 0이 아니라
            # straightness_cost도 안전)
            reward, info = super()._get_rew(
                x_vel, y_vel, joy_x, joy_y, action, cur_ypr, yaw_vel, joy_r, com_pos_after
            )
            # 앵커 상태는 회전 명령 전환 대비 항상 추적한다 (비용은 미부과)
            self._current_anchor_distance = float(
                np.linalg.norm(np.asarray(com_pos_after) - self._initial_com[0:2])
            )
            info["anchor_distance"] = self._current_anchor_distance
        info["command_id"] = self._command_id
        return reward, info

    def _rotation_rew(self, action, yaw_vel, joy_r, com_pos_after):
        joy_sign = np.sign(joy_r)
        aligned_yaw = joy_sign * yaw_vel
        tgt = self._rotation_target_rate
        capped_yaw = float(np.clip(aligned_yaw, -tgt, tgt))
        angular_movement_reward = self._rotation_reward_weight * capped_yaw * abs(joy_r)

        overspeed = max(abs(yaw_vel) - tgt - self._rotation_overspeed_tolerance, 0.0)
        overspeed_cost = self._rotation_overspeed_weight * overspeed

        if np.linalg.norm(action) > 1e-3:
            efficiency = capped_yaw / (np.linalg.norm(action) * 1e-2 + 1e-1)
        else:
            efficiency = 0.0
        efficiency_reward = self._efficiency_reward_weight * efficiency

        healthy_reward = self.healthy_reward

        anchor_distance = float(
            np.linalg.norm(np.asarray(com_pos_after) - self._initial_com[0:2])
        )
        self._current_anchor_distance = anchor_distance
        anchor_excess = min(
            max(anchor_distance - self._anchor_dead_zone, 0.0), self._anchor_cost_cap
        )
        anchor_cost = self._anchor_cost_weight * anchor_excess
        # 근접 보상: 앵커 위 w, 반경 r에서 0으로 선형 감소, 밖은 0 (유한·단조)
        anchor_proximity_reward = self._anchor_proximity_reward_weight * max(
            0.0, 1.0 - anchor_distance / self._anchor_proximity_radius
        )

        ctrl_cost = self._ctrl_cost_weight * self._control_effort(action) * (1 / 30)
        unhealthy_cost = self.is_terminated * self._rotation_unhealthy_cost_weight

        reward = (
            angular_movement_reward + efficiency_reward + healthy_reward + anchor_proximity_reward
            - anchor_cost - overspeed_cost - ctrl_cost - unhealthy_cost
        )
        info = {
            "reward_linear_movement": 0.0,
            "reward_angular_movement": angular_movement_reward,
            "reward_efficiency": efficiency_reward,
            "reward_healthy": healthy_reward,
            "cost_ctrl": -ctrl_cost,
            "cost_unhealthy": -unhealthy_cost,
            "cost_orientation": 0.0,
            "cost_yaw_vel": 0.0,
            "cost_proj_dist": 0.0,
            "direction_similarity": 0.0,
            "rotation_alignment": joy_sign * np.sign(yaw_vel) if abs(yaw_vel) > 1e-3 else 0.0,
            "reward_func_orientation": self._cur_euler_ypr,
            "velocity_theta": 0.0,
            "cost_anchor": -anchor_cost,
            "cost_overspeed": -overspeed_cost,
            "reward_anchor_proximity": anchor_proximity_reward,
            "anchor_distance": anchor_distance,
            "aligned_yaw_vel": aligned_yaw,
        }
        return reward, info

    # ------------------------------------------------------------------ 건강/종료 (명령 조건부, 스텝당 1회)
    @property
    def is_healthy(self):
        healthy = super().is_healthy
        if self.is_rotation_command and self._anchor_terminate:
            healthy = bool(healthy and self._current_anchor_distance <= self._anchor_healthy_radius)
        return healthy

    @property
    def is_terminated(self):
        step = self._n_step
        if self._health_eval_step != step:
            self._health_eval_step = step
            y, p, r = self._cur_euler_ypr
            t_min_r, t_max_r = self._terminating_roll_range
            ok = t_min_r <= r <= t_max_r
            if self.is_rotation_command:
                if self._anchor_terminate:
                    ok = ok and (self._current_anchor_distance <= self._anchor_healthy_radius)
                limit = self._rotation_recovery_steps
            else:
                limit = self._unhealthy_max_steps
            if ok:
                self._unhealth_steps = 0
            else:
                self._unhealth_steps += 1
            self._is_done_cache = self._unhealth_steps >= limit
        return self._is_done_cache
