from __future__ import annotations

from typing import Any

import numpy as np
from gymnasium import utils
from gymnasium.spaces import Box

from horcrux_env.envs.plane_v3 import PlaneJoyDirWorld


class PlaneDirectTorqueWorld(PlaneJoyDirWorld):
    """Plane environment with direct joint-torque actions and no gait input.

    This environment deliberately reuses PlaneJoyDirWorld's MuJoCo model,
    reward, termination, reset, filtering, and diagnostic logic. The only
    control differences are:

    * the policy directly selects signed torque for each of the 14 actuators;
    * no gait motion vector is multiplied into the action; and
    * the 14-dimensional gait motion vector is omitted from observations.
    """

    def __init__(
        self,
        torque_min: float = -2.7,
        torque_max: float = 2.7,
        **kwargs: Any,
    ) -> None:
        if not np.isfinite(torque_min) or not np.isfinite(torque_max):
            raise ValueError("torque_min and torque_max must be finite.")
        if torque_min >= torque_max:
            raise ValueError("torque_min must be smaller than torque_max.")

        # This environment never applies gait decomposition, even if a caller
        # accidentally supplies use_gait=True.
        kwargs.pop("use_gait", None)
        super().__init__(use_gait=False, **kwargs)

        actuator_low = self.model.actuator_ctrlrange[:, 0]
        actuator_high = self.model.actuator_ctrlrange[:, 1]
        if torque_min < float(np.max(actuator_low)) or torque_max > float(
            np.min(actuator_high)
        ):
            raise ValueError(
                "Requested torque range exceeds the MuJoCo actuator range "
                f"[{float(np.max(actuator_low))}, {float(np.min(actuator_high))}]."
            )

        self._torque_min = float(torque_min)
        self._torque_max = float(torque_max)
        self.action_space = Box(
            low=self._torque_min,
            high=self._torque_max,
            shape=(self.model.nu,),
            dtype=np.float32,
        )

        # 80 MuJoCo sensor values + 3 target-command values. The original
        # environment additionally exposes a 14-dimensional gait vector.
        obs_size = self.data.sensordata.size + self._joy_input.size
        self.observation_space = Box(
            low=-np.inf,
            high=np.inf,
            shape=(obs_size,),
            dtype=np.float32,
        )
        self.observation_structure = {
            "jpos": self.data.sensordata[:14],
            "jvel": self.data.sensordata[14:28],
            "jtor": self.data.sensordata[28:42],
            "link_contacts_top": self.data.sensordata[42:56],
            "link_contacts_bot": self.data.sensordata[56:70],
            "head_orientation": self.data.sensordata[70:74],
            "head_angvel": self.data.sensordata[74:77],
            "head_linacc": self.data.sensordata[77:80],
            "joy_input": self._joy_input,
        }

        # Replace the base class's pickle constructor description with this
        # subclass's public arguments.
        utils.EzPickle.__init__(
            self,
            torque_min=torque_min,
            torque_max=torque_max,
            **kwargs,
        )

    def _action_to_control(self, action: np.ndarray) -> np.ndarray:
        """Send the policy action directly to the MuJoCo actuators."""
        return np.asarray(action, dtype=np.float64).copy()

    def _control_effort(self, action: np.ndarray) -> float:
        """Treat positive and negative torque as equal control effort."""
        return float(np.sum(np.abs(action)))

    def _advance_gait(self) -> None:
        """A direct-torque policy has no gait phase to advance."""

    def _get_gait_info(self, observation: np.ndarray) -> dict:
        """Do not expose unused gait-generator data in info."""
        return {}

    def _get_obs(self, _motion_vector: np.ndarray | None = None) -> np.ndarray:
        tmp = self.data.sensordata.copy()

        if self._use_imu_mov_mean:
            tmp[-10:-6] = self._mov_mean_imu_quat.update(
                (
                    self.data.sensordata[-10].copy(),
                    self.data.sensordata[-9].copy(),
                    self.data.sensordata[-8].copy(),
                    self.data.sensordata[-7].copy(),
                )
            )
            tmp[-6:-3] = self._mov_mean_imu_vel.update(
                self.data.sensordata[-6].copy(),
                self.data.sensordata[-5].copy(),
                self.data.sensordata[-4].copy(),
            )
            tmp[-3:] = self._mov_mean_imu_acc.update(
                self.data.sensordata[-3].copy(),
                self.data.sensordata[-2].copy(),
                self.data.sensordata[-1].copy(),
            )

        tmp[42:56] = (tmp[42:56] > 1).astype(int)
        tmp[56:70] = (tmp[56:70] > 1).astype(int)
        return np.concatenate((tmp, self._joy_input), dtype=np.float32)

    def step(self, action):
        observation, reward, terminated, truncated, info = super().step(action)

        # The original environment's info indexing includes the gait vector.
        # Rebuild those entries against the direct environment's 83-D layout.
        info.update(
            {
                "joint_pos": observation[0:14].copy(),
                "joint_vel": observation[14:28].copy(),
                "head_quat": observation[70:74].copy(),
                "head_ang_vel": observation[74:77].copy(),
                "head_lin_acc": observation[77:80].copy(),
                "joy_input": observation[80:83].copy(),
            }
        )
        return observation, reward, terminated, truncated, info
