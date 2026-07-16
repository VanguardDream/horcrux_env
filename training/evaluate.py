from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import gymnasium as gym
import yaml
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

import horcrux_env  # noqa: F401 - registers the Gymnasium environment
from horcrux_env.wrappers import NormalizeAction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an SB3 Horcrux PPO policy.")
    parser.add_argument("model", type=Path, help="Path to an SB3 PPO .zip model.")
    parser.add_argument("--config", type=Path, help="Experiment YAML; auto-detected by default.")
    parser.add_argument(
        "--vecnormalize",
        type=Path,
        help="VecNormalize .pkl file; inferred from the model path by default.",
    )
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--render", action="store_true", help="Render with MuJoCo's human viewer.")
    return parser.parse_args()


def find_config(model_path: Path) -> Path:
    for directory in (model_path.resolve().parent, *model_path.resolve().parents):
        candidate = directory / "resolved_config.yaml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find resolved_config.yaml above the model. Pass --config explicitly."
    )


def load_config(path: Path) -> dict[str, Any]:
    with path.resolve().open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if config.get("schema_version") != 2:
        raise ValueError("Only SB3 training schema_version 2 is supported.")
    return config


def find_vecnormalize(model_path: Path) -> Path:
    model_path = model_path.resolve()
    if model_path.stem == "best_model":
        candidate = model_path.parent / "best_model_vecnormalize.pkl"
    else:
        checkpoint_match = re.fullmatch(r"(.+)_(\d+)_steps", model_path.stem)
        if checkpoint_match:
            prefix, steps = checkpoint_match.groups()
            candidate = model_path.parent / f"{prefix}_vecnormalize_{steps}_steps.pkl"
        else:
            candidate = model_path.parent / "vecnormalize.pkl"

    if candidate.is_file():
        return candidate
    raise FileNotFoundError(
        f"Could not find VecNormalize statistics for {model_path}. "
        "Pass --vecnormalize explicitly."
    )


def main() -> None:
    args = parse_args()
    if args.episodes < 1:
        raise ValueError("--episodes must be at least 1.")

    config_path = args.config or find_config(args.model)
    config = load_config(config_path)
    environment = config["environment"]
    env_kwargs = dict(environment.get("kwargs", {}))
    if args.render:
        env_kwargs["render_mode"] = "human"

    def make_evaluation_env():
        env = gym.make(environment["id"], **env_kwargs)
        if config.get("action_normalization", {}).get("enabled", False):
            env = NormalizeAction(env)
        return Monitor(env)

    vec_env = DummyVecEnv([make_evaluation_env])
    normalization_enabled = bool(config.get("normalization", {}).get("enabled", False))
    vecnormalize_path = None
    if normalization_enabled:
        vecnormalize_path = args.vecnormalize or find_vecnormalize(args.model)
        env = VecNormalize.load(vecnormalize_path, vec_env)
        env.training = False
        env.norm_reward = False
    else:
        env = vec_env

    model = PPO.load(args.model, env=env, device=config["algorithm"].get("device", "auto"))
    deterministic = bool(config.get("evaluation", {}).get("deterministic", True))
    base_seed = int(config["experiment"]["seed"])

    returns: list[float] = []
    try:
        for episode in range(args.episodes):
            env.seed(base_seed + episode)
            observation = env.reset()
            episode_return = 0.0
            episode_length = 0
            done = False

            while not done:
                action, _ = model.predict(observation, deterministic=deterministic)
                observation, reward, dones, _ = env.step(action)
                episode_return += float(reward[0])
                episode_length += 1
                done = bool(dones[0])

            returns.append(episode_return)
            print(
                f"Episode {episode + 1}: return={episode_return:.3f}, "
                f"length={episode_length}"
            )
    finally:
        env.close()

    mean_return = sum(returns) / len(returns)
    if vecnormalize_path is not None:
        print(f"Observation statistics: {Path(vecnormalize_path).resolve()}")
    print(f"Mean return over {len(returns)} episodes: {mean_return:.3f}")


if __name__ == "__main__":
    main()
