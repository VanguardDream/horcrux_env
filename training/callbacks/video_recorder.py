from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import gymnasium as gym
from gymnasium.wrappers import RecordVideo
from stable_baselines3.common.callbacks import BaseCallback

from horcrux_env.wrappers import NormalizeAction


class VideoRecorderCallback(BaseCallback):
    """Record the current policy in an isolated evaluation environment."""

    def __init__(
        self,
        env_id: str,
        env_kwargs: dict[str, Any],
        video_folder: Path,
        start_iteration: int,
        record_every_iterations: int | None,
        video_length: int,
        seed: int,
        deterministic: bool = True,
        normalize_action: bool = False,
        verbose: int = 1,
        track_com: bool = True,
        cam_fovy: float | None = 80.0,
    ) -> None:
        super().__init__(verbose=verbose)
        if start_iteration < 1:
            raise ValueError("video.start_iteration must be at least 1.")
        if record_every_iterations is not None and record_every_iterations < 1:
            raise ValueError("video.record_every_iterations must be positive or null.")
        if video_length < 1:
            raise ValueError("video.video_length must be positive.")

        self.env_id = env_id
        self.env_kwargs = dict(env_kwargs)
        self.video_folder = video_folder
        self.start_iteration = start_iteration
        self.record_every_iterations = record_every_iterations
        self.video_length = video_length
        self.seed = seed
        self.deterministic = deterministic
        self.normalize_action = normalize_action
        # 카메라: 기본 'ceiling' 카메라는 고정 위치라 로봇이 30초 안에 프레임을 벗어난다
        # (2026-09-10 지적). 데모와 같이 매 스텝 CoM을 추적하고 fovy를 넓힌다.
        self.track_com = track_com
        self.cam_fovy = cam_fovy
        self.completed_iterations = 0
        self.recorded_iterations: set[int] = set()

    def _setup_camera(self, base_env):
        """CoM 추적 카메라 준비. 지원하지 않는 env면 None (고정 카메라 유지)."""
        try:
            u = base_env.unwrapped
            cam_id = u.model.camera("ceiling").id
            if self.cam_fovy is not None:
                u.model.cam_fovy[cam_id] = float(self.cam_fovy)
            cam_z = float(u.model.cam_pos[cam_id][2])
            u.get_robot_com()
            return u, cam_id, cam_z
        except Exception:
            return None

    @staticmethod
    def _track(cam):
        if cam is None:
            return
        u, cam_id, cam_z = cam
        com = u.get_robot_com()
        u.model.cam_pos[cam_id][0] = float(com[0])
        u.model.cam_pos[cam_id][1] = float(com[1])
        u.model.cam_pos[cam_id][2] = cam_z

    def _on_step(self) -> bool:
        return True

    def _on_rollout_start(self) -> None:
        self._record_if_scheduled()

    def _on_rollout_end(self) -> None:
        self.completed_iterations += 1

    def _on_training_end(self) -> None:
        self._record_if_scheduled()

    def _record_if_scheduled(self) -> None:
        if not self._should_record(self.completed_iterations):
            return

        self._record_video()
        self.recorded_iterations.add(self.completed_iterations)
        self.logger.record("video/last_recorded_iteration", self.completed_iterations)
        self.logger.record("video/last_recorded_timestep", self.num_timesteps)

    def _should_record(self, iteration: int) -> bool:
        if iteration in self.recorded_iterations:
            return False
        if iteration < self.start_iteration:
            return False
        if iteration == self.start_iteration:
            return True
        if self.record_every_iterations is None:
            return False
        return (
            iteration - self.start_iteration
        ) % self.record_every_iterations == 0

    def _record_video(self) -> None:
        self.video_folder.mkdir(parents=True, exist_ok=True)
        env_kwargs = dict(self.env_kwargs)
        env_kwargs["render_mode"] = "rgb_array"

        base_env = gym.make(self.env_id, **env_kwargs)
        if self.normalize_action:
            base_env = NormalizeAction(base_env)
        name_prefix = (
            f"iteration-{self.completed_iterations:06d}"
            f"-timesteps-{self.num_timesteps:09d}"
        )
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*Overwriting existing videos.*",
            )
            env = RecordVideo(
                base_env,
                video_folder=str(self.video_folder),
                episode_trigger=lambda episode_id: episode_id == 0,
                video_length=self.video_length,
                name_prefix=name_prefix,
                disable_logger=True,
            )

        cam = self._setup_camera(base_env) if self.track_com else None
        try:
            observation, _ = env.reset(seed=self.seed + self.completed_iterations)
            for _ in range(self.video_length):
                self._track(cam)
                policy_observation = observation
                vec_normalize = self.model.get_vec_normalize_env()
                if vec_normalize is not None:
                    policy_observation = vec_normalize.normalize_obs(observation)
                action, _ = self.model.predict(
                    policy_observation,
                    deterministic=self.deterministic,
                )
                observation, _, terminated, truncated, _ = env.step(action)
                if terminated or truncated:
                    observation, _ = env.reset()
        finally:
            env.close()

        if self.verbose:
            print(
                f"Recorded policy video after iteration {self.completed_iterations}: "
                f"{self.video_folder}"
            )
