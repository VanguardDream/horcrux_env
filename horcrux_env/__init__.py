from gymnasium.envs.registration import register

register(
    id="horcrux_env/plane-v0",
    entry_point="horcrux_env.envs:PlaneJoyDirWorld",
)
