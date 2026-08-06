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

    def __init__(self, per_component: bool = True, verbose: int = 0):
        super().__init__(verbose)
        self._per_component = per_component

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
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
