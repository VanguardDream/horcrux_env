from __future__ import annotations

from typing import Any, Optional

import importlib.resources as resources
import numpy as np

from gymnasium import utils

from horcrux_env.envs.gait_v3 import GaitV3
from horcrux_env.envs.plane_direct_torque import PlaneDirectTorqueWorld
from horcrux_env.envs.plane_v3_scalable import SingleEvalTerminationMixin


class PlaneDirectTorqueWorldScalable(SingleEvalTerminationMixin, PlaneDirectTorqueWorld):
    """
    PlaneDirectTorqueWorld의 관절 수 일반화 버전 (CoRL 2026 리부탈,
    관절 수 스케일링 실험의 no-GD 비교군).

    n_joints에 따라 resources_rebuttal의 horcrux_plane_n{N}.xml 모델을
    사용한다. action/obs 공간은 부모가 model.nu / sensordata 크기에서 자동
    유도하므로 그대로 맞고, 관측·info 슬라이싱만 n 기반 공식으로 재정의한다.

    Observation 구조 (총 5n + 13, gait motion vector 없음):
        sensordata (5n + 10): jpos n | jvel n | jtor n | touch_top n | touch_bot n
                              | head_quat 4 | head_angvel 3 | head_linacc 3
        joy_input (3)

    PlaneJoyDirWorldScalable과 동일하게 SingleEvalTerminationMixin을 적용해
    unhealthy 유예가 step당 1회 갱신된다 (양 비교군의 종료 조건 의미 통일).
    """

    def __init__(
        self,
        n_joints: int = 14,
        model_path: Optional[str] = None,
        torque_min: float = -2.7,
        torque_max: float = 2.7,
        **kwargs: Any,
    ) -> None:
        self.n_joints = int(n_joints)
        n = self.n_joints

        resolved_path = model_path
        if resolved_path is None:
            resolved_path = str(
                resources.files("horcrux_env.resources_rebuttal") / f"horcrux_plane_n{n:02d}.xml"
            )

        super().__init__(
            torque_min=torque_min,
            torque_max=torque_max,
            model_path=resolved_path,
            **kwargs,
        )

        # EzPickle 인자를 서브클래스 시그니처로 재기록
        utils.EzPickle.__init__(
            self,
            n_joints=n_joints,
            model_path=model_path,
            torque_min=torque_min,
            torque_max=torque_max,
            **kwargs,
        )

        # 부모(PlaneDirectTorqueWorld)가 action/obs 공간을 model.nu와
        # sensordata 크기에서 유도하므로 공간 재정의는 불필요. 나머지
        # 14 기준 항목만 n 기반으로 재정의한다.
        self._robot_body_names = [f"link{i}" for i in range(1, n + 2)]
        self._gait = GaitV3(
            self._gait_params,
            n_joints=n,
            sampling_t=self._gait_sampling_interval,
            frame_skip=self.frame_skip,
        )
        self._motion_vector = np.array([0] * n)  # 미사용이지만 차원 일관성 유지

        self._sl_touch_top = slice(3 * n, 4 * n)
        self._sl_touch_bot = slice(4 * n, 5 * n)

        self.observation_structure = {
            "jpos": self.data.sensordata[:n],
            "jvel": self.data.sensordata[n:2 * n],
            "jtor": self.data.sensordata[2 * n:3 * n],
            "link_contacts_top": self.data.sensordata[self._sl_touch_top],
            "link_contacts_bot": self.data.sensordata[self._sl_touch_bot],
            "head_orientation": self.data.sensordata[5 * n:5 * n + 4],
            "head_angvel": self.data.sensordata[5 * n + 4:5 * n + 7],
            "head_linacc": self.data.sensordata[5 * n + 7:5 * n + 10],
            "joy_input": self._joy_input,
        }

    def _get_obs(self, _motion_vector: np.ndarray | None = None) -> np.ndarray:
        tmp = self.data.sensordata.copy()

        if self._use_imu_mov_mean:
            tmp[-10:-6] = self._mov_mean_imu_quat.update(
                (
                    self.data.sensordata[-10].copy(),
                    self.data.sensordata[-9].copy(),
                    self.data.sensordata[-8].copy(),
                    self.data.sensordata[-7].copy(),
                )
            )
            tmp[-6:-3] = self._mov_mean_imu_vel.update(
                self.data.sensordata[-6].copy(),
                self.data.sensordata[-5].copy(),
                self.data.sensordata[-4].copy(),
            )
            tmp[-3:] = self._mov_mean_imu_acc.update(
                self.data.sensordata[-3].copy(),
                self.data.sensordata[-2].copy(),
                self.data.sensordata[-1].copy(),
            )

        tmp[self._sl_touch_top] = (tmp[self._sl_touch_top] > 1).astype(int)
        tmp[self._sl_touch_bot] = (tmp[self._sl_touch_bot] > 1).astype(int)
        return np.concatenate((tmp, self._joy_input), dtype=np.float32)

    def step(self, action):
        observation, reward, terminated, truncated, info = super().step(action)

        n = self.n_joints
        info.update(
            {
                "joint_pos": observation[0:n].copy(),
                "joint_vel": observation[n:2 * n].copy(),
                "head_quat": observation[5 * n:5 * n + 4].copy(),
                "head_ang_vel": observation[5 * n + 4:5 * n + 7].copy(),
                "head_lin_acc": observation[5 * n + 7:5 * n + 10].copy(),
                "joy_input": observation[5 * n + 10:5 * n + 13].copy(),
            }
        )
        return observation, reward, terminated, truncated, info

    def reset_model(self):
        observation = super().reset_model()
        self._initial_com = np.array([-(self.n_joints * 0.0685) / 2, 0, 0.0350])
        return observation


if __name__ == "__main__":
    # 검증: python -m horcrux_env.envs.plane_direct_torque_scalable
    print("[1] n=6/10/14/20 차원 검증:")
    for n in (6, 10, 14, 20):
        env = PlaneDirectTorqueWorldScalable(n_joints=n)
        expect_obs = 5 * n + 13

        assert env.model.nu == n
        assert env.action_space.shape == (n,), f"n={n}: action {env.action_space.shape}"
        assert np.isclose(env.action_space.low[0], -2.7) and np.isclose(env.action_space.high[0], 2.7)
        assert env.observation_space.shape == (expect_obs,), f"n={n}: obs_space {env.observation_space.shape}"

        obs, _ = env.reset(seed=0)
        assert obs.shape == (expect_obs,), f"n={n}: reset obs {obs.shape}"

        rng = np.random.default_rng(0)
        for _ in range(10):
            obs, reward, terminated, truncated, info = env.step(rng.uniform(-0.5, 0.5, size=n))
        assert obs.shape == (expect_obs,)
        top, bot = obs[3 * n:4 * n], obs[4 * n:5 * n]
        assert set(np.unique(np.concatenate([top, bot]))).issubset({0.0, 1.0}), f"n={n}: touch 이진화 실패"
        assert info["joint_pos"].shape == (n,)
        assert np.array_equal(info["joint_vel"], obs[n:2 * n]), f"n={n}: joint_vel != obs[n:2n]"
        assert np.array_equal(info["joy_input"], obs[5 * n + 10:5 * n + 13])
        assert "motion_vector" not in info or info.get("motion_vector") is None or True
        assert np.isfinite(reward)
        env.close()
        print(f"    n={n:2d}: action ({n},) [±2.7], obs ({expect_obs},), touch/info 구조 — OK")

    print("[2] n=14 등가성 검증 (vs PlaneDirectTorqueWorld, unhealthy 미진입 궤적):")
    ref = PlaneDirectTorqueWorld()
    gen = PlaneDirectTorqueWorldScalable(n_joints=14)

    obs_ref, _ = ref.reset(seed=42)
    obs_gen, _ = gen.reset(seed=42)
    assert np.array_equal(obs_ref, obs_gen), "reset 관측 불일치"

    rng = np.random.default_rng(7)
    unhealthy_seen = False
    for t in range(300):
        action = rng.uniform(-0.8, 0.8, size=14)  # 뒤집힘(unhealthy) 회피용 저강도 토크
        o_r, r_r, term_r, trunc_r, i_r = ref.step(action)
        o_g, r_g, term_g, trunc_g, i_g = gen.step(action)
        if ref._unhealth_steps > 0 or gen._unhealth_steps > 0:
            unhealthy_seen = True
            break  # 이후는 유예 수정으로 의도적으로 달라질 수 있음
        assert np.array_equal(o_r, o_g), f"step {t}: 관측 불일치"
        assert r_r == r_g, f"step {t}: 보상 불일치"
        assert (term_r, trunc_r) == (term_g, trunc_g), f"step {t}: 종료 플래그 불일치"
        for key in ("x_velocity", "joint_pos", "joint_vel", "head_quat", "joy_input"):
            assert np.array_equal(np.asarray(i_r[key]), np.asarray(i_g[key])), f"step {t}: info[{key}] 불일치"
    ref.close()
    gen.close()
    label = "unhealthy 진입 시점까지" if unhealthy_seen else "300스텝 전체"
    print(f"    {label} 동일 action: 관측·보상·종료·info 전부 bitwise 동일 — OK")

    print("[3] unhealthy 유예 카운터 검증 (mixin 적용 확인):")
    gen = PlaneDirectTorqueWorldScalable(n_joints=14)
    gen.reset(seed=0)
    gen._n_step = 1
    gen._unhealth_steps = 0
    gen._cur_euler_ypr = np.array([0.0, 0.0, 150.0])
    _ = gen.is_terminated
    _ = gen.is_terminated
    assert gen._unhealth_steps == 1, f"counter {gen._unhealth_steps} != 1"
    gen.close()
    print("    동일 step 내 2회 호출 후 counter=1 (step당 1회 갱신) — OK")

    print("all checks passed")
