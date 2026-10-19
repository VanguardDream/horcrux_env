from __future__ import annotations

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback


class InfoMetricsCallback(BaseCallback):
    """Record environment diagnostics exposed in the info dictionary.

    Tag namespaces:
      env/         scalar metrics and vector aggregates (rollout means)
      env_detail/  per-component vector entries (jpos_00, act_03, ...)

    Existing tag names are preserved so TensorBoard comparisons against
    earlier runs stay valid; everything beyond the original 15 scalars +
    com_yaw is additive. Keys absent from an env's info (e.g. motion_vector
    in the direct-torque env) are skipped silently. Intentionally excluded:
    motionMatrix (large, static), gait_params / init_* (static; recorded in
    the config and TRAINING_HISTORY), step (redundant with timesteps).

    per_component=False disables the env_detail/ namespace if the tag count
    or callback overhead ever becomes a concern.
    """

    SCALAR_METRICS = (
        "x_velocity",
        "y_velocity",
        "yaw_velocity",
        "direction_similarity",
        "rotation_alignment",
        "reward_linear_movement",
        "reward_angular_movement",
        "reward_efficiency",
        "reward_healthy",
        "cost_ctrl",
        "cost_unhealthy",
        "cost_orientation",
        "cost_yaw_vel",
        "cost_proj_dist",
        "velocity_theta",
        "x_displacement",
        "y_displacement",
        "distance_from_origin",
        # plane-rotation-v0 전용 (다른 환경은 키가 없어 자동 생략)
        "anchor_distance",
        "aligned_yaw_vel",
        "cost_anchor",
        "cost_overspeed",
        "cost_trans_vel",
        "reward_anchor_proximity",  # plane-unified-v0 앵커 근접 보상 (2026-09-09)
        "cost_tilt",                # plane-moving-init-v0 iteration 3 기울기 벌점 (2026-09-11)
        "cost_push_tilt",           # plane-moving-init-v0 iteration 3 기운 채로 세게 밀기 벌점
    )

    # info key -> (tag prefix, component labels or None for index numbering)
    PER_COMPONENT_KEYS = {
        "joint_pos": ("jpos", None),
        "joint_vel": ("jvel", None),
        "action": ("act", None),
        "motion_vector": ("mvec", None),
        "head_quat": ("head_quat", ("w", "x", "y", "z")),
        "head_ang_vel": ("head_angvel", ("x", "y", "z")),
        "head_lin_acc": ("head_linacc", ("x", "y", "z")),
        "joy_input": ("joy", ("x", "y", "yaw")),
        "friction_coeff": ("friction", ("slide", "torsion", "roll")),
        "step_ypr": ("step_ypr", ("yaw", "pitch", "roll")),
        "reward_func_orientation": ("rew_ori", ("yaw", "pitch", "roll")),
    }

    # 전환 후 관찰 창 (스텝): 보상 평균 창 / 실패(종료) 판정 창
    SWITCH_REWARD_WINDOW = 50
    SWITCH_FAIL_WINDOW = 100

    def __init__(self, per_component: bool = True, verbose: int = 0):
        super().__init__(verbose)
        self._per_component = per_component
        self._switch_trackers: list[dict | None] = []

    def _track_switch(self, i: int, info: dict, reward: float, done: bool) -> None:
        """전환 커리큘럼(plane-unified-v0 switch_enabled) 통계.

        env_switch/post50_reward      전환 직후 50스텝 평균 보상 (회복 속도)
        env_switch/fail_within100     전환 후 100스텝 내 종료(낙상/앵커 이탈) 비율
        env_switch/*_to_XX            도착 명령별 분해
        env_switch/per_episode        에피소드당 전환 횟수
        """
        if i >= len(self._switch_trackers):
            self._switch_trackers.extend([None] * (i + 1 - len(self._switch_trackers)))
        tr = self._switch_trackers[i]
        if tr is not None:
            tr["t"] += 1
            if tr["t"] <= self.SWITCH_REWARD_WINDOW:
                tr["rsum"] += reward
            failed = done and not info.get("TimeLimit.truncated", False)
            finish = failed or done or tr["t"] >= self.SWITCH_FAIL_WINDOW
            if finish:
                n_r = min(tr["t"], self.SWITCH_REWARD_WINDOW)
                to = tr["to"]
                self.logger.record_mean("env_switch/post50_reward", tr["rsum"] / max(n_r, 1))
                self.logger.record_mean("env_switch/fail_within100", float(failed))
                self.logger.record_mean(f"env_switch/post50_reward_to_{to:02d}", tr["rsum"] / max(n_r, 1))
                self.logger.record_mean(f"env_switch/fail_to_{to:02d}", float(failed))
                self._switch_trackers[i] = None
        if info.get("switched", False):
            self._switch_trackers[i] = dict(t=0, rsum=0.0, to=int(info["switch_to"]))
        if done:
            self._switch_trackers[i] = None

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        rewards = self.locals.get("rewards")
        dones = self.locals.get("dones")
        for i, info in enumerate(infos):
            if "switch_count" in info and rewards is not None and dones is not None:
                self._track_switch(i, info, float(rewards[i]), bool(dones[i]))
            # 인계 시작 환경(plane-moving-init-v0): 시작 유형별 에피소드 통계
            episode = info.get("episode")
            if episode is not None and "moving_init" in info:
                kind = "moving" if info["moving_init"] else "rest"
                self.logger.record_mean(f"env_init/return_{kind}", float(episode["r"]))
                self.logger.record_mean(f"env_init/eplen_{kind}", float(episode["l"]))
                if info["moving_init"]:
                    failed = float(episode["l"] <= 100 and not info.get("TimeLimit.truncated", False))
                    self.logger.record_mean("env_init/fail100_moving", failed)
                    src = int(info.get("source_cmd", -1))
                    if src >= 0:
                        self.logger.record_mean(f"env_init/fail100_from_{src:02d}", failed)
                self.logger.record_mean("env_init/moving_frac", float(info["moving_init"]))
            # 통합 환경(plane-unified-v0): 명령별 에피소드 리턴/길이
            command_id = info.get("command_id")
            if episode is not None and command_id is not None:
                cid = int(command_id)
                self.logger.record_mean(f"env_cmd/return_{cid:02d}", float(episode["r"]))
                self.logger.record_mean(f"env_cmd/eplen_{cid:02d}", float(episode["l"]))
                if "switch_count" in info:
                    self.logger.record_mean("env_switch/per_episode", float(info["switch_count"]))

            for name in self.SCALAR_METRICS:
                value = info.get(name)
                if value is not None:
                    self.logger.record_mean(f"env/{name}", float(value))

            # COM 위치/자세. plane_v3의 com_ypr은 ZYX 순서: yaw, pitch, roll.
            com_pos = info.get("com_pos")
            if com_pos is not None:
                self.logger.record_mean("env/com_x", float(com_pos[0]))
                self.logger.record_mean("env/com_y", float(com_pos[1]))
                self.logger.record_mean("env/com_z", float(com_pos[2]))

            com_ypr = info.get("com_ypr")
            if com_ypr is not None:
                com_yaw_deg = float(com_ypr[0])
                # 기존 태그명 유지 (이전 run들과의 TB 비교 연속성)
                self.logger.record_mean("env/com_yaw_deg", com_yaw_deg)
                self.logger.record_mean("env/abs_com_yaw_deg", abs(com_yaw_deg))
                self.logger.record_mean("env/com_pitch_deg", float(com_ypr[1]))
                self.logger.record_mean("env/com_roll_deg", float(com_ypr[2]))
                self.logger.record_mean("env/abs_com_roll_deg", abs(float(com_ypr[2])))

            # 벡터 집계: 크기 요약 (exploit 탐지·행동 스케일 모니터링용)
            for key, tag in (("action", "action"), ("joint_pos", "jpos"), ("joint_vel", "jvel")):
                vec = info.get(key)
                if vec is not None:
                    arr = np.abs(np.asarray(vec, dtype=np.float64))
                    self.logger.record_mean(f"env/{tag}_abs_mean", float(arr.mean()))
                    self.logger.record_mean(f"env/{tag}_abs_max", float(arr.max()))
            for key, tag in (("head_ang_vel", "head_angvel_norm"), ("head_lin_acc", "head_linacc_norm")):
                vec = info.get(key)
                if vec is not None:
                    self.logger.record_mean(f"env/{tag}", float(np.linalg.norm(np.asarray(vec, dtype=np.float64))))

            # 성분별 상세 로깅
            if self._per_component:
                for key, (prefix, labels) in self.PER_COMPONENT_KEYS.items():
                    vec = info.get(key)
                    if vec is None:
                        continue
                    arr = np.asarray(vec, dtype=np.float64).ravel()
                    if labels is None:
                        for i, v in enumerate(arr):
                            self.logger.record_mean(f"env_detail/{prefix}_{i:02d}", float(v))
                    else:
                        for label, v in zip(labels, arr):
                            self.logger.record_mean(f"env_detail/{prefix}_{label}", float(v))
        return True
