# Environment integration point

SB3 consumes the registered Gymnasium environment directly through
`gymnasium.make("horcrux_env/plane-v0", **kwargs)`. `training/train.py` wraps
each environment with SB3's `Monitor`. It uses `DummyVecEnv` for sequential
execution and `SubprocVecEnv` for process-based parallel execution.

When `action_normalization.enabled` is true, the reusable
`horcrux_env.wrappers.NormalizeAction` wrapper is applied before `Monitor`.
The base environment keeps its physical `[0, 2.7]` action space while SB3 sees
a symmetric `[-1, 1]` space. The same wrapper is used for training, evaluation,
and video recording.

Each environment receives `experiment.seed + rank`, and Monitor output is
written to a separate `monitor/env_NNN.monitor.csv` file. On Windows, use the
`spawn` start method. Callback frequencies expressed in environment timesteps
are divided by the number of vectorized environments inside the trainer.

Future training-only wrapper composition can live in this directory. Reusable
Gymnasium wrappers belong in `horcrux_env/wrappers/`; environment
implementations must not be duplicated here.
