from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from multiprocessing import freeze_support
from pathlib import Path
from typing import Any

import gymnasium as gym
import torch.nn as nn
import yaml
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import (
    DummyVecEnv,
    SubprocVecEnv,
    VecEnv,
    VecNormalize,
)

import horcrux_env  # noqa: F401 - registers the Gymnasium environment
from horcrux_env.wrappers import NormalizeAction
from callbacks import (
    InfoMetricsCallback,
    SaveVecNormalizeCallback,
    VideoRecorderCallback,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIVATIONS = {
    "elu": nn.ELU,
    "relu": nn.ReLU,
    "tanh": nn.Tanh,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a Horcrux policy with SB3 PPO.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "configs" / "ppo_plane.yaml",
        help="Path to an SB3 experiment YAML file.",
    )
    parser.add_argument("--seed", type=int, help="Override experiment.seed.")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        help="Override algorithm.device.",
    )
    parser.add_argument(
        "--total-timesteps",
        type=int,
        help="Override training.total_timesteps.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Override experiment.output_dir.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    if not path.resolve().is_file():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

    with path.resolve().open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError("The configuration root must be a YAML mapping.")
    if config.get("schema_version") != 2:
        raise ValueError("Only SB3 training schema_version 2 is supported.")
    if config.get("algorithm", {}).get("name") != "PPO":
        raise ValueError("Only the PPO algorithm is currently supported.")

    for section in ("experiment", "environment", "algorithm", "training"):
        if not isinstance(config.get(section), dict):
            raise ValueError(f"Missing or invalid '{section}' configuration section.")

    ppo_kwargs = config["algorithm"].get("kwargs", {})
    n_steps = int(ppo_kwargs.get("n_steps", 2048))
    batch_size = int(ppo_kwargs.get("batch_size", 64))
    sampling = config.get("sampling", {})
    if not isinstance(sampling, dict):
        raise ValueError("The 'sampling' configuration section must be a mapping.")
    num_envs = int(sampling.get("num_envs", 1))
    vec_env = sampling.get("vec_env", "dummy" if num_envs == 1 else "subproc")
    start_method = sampling.get("start_method", "spawn")
    if n_steps < 2 or batch_size < 1:
        raise ValueError("n_steps must be at least 2 and batch_size must be positive.")
    if num_envs < 1:
        raise ValueError("sampling.num_envs must be positive.")
    if vec_env not in {"dummy", "subproc"}:
        raise ValueError("sampling.vec_env must be either 'dummy' or 'subproc'.")
    if start_method not in {"spawn", "forkserver", "fork"}:
        raise ValueError(
            "sampling.start_method must be 'spawn', 'forkserver', or 'fork'."
        )
    rollout_size = n_steps * num_envs
    if rollout_size % batch_size != 0:
        raise ValueError(
            "n_steps * sampling.num_envs must be divisible by batch_size "
            f"(got {n_steps} * {num_envs} = {rollout_size}, batch_size={batch_size})."
        )
    if int(config["training"].get("total_timesteps", 0)) < 1:
        raise ValueError("training.total_timesteps must be positive.")

    normalization = config.get("normalization", {})
    if not isinstance(normalization, dict):
        raise ValueError("The 'normalization' configuration section must be a mapping.")
    if normalization.get("enabled", False):
        if float(normalization.get("clip_obs", 10.0)) <= 0:
            raise ValueError("normalization.clip_obs must be positive.")
        if float(normalization.get("epsilon", 1e-8)) <= 0:
            raise ValueError("normalization.epsilon must be positive.")

    action_normalization = config.get("action_normalization", {})
    if not isinstance(action_normalization, dict):
        raise ValueError(
            "The 'action_normalization' configuration section must be a mapping."
        )
    return config


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    resolved = copy.deepcopy(config)
    if args.seed is not None:
        resolved["experiment"]["seed"] = args.seed
    if args.device is not None:
        resolved["algorithm"]["device"] = args.device
    if args.total_timesteps is not None:
        if args.total_timesteps < 1:
            raise ValueError("--total-timesteps must be positive.")
        resolved["training"]["total_timesteps"] = args.total_timesteps
    if args.output_dir is not None:
        resolved["experiment"]["output_dir"] = str(args.output_dir)
    return resolved


def resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def make_monitored_env(
    env_id: str,
    env_kwargs: dict[str, Any],
    seed: int,
    monitor_path: Path | None = None,
    normalize_action: bool = False,
):
    def factory():
        env = gym.make(env_id, **env_kwargs)
        if normalize_action:
            env = NormalizeAction(env)
        env.reset(seed=seed)
        env.action_space.seed(seed)
        filename = str(monitor_path) if monitor_path is not None else None
        return Monitor(env, filename=filename)

    return factory


def build_training_env(
    config: dict[str, Any],
    run_dir: Path,
    seed: int,
) -> tuple[VecEnv, int]:
    environment = config["environment"]
    sampling = config.get("sampling", {})
    num_envs = int(sampling.get("num_envs", 1))
    vec_env_name = sampling.get("vec_env", "dummy" if num_envs == 1 else "subproc")
    start_method = sampling.get("start_method", "spawn")

    monitor_dir = run_dir / "monitor"
    monitor_dir.mkdir()
    env_fns = [
        make_monitored_env(
            environment["id"],
            environment.get("kwargs", {}),
            seed + rank,
            monitor_dir / f"env_{rank:03d}.monitor.csv",
            action_normalization_enabled(config),
        )
        for rank in range(num_envs)
    ]

    if vec_env_name == "subproc":
        return SubprocVecEnv(env_fns, start_method=start_method), num_envs
    return DummyVecEnv(env_fns), num_envs


def observation_normalization_enabled(config: dict[str, Any]) -> bool:
    return bool(config.get("normalization", {}).get("enabled", False))


def action_normalization_enabled(config: dict[str, Any]) -> bool:
    return bool(config.get("action_normalization", {}).get("enabled", False))


def wrap_with_observation_normalization(
    env: VecEnv,
    config: dict[str, Any],
    *,
    training: bool,
) -> VecEnv:
    if not observation_normalization_enabled(config):
        return env

    normalization = config["normalization"]
    return VecNormalize(
        env,
        training=training,
        norm_obs=True,
        norm_reward=False,
        clip_obs=float(normalization.get("clip_obs", 10.0)),
        epsilon=float(normalization.get("epsilon", 1e-8)),
    )


def save_observation_statistics(env: VecEnv, path: Path) -> None:
    if isinstance(env, VecNormalize):
        env.save(path)


def scale_callback_frequency(frequency: int, num_envs: int) -> int:
    """Convert an environment-timestep frequency to VecEnv callback calls."""
    if frequency < 1:
        raise ValueError("Callback frequency must be positive when enabled.")
    return max(frequency // num_envs, 1)


def git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def create_run_directory(config: dict[str, Any]) -> Path:
    output_dir = resolve_path(config["experiment"]["output_dir"])
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_dir = output_dir / f"{timestamp}_{config['experiment']['name']}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def save_run_metadata(config: dict[str, Any], run_dir: Path) -> None:
    with (run_dir / "resolved_config.yaml").open("w", encoding="utf-8") as output:
        yaml.safe_dump(config, output, sort_keys=False, allow_unicode=True)

    metadata = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_revision(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            name: package_version(name)
            for name in ("horcrux_env", "gymnasium", "mujoco", "stable-baselines3", "torch")
        },
    }
    with (run_dir / "metadata.json").open("w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2, ensure_ascii=False)


def build_policy_kwargs(config: dict[str, Any]) -> dict[str, Any]:
    policy_kwargs = dict(config["algorithm"].get("policy_kwargs", {}))
    activation_name = str(policy_kwargs.pop("activation_fn", "tanh")).lower()
    try:
        policy_kwargs["activation_fn"] = ACTIVATIONS[activation_name]
    except KeyError as error:
        choices = ", ".join(sorted(ACTIVATIONS))
        raise ValueError(f"Unsupported activation_fn '{activation_name}'. Choose: {choices}.") from error
    return policy_kwargs


def main() -> None:
    args = parse_args()
    config = apply_overrides(load_config(args.config), args)
    run_dir = create_run_directory(config)
    save_run_metadata(config, run_dir)

    experiment = config["experiment"]
    environment = config["environment"]
    algorithm = config["algorithm"]
    seed = int(experiment["seed"])

    train_env = None
    eval_env = None
    model = None
    try:
        train_env, num_envs = build_training_env(config, run_dir, seed)
        train_env = wrap_with_observation_normalization(
            train_env,
            config,
            training=True,
        )

        callbacks = [InfoMetricsCallback()]
        checkpointing = config.get("checkpointing", {})
        if checkpointing.get("enabled", False):
            checkpoint_dir = run_dir / "checkpoints"
            checkpoint_dir.mkdir()
            callbacks.append(
                CheckpointCallback(
                    save_freq=scale_callback_frequency(
                        int(checkpointing["save_freq"]), num_envs
                    ),
                    save_path=str(checkpoint_dir),
                    name_prefix="ppo_plane",
                    save_vecnormalize=observation_normalization_enabled(config),
                )
            )

        evaluation = config.get("evaluation", {})
        if evaluation.get("enabled", False):
            evaluation_dir = run_dir / "evaluation"
            evaluation_dir.mkdir()
            eval_env = DummyVecEnv(
                [
                    make_monitored_env(
                        environment["id"],
                        environment.get("kwargs", {}),
                        seed + num_envs,
                        normalize_action=action_normalization_enabled(config),
                    )
                ]
            )
            eval_env = wrap_with_observation_normalization(
                eval_env,
                config,
                training=False,
            )
            callback_on_new_best = None
            if observation_normalization_enabled(config):
                callback_on_new_best = SaveVecNormalizeCallback(
                    evaluation_dir / "best_model_vecnormalize.pkl"
                )
            callbacks.append(
                EvalCallback(
                    eval_env,
                    best_model_save_path=str(evaluation_dir),
                    log_path=str(evaluation_dir),
                    eval_freq=scale_callback_frequency(
                        int(evaluation["eval_freq"]), num_envs
                    ),
                    n_eval_episodes=int(evaluation["n_eval_episodes"]),
                    deterministic=bool(evaluation.get("deterministic", True)),
                    callback_on_new_best=callback_on_new_best,
                )
            )

        video = config.get("video", {})
        if video.get("enabled", False):
            callbacks.append(
                VideoRecorderCallback(
                    env_id=environment["id"],
                    env_kwargs=environment.get("kwargs", {}),
                    video_folder=run_dir / "videos",
                    start_iteration=int(video["start_iteration"]),
                    record_every_iterations=video.get("record_every_iterations"),
                    video_length=int(video["video_length"]),
                    seed=seed + num_envs + 1,
                    deterministic=bool(video.get("deterministic", True)),
                    normalize_action=action_normalization_enabled(config),
                )
            )

        model = PPO(
            algorithm.get("policy", "MlpPolicy"),
            train_env,
            seed=seed,
            device=algorithm.get("device", "auto"),
            policy_kwargs=build_policy_kwargs(config),
            tensorboard_log=str(run_dir / "tensorboard"),
            verbose=1,
            **algorithm.get("kwargs", {}),
        )

        print(f"Configuration: {args.config.resolve()}")
        print(f"Run directory: {run_dir}")
        print(f"Training device: {model.device}")
        print(f"Vectorized environments: {num_envs} ({type(train_env).__name__})")
        print(
            "Samples per PPO iteration: "
            f"{algorithm.get('kwargs', {}).get('n_steps', 2048)} * {num_envs} = "
            f"{algorithm.get('kwargs', {}).get('n_steps', 2048) * num_envs}"
        )
        print(
            "Observation normalization: "
            f"{'enabled' if observation_normalization_enabled(config) else 'disabled'}"
        )
        print(
            "Action normalization: "
            f"{'enabled' if action_normalization_enabled(config) else 'disabled'}"
        )
        model.learn(
            total_timesteps=int(config["training"]["total_timesteps"]),
            callback=CallbackList(callbacks),
            tb_log_name=experiment["name"],
        )
        model.save(run_dir / "final_model")
        save_observation_statistics(train_env, run_dir / "vecnormalize.pkl")
        print(f"Training complete: {run_dir / 'final_model.zip'}")
    except KeyboardInterrupt:
        if model is not None:
            model.save(run_dir / "interrupted_model")
            if train_env is not None:
                save_observation_statistics(train_env, run_dir / "vecnormalize.pkl")
            print(f"Training interrupted; model saved: {run_dir / 'interrupted_model.zip'}")
    finally:
        if train_env is not None:
            train_env.close()
        if eval_env is not None:
            eval_env.close()


if __name__ == "__main__":
    freeze_support()
    main()
