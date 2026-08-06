from gymnasium.envs.registration import register

register(
    id="horcrux_env/plane-v0",
    entry_point="horcrux_env.envs:PlaneJoyDirWorld",
)

register(
    id="horcrux_env/plane-direct-torque-v0",
    entry_point="horcrux_env.envs:PlaneDirectTorqueWorld",
)

# CoRL 2026 리부탈: 관절 수 스케일링 실험용 (env_kwargs로 n_joints 지정)
register(
    id="horcrux_env/plane-scalable-v0",
    entry_point="horcrux_env.envs.plane_v3_scalable:PlaneJoyDirWorldScalable",
)

register(
    id="horcrux_env/plane-direct-torque-scalable-v0",
    entry_point="horcrux_env.envs.plane_direct_torque_scalable:PlaneDirectTorqueWorldScalable",
)
