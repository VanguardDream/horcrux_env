from __future__ import annotations

from stable_baselines3.common.callbacks import BaseCallback


class InfoMetricsCallback(BaseCallback):
    """Record scalar environment diagnostics exposed in the info dictionary."""

    METRICS = (
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
    )

    def _on_step(self) -> bool:
        for info in self.locals.get("infos", []):
            for name in self.METRICS:
                value = info.get(name)
                if value is not None:
                    self.logger.record_mean(f"env/{name}", float(value))
        return True
