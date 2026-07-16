from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import gymnasium as gym
import yaml

import horcrux_env  # noqa: F401 - registers the Gymnasium environment


DEFAULT_CONFIG = Path(__file__).parent / "configs" / "environment_plane.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Horcrux Gymnasium environment from a YAML configuration."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--render-mode",
        choices=("human", "rgb_array", "depth_array"),
        help="Override render_mode; omit it for headless execution.",
    )
    return parser.parse_args()


def load_environment_config(path: Path) -> tuple[str, dict[str, Any]]:
    resolved_path = path.resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Environment configuration not found: {resolved_path}")

    with resolved_path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError("The configuration root must be a YAML mapping.")
    if config.get("schema_version") != 1:
        raise ValueError("Only environment schema_version 1 is supported.")

    environment = config.get("environment")
    if not isinstance(environment, dict):
        raise ValueError("Missing or invalid 'environment' section.")

    env_id = environment.get("id")
    kwargs = environment.get("kwargs", {})
    if not isinstance(env_id, str) or not env_id:
        raise ValueError("environment.id must be a non-empty string.")
    if not isinstance(kwargs, dict):
        raise ValueError("environment.kwargs must be a YAML mapping.")
    return env_id, kwargs


def main() -> None:
    args = parse_args()
    if args.steps < 1:
        raise ValueError("--steps must be positive.")

    env_id, env_kwargs = load_environment_config(args.config)
    env_kwargs = dict(env_kwargs)
    if args.render_mode is not None:
        env_kwargs["render_mode"] = args.render_mode

    env = gym.make(env_id, **env_kwargs)
    env.action_space.seed(args.seed)

    episode = 1
    episode_return = 0.0
    observation, _ = env.reset(seed=args.seed)
    print(f"Environment: {env_id}")
    print(f"Observation: shape={observation.shape}, dtype={observation.dtype}")
    print(f"Action space: {env.action_space}")

    try:
        for step in range(1, args.steps + 1):
            action = env.action_space.sample()
            observation, reward, terminated, truncated, _ = env.step(action)
            episode_return += float(reward)

            if terminated or truncated:
                print(f"Episode {episode}: return={episode_return:.3f}, end_step={step}")
                episode += 1
                episode_return = 0.0
                observation, _ = env.reset()
    finally:
        env.close()

    print(f"Completed {args.steps} environment steps.")


if __name__ == "__main__":
    main()
