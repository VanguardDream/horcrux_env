# SB3 callbacks

`InfoMetricsCallback` records selected scalar values already exposed through
the environment's `info` dictionary. Metrics include velocity, direction and
rotation alignment, reward components, control cost, orientation cost, and
health cost.

Callbacks in this directory must remain training-only and must not change the
environment reward or dynamics. Reusable Gymnasium wrappers belong in
`horcrux_env/wrappers/`.

## Policy video recording

`VideoRecorderCallback` runs the current policy in a separate evaluation
environment after selected PPO rollout-and-update iterations. This prevents
video capture from changing the state of the training environment.

Configure it in an experiment YAML:

```yaml
video:
  enabled: true
  start_iteration: 10
  record_every_iterations: 10
  video_length: 100
  deterministic: true
```

This records at iterations 10, 20, 30, and so on. Set
`record_every_iterations: null` to record only once at `start_iteration`.
Videos are saved under the run's `videos/` directory. One PPO iteration
corresponds to `algorithm.kwargs.n_steps * sampling.num_envs` environment
steps.

Observation normalization is kept consistent across callbacks. Checkpoints save
their matching `VecNormalize` statistics, the best-model callback stores
`best_model_vecnormalize.pkl`, and video inference normalizes observations with
the current training statistics.

When action normalization is enabled, the video environment also uses
`NormalizeAction`, ensuring recorded policy actions have the same `[-1, 1]` to
physical-range mapping as training.
