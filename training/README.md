# RLlib training workspace

This directory holds experiment configuration and documentation for training
`horcrux_env` policies with Ray RLlib. Environment implementation remains in
`horcrux_env/`; generated models, checkpoints, and logs belong in `runs/` and
are not committed.

No Python training entry point is included yet. The YAML files define the
initial project configuration schema that a future runner will translate into
RLlib's `PPOConfig`, `RunConfig`, and checkpoint settings.

## Install training dependencies

```bash
conda activate horcrux
pip install -e ".[train]"
```

The `train` extra installs RLlib, PyTorch, PyYAML, and TensorBoard. RLlib's
official pip extra already includes Ray Core and Ray Tune.

## Layout

```text
training/
├── README.md
├── configs/
│   ├── ppo_plane.yaml
│   └── smoke.yaml
├── callbacks/
│   └── README.md
└── envs/
    └── README.md
```

- `configs/`: reproducible experiment profiles.
- `envs/`: future RLlib environment registration and wrapper composition.
- `callbacks/`: future episode metrics and checkpoint callback definitions.
- `runs/`: generated output at the repository root; ignored by Git.

## Configuration rules

- Keep environment constructor arguments under `environment.kwargs`.
- Keep RLlib algorithm settings under `algorithm`.
- Use the smoke profile before starting a long experiment.
- Record the resolved configuration in every run directory.
- Treat seeds, package versions, and Git revision as required run metadata.

## Planned entry points

When Python code is added, keep the entry points thin:

- `training/train.py`: load YAML, register the environment, build RLlib config,
  start Tune, and save resolved metadata.
- `training/evaluate.py`: restore a checkpoint and run deterministic episodes.

Before using results as a baseline, fix the known environment termination and
seeding issues documented in `PROJECT.md` and identified during environment
review.
