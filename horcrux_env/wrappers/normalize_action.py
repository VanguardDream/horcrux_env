from __future__ import annotations

import gymnasium as gym
import numpy as np
from gymnasium.spaces import Box


class NormalizeAction(gym.ActionWrapper):
    """Expose a normalized [-1, 1] action space for a finite Box environment."""

    def __init__(self, env: gym.Env) -> None:
        super().__init__(env)
        if not isinstance(env.action_space, Box):
            raise TypeError("NormalizeAction requires a Box action space.")
        if not (
            np.all(np.isfinite(env.action_space.low))
            and np.all(np.isfinite(env.action_space.high))
        ):
            raise ValueError("NormalizeAction requires finite action bounds.")
        if np.any(env.action_space.high <= env.action_space.low):
            raise ValueError("Every action upper bound must exceed its lower bound.")

        self._physical_low = env.action_space.low.astype(np.float64, copy=True)
        self._physical_high = env.action_space.high.astype(np.float64, copy=True)
        self._physical_dtype = env.action_space.dtype
        self.action_space = Box(
            low=-1.0,
            high=1.0,
            shape=env.action_space.shape,
            dtype=np.float32,
        )

    def action(self, action: np.ndarray) -> np.ndarray:
        normalized_action = np.asarray(action, dtype=np.float64)
        if normalized_action.shape != self.action_space.shape:
            raise ValueError(
                f"Expected action shape {self.action_space.shape}, "
                f"got {normalized_action.shape}."
            )
        normalized_action = np.clip(normalized_action, -1.0, 1.0)
        physical_action = self._physical_low + 0.5 * (
            normalized_action + 1.0
        ) * (self._physical_high - self._physical_low)
        return physical_action.astype(self._physical_dtype, copy=False)

    def reverse_action(self, action: np.ndarray) -> np.ndarray:
        physical_action = np.asarray(action, dtype=np.float64)
        if physical_action.shape != self.action_space.shape:
            raise ValueError(
                f"Expected action shape {self.action_space.shape}, "
                f"got {physical_action.shape}."
            )
        normalized_action = 2.0 * (
            physical_action - self._physical_low
        ) / (self._physical_high - self._physical_low) - 1.0
        return np.clip(normalized_action, -1.0, 1.0).astype(np.float32)
