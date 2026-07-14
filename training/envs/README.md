# Environment integration point

Future RLlib environment registration and wrapper composition should live here.
This layer should translate RLlib `env_config` values into
`gymnasium.make("horcrux_env/plane-v0", **kwargs)` without duplicating any
environment implementation.

Keep training-only wrappers here; reusable Gymnasium wrappers belong in
`horcrux_env/wrappers/`.
