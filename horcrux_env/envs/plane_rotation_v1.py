"""제자리 회전(CW/CCW) 태스크 환경.

PlaneJoyDirWorld의 물리·관측·행동·종료 로직을 그대로 상속하고 보상만 교체한다.
명령은 joy_input의 세 번째 성분(yaw rate)으로 준다: CCW=+1, CW=-1.

보상 구성 (2026-09-05 v2, 안정 우선 설계, CLAUDE_CHANGES 참조):
  + w_rot * clip(sign(joy_r)*yaw_vel, -target, +target)  목표 속도 포화 회전 보상
  + 효율 (포화값 기준) + healthy (roll AND 앵커<=0.2m)
  - 과속 페널티 w_over * max(|yaw|-target-tol, 0)
  - 포화 앵커 비용 w * min(max(dist-dead_zone,0), cap)
  - unhealthy_cost (권장 1000) — 종료(실패)를 근시안 지평에서도 가시화
종료(실패): roll 종료범위 이탈 '또는' 앵커 반경(0.2m) 이탈이
연속 unhealthy_max_steps 지속되면 terminated.

부모 보상 대비 제거된 항과 이유:
  - orientation_cost(|body yaw|): 제자리 회전에서는 yaw가 누적되는 것이 목표라
    정면 충돌한다.
  - proj_dist(straightness_cost): 선형 명령이 0이면 방향 벡터 정규화에서
    0-나눗셈으로 NaN이 발생한다 (개루프 실측으로 확인). 앵커 거리로 대체.
  - linear_movement/direction_similarity: 선형 명령이 없다.
"""
from typing import Tuple

import numpy as np

from horcrux_env.envs.plane_v3 import PlaneJoyDirWorld


class PlaneRotationWorld(PlaneJoyDirWorld):
    def __init__(
        self,
        anchor_cost_weight: float = 50.0,
        anchor_dead_zone: float = 0.05,
        anchor_cost_cap: float = 2.0,
        anchor_healthy_radius: float = 0.2,
        rotation_target_rate: float = 0.5,
        rotation_overspeed_tolerance: float = 0.15,
        rotation_overspeed_weight: float = 45.0,
        trans_vel_cost_weight: float = 0.0,
        joy_input: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        joy_input_random: bool = False,
        **kwargs,
    ) -> None:
        # 앵커 비용은 포화형이다: w * min(max(dist - dead_zone, 0), cap).
        # 2026-09-05 1차 학습(무한 선형 비용)에서 표류 10m 시 -500/step로
        # 보상 스케일을 지배해 critic EV가 0에 고착(회전 신호 잡음화)된
        # 실측에 따른 수정. cap=2.0이면 최대 -100/step로 유계.
        self._anchor_cost_weight = anchor_cost_weight
        self._anchor_dead_zone = anchor_dead_zone
        self._anchor_cost_cap = anchor_cost_cap
        # 안정 우선 설계 (2026-09-05 사용자 지시):
        # - 회전 보상은 목표 속도에서 포화(clip) + 초과분은 과속 페널티
        #   -> '더 빨리'가 아니라 '목표 속도로 꾸준히'가 최적이 된다.
        # - 앵커 반경(기본 0.2m) 이탈은 roll 이탈과 동일한 불건강 조건:
        #   연속 unhealthy_max_steps 지속 시 종료(실패).
        self._anchor_healthy_radius = anchor_healthy_radius
        self._rotation_target_rate = rotation_target_rate
        self._rotation_overspeed_tolerance = rotation_overspeed_tolerance
        self._rotation_overspeed_weight = rotation_overspeed_weight
        self._trans_vel_cost_weight = trans_vel_cost_weight
        self._current_anchor_distance = 0.0
        self._health_eval_step = -1
        self._is_done_cache = False
        super().__init__(
            joy_input=joy_input,
            joy_input_random=joy_input_random,
            **kwargs,
        )

    def _get_rew(self, x_vel, y_vel, joy_x, joy_y, action, cur_ypr, yaw_vel, joy_r, com_pos_after):
        joy_sign = np.sign(joy_r) if np.abs(joy_r) > 1e-2 else 0.0
        aligned_yaw = joy_sign * yaw_vel  # 명령 방향 회전이면 양수

        # 회전 정렬 보상: 목표 속도에서 포화 (안정 우선 — 초과 속도는 무보상)
        tgt = self._rotation_target_rate
        capped_yaw = float(np.clip(aligned_yaw, -tgt, tgt))
        angular_movement_reward = self._rotation_reward_weight * capped_yaw * np.abs(joy_r)

        # 과속 페널티: 목표+허용치를 넘는 회전 크기는 방향 불문 벌점
        overspeed = max(abs(yaw_vel) - tgt - self._rotation_overspeed_tolerance, 0.0)
        overspeed_cost = self._rotation_overspeed_weight * overspeed

        # 효율 보상 (포화값 기준 — 과속이 효율을 부풀리지 않도록)
        if np.linalg.norm(action) > 1e-3:
            efficiency = capped_yaw / (np.linalg.norm(action) * 1e-2 + 1e-1)
        else:
            efficiency = 0.0
        efficiency_reward = self._efficiency_reward_weight * efficiency

        healthy_reward = self.healthy_reward
        rewards = angular_movement_reward + efficiency_reward + healthy_reward

        # 제자리 이탈 비용: 에피소드 시작 COM으로부터의 평면 거리 (포화형)
        anchor_distance = float(
            np.linalg.norm(np.asarray(com_pos_after) - self._initial_com[0:2])
        )
        self._current_anchor_distance = anchor_distance
        anchor_excess = min(
            max(anchor_distance - self._anchor_dead_zone, 0.0),
            self._anchor_cost_cap,
        )
        anchor_cost = self._anchor_cost_weight * anchor_excess

        # 보조: 순간 병진 속도 비용 (기본 가중치 0)
        trans_vel = float(np.linalg.norm([x_vel, y_vel]))
        trans_vel_cost = self._trans_vel_cost_weight * trans_vel

        ctrl_cost = self._ctrl_cost_weight * self._control_effort(action) * (1 / 30)
        unhealthy_cost = self.is_terminated * self._unhealthy_cost_weight

        costs = anchor_cost + trans_vel_cost + overspeed_cost + ctrl_cost + unhealthy_cost
        reward = rewards - costs

        reward_info = {
            # 부모와 동일 키 (미사용 항은 0으로 유지해 로깅 호환)
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
            "rotation_alignment": joy_sign * np.sign(yaw_vel) if np.abs(yaw_vel) > 1e-3 else 0.0,
            "reward_func_orientation": cur_ypr,
            "velocity_theta": 0.0,
            # 회전 태스크 신규 키
            "cost_anchor": -anchor_cost,
            "cost_overspeed": -overspeed_cost,
            "cost_trans_vel": -trans_vel_cost,
            "anchor_distance": anchor_distance,
            "aligned_yaw_vel": aligned_yaw,
        }
        return reward, reward_info

    @property
    def is_healthy(self):
        # 부모(roll 건강 범위)에 앵커 반경 조건을 추가
        return bool(
            super().is_healthy
            and self._current_anchor_distance <= self._anchor_healthy_radius
        )

    @property
    def is_terminated(self):
        # 앵커 반경 이탈도 roll 이탈과 동일한 불건강 조건으로 취급한다.
        # 부모와 달리 카운터 갱신을 '스텝당 1회'로 멱등화한다: 부모 step()이
        # 이 property를 보상 계산 내부와 종료 판정에서 두 번 읽는데, 그대로
        # 두면 (1) 카운터가 이중 증가하고 (2) 임계 도달이 보상 계산 밖에서
        # 일어나 종료 페널티(unhealthy_cost)가 보상에 실리지 않는 결함이
        # 생긴다 (2026-09-05 검증 T1에서 실측).
        step = self._n_step
        if self._health_eval_step != step:
            self._health_eval_step = step
            y, p, r = self._cur_euler_ypr
            t_min_r, t_max_r = self._terminating_roll_range
            roll_ok = t_min_r <= r <= t_max_r
            anchor_ok = self._current_anchor_distance <= self._anchor_healthy_radius
            if roll_ok and anchor_ok:
                self._unhealth_steps = 0
            else:
                self._unhealth_steps += 1
            self._is_done_cache = self._unhealth_steps >= self._unhealthy_max_steps
        return self._is_done_cache
