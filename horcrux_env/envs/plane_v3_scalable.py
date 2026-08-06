from typing import Optional

import importlib.resources as resources
import numpy as np

from gymnasium import utils
from gymnasium.spaces import Box

from horcrux_env.envs.gait_v3 import GaitV3
from horcrux_env.envs.plane_v3 import PlaneJoyDirWorld


class SingleEvalTerminationMixin:
    """unhealthy 유예 카운터를 step당 정확히 1회만 갱신하는 mixin.

    원본 plane_v3.py의 is_terminated는 호출마다 카운터를 증가시키는
    property인데, step()당 두 번 호출된다(_get_rew의 unhealthy_cost 계산과
    종료 판정). 그 결과 카운터가 step당 2씩 증가해 실효 유예가
    unhealthy_max_steps의 절반이 된다(예: 30 설정 -> 실제 15 step = 0.75 s).
    이 mixin은 같은 step 내 반복 호출 시 캐시를 반환해, 설정값이 곧
    "unhealthy 상태로 버틸 수 있는 env step 수"가 되도록 의미를 바로잡는다.
    판정 조건 자체(terminating_roll_range 이탈)는 원본과 동일하다.
    """

    @property
    def is_terminated(self):
        if getattr(self, "_unhealth_eval_step", None) != self._n_step:
            self._unhealth_eval_step = self._n_step
            y, p, r = self._cur_euler_ypr
            t_min_r, t_max_r = self._terminating_roll_range
            if t_min_r <= r <= t_max_r:
                self._unhealth_steps = 0
            else:
                self._unhealth_steps += 1
            self._is_terminated_cached = self._unhealth_steps >= self._unhealthy_max_steps
        return self._is_terminated_cached


class PlaneJoyDirWorldScalable(SingleEvalTerminationMixin, PlaneJoyDirWorld):
    """
    PlaneJoyDirWorld의 관절 수 일반화 버전 (CoRL 2026 리부탈, 관절 수 스케일링 실험).

    n_joints에 따라 resources_rebuttal의 horcrux_plane_n{N}.xml 모델과 GaitV3를
    사용하며, action/observation 공간과 모든 관측 슬라이싱을 n 기반 공식으로
    재정의한다. n_joints=14이면 기존 PlaneJoyDirWorld와 관측·보상이 동일하다
    (아래 __main__ 검증으로 보장).

    Observation 구조 (총 6n + 13):
        sensordata (5n + 10): jpos n | jvel n | jtor n | touch_top n | touch_bot n
                              | head_quat 4 | head_angvel 3 | head_linacc 3
        motion_vector (n) | joy_input (3)

    원본과의 의도된 차이 (아직 학습에 사용된 적 없는 신규 env이므로 원본의
    버그를 계승하지 않는다):
      1. info["joint_vel"]: 원본 슬라이스(-41:-27)는 실제로 touch_bot 구간을
         가리키는 버그. 실제 관절 속도 observation[n:2n]을 보고하도록 수정.
      2. unhealthy 유예: 원본은 is_terminated property가 step당 2회 호출되어
         실효 유예가 unhealthy_max_steps의 절반. SingleEvalTerminationMixin으로
         step당 1회 갱신으로 수정 (설정값 = 실제 유예 step 수).
    따라서 n=14 등가성은 위 두 항목을 제외한 모든 관측·보상·info에 대해
    성립한다 (unhealthy 상태에 진입하지 않는 궤적에서는 2번도 완전 동일).
    """

    def __init__(self, n_joints: int = 14, model_path: Optional[str] = None, **kwargs):
        self.n_joints = int(n_joints)
        n = self.n_joints

        resolved_path = model_path
        if resolved_path is None:
            resolved_path = str(
                resources.files("horcrux_env.resources_rebuttal") / f"horcrux_plane_n{n:02d}.xml"
            )

        super().__init__(model_path=resolved_path, **kwargs)

        # EzPickle 인자를 서브클래스 시그니처로 재기록 (복원 시 이 클래스로 재생성)
        utils.EzPickle.__init__(self, n_joints=n_joints, model_path=model_path, **kwargs)

        # ---- 부모가 14 기준으로 설정한 항목들을 n 기반으로 재정의 ----
        self._robot_body_names = [f"link{i}" for i in range(1, n + 2)]
        self._gait = GaitV3(
            self._gait_params,
            n_joints=n,
            sampling_t=self._gait_sampling_interval,
            frame_skip=self.frame_skip,
        )

        obs_size = self.data.sensordata.size + n + 3  # sensordata + motion vector + joy
        self.observation_space = Box(low=-np.inf, high=np.inf, shape=(obs_size,))
        self.action_space = Box(low=0, high=2.7, shape=(n,))
        self._motion_vector = np.array([0] * n)

        # 관측/info 슬라이스의 n 기반 공식화 (n=14일 때 plane_v3.py의 리터럴과 일치)
        self._sl_touch_top = slice(3 * n, 4 * n)         # 42:56
        self._sl_touch_bot = slice(4 * n, 5 * n)         # 56:70
        self._sl_info_jpos = slice(0, n)                 # :14
        self._sl_info_jvel = slice(n, 2 * n)             # 실제 관절 속도 (원본 버그 -41:-27 미계승)
        self._sl_quat = slice(-(n + 13), -(n + 9))       # -27:-23
        self._sl_gyro = slice(-(n + 9), -(n + 6))        # -23:-20
        self._sl_acc = slice(-(n + 6), -(n + 3))         # -20:-17
        self._sl_mvec = slice(-(n + 3), -3)              # -17:-3

        self.observation_structure = {
            "jpos": self.data.sensordata[:n],
            "jvel": self.data.sensordata[n:2 * n],
            "jtor": self.data.sensordata[2 * n:3 * n],
            "link_contacts_top": self.data.sensordata[self._sl_touch_top],
            "link_contacts_bot": self.data.sensordata[self._sl_touch_bot],
            "head_orientation": self.data.sensordata[5 * n:5 * n + 4],
            "head_angvel": self.data.sensordata[5 * n + 4:5 * n + 7],
            "head_linacc": self.data.sensordata[5 * n + 7:5 * n + 10],
            "motion_vector": self._motion_vector,
            "joy_input": self._joy_input,
        }

    def _get_obs(self, mVec: np.ndarray):
        tmp = self.data.sensordata.copy()

        if self._use_imu_mov_mean:
            tmp[-10:-6] = self._mov_mean_imu_quat.update((self.data.sensordata[-10].copy(), self.data.sensordata[-9].copy(), self.data.sensordata[-8].copy(), self.data.sensordata[-7].copy()))
            tmp[-6:-3] = self._mov_mean_imu_vel.update(self.data.sensordata[-6].copy(), self.data.sensordata[-5].copy(), self.data.sensordata[-4].copy())
            tmp[-3::] = self._mov_mean_imu_acc.update(self.data.sensordata[-3].copy(), self.data.sensordata[-2].copy(), self.data.sensordata[-1].copy())

        tmp[self._sl_touch_top] = (tmp[self._sl_touch_top] > 1).astype(int)
        tmp[self._sl_touch_bot] = (tmp[self._sl_touch_bot] > 1).astype(int)
        return np.concatenate((tmp.flatten(), mVec, self._joy_input), dtype=np.float32)

    def _get_gait_info(self, observation: np.ndarray) -> dict:
        return {
            "motion_vector": observation[self._sl_mvec].copy(),
            "gait_params": self._gait_params,
            "motionMatrix": self._gait.getMotionMat().copy(),
        }

    def step(self, action):
        # 물리/보상/게이트 로직은 부모와 동일. 부모 step이 14 기준 리터럴
        # 슬라이스로 채운 info 항목들만 n 기반 슬라이스로 덮어쓴다.
        observation, reward, terminated, truncated, info = super().step(action)

        info.update({
            "joint_pos": observation[self._sl_info_jpos].copy(),
            "joint_vel": observation[self._sl_info_jvel].copy(),
            "head_quat": observation[self._sl_quat].copy(),
            "head_ang_vel": observation[self._sl_gyro].copy(),
            "head_lin_acc": observation[self._sl_acc].copy(),
        })
        return observation, reward, terminated, truncated, info

    def reset_model(self):
        observation = super().reset_model()
        # 부모의 -0.4795는 14관절(15링크) 체인 중심. n 기반으로 일반화한다.
        self._initial_com = np.array([-(self.n_joints * 0.0685) / 2, 0, 0.0350])
        return observation


if __name__ == "__main__":
    # 검증: python -m horcrux_env.envs.plane_v3_scalable
    np.set_printoptions(linewidth=200)

    print("[1] n=6/10/14/20 차원 검증:")
    for n in (6, 10, 14, 20):
        env = PlaneJoyDirWorldScalable(n_joints=n)
        expect_obs = 6 * n + 13

        assert env.model.nu == n, f"n={n}: nu {env.model.nu}"
        assert env.model.body(2).name == "link1", f"n={n}: main_body(2) != link1"
        assert env.action_space.shape == (n,), f"n={n}: action {env.action_space.shape}"
        assert env.observation_space.shape == (expect_obs,), f"n={n}: obs_space {env.observation_space.shape}"

        obs, _ = env.reset(seed=0)
        assert obs.shape == (expect_obs,), f"n={n}: reset obs {obs.shape}"

        rng = np.random.default_rng(0)
        for _ in range(10):
            action = rng.uniform(0, 2.7, size=n)
            obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == (expect_obs,), f"n={n}: step obs {obs.shape}"

        mvec = obs[-(n + 3):-3]
        assert set(np.unique(mvec)).issubset({-1.0, 0.0, 1.0}), f"n={n}: motion vector 값 이상"
        assert np.array_equal(mvec, env._gait.getMvec(env._k)), f"n={n}: motion vector 불일치"
        top, bot = obs[3 * n:4 * n], obs[4 * n:5 * n]
        assert set(np.unique(np.concatenate([top, bot]))).issubset({0.0, 1.0}), f"n={n}: touch 이진화 실패"
        assert info["joint_pos"].shape == (n,) and info["motion_vector"].shape == (n,)
        assert np.array_equal(info["joint_vel"], obs[n:2 * n]), f"n={n}: joint_vel != obs[n:2n]"
        assert np.isfinite(reward)
        env.close()
        print(f"    n={n:2d}: action ({n},), obs ({expect_obs},), mvec/touch/info 구조 — OK")

    print("[2] n=14 등가성 검증 (vs PlaneJoyDirWorld):")
    ref = PlaneJoyDirWorld()
    gen = PlaneJoyDirWorldScalable(n_joints=14)

    obs_ref, _ = ref.reset(seed=42)
    obs_gen, _ = gen.reset(seed=42)
    assert np.array_equal(obs_ref, obs_gen), "reset 관측 불일치"

    rng = np.random.default_rng(7)
    max_rew_diff = 0.0
    for t in range(300):
        action = rng.uniform(0, 2.7, size=14)
        o_r, r_r, term_r, trunc_r, i_r = ref.step(action)
        o_g, r_g, term_g, trunc_g, i_g = gen.step(action)
        assert np.array_equal(o_r, o_g), f"step {t}: 관측 불일치"
        assert r_r == r_g, f"step {t}: 보상 불일치 {r_r} vs {r_g}"
        assert (term_r, trunc_r) == (term_g, trunc_g), f"step {t}: 종료 플래그 불일치"
        for key in ("x_velocity", "y_velocity", "yaw_velocity", "reward_linear_movement",
                    "cost_orientation", "joint_pos", "head_quat", "motion_vector"):
            v_r, v_g = i_r[key], i_g[key]
            assert np.array_equal(np.asarray(v_r), np.asarray(v_g)), f"step {t}: info[{key}] 불일치"
        # 의도된 차이: joint_vel은 원본 버그(-41:-27 = touch_bot 구간)를 계승하지
        # 않고 실제 관절 속도 observation[n:2n]을 보고해야 한다
        assert np.array_equal(i_g["joint_vel"], o_g[14:28]), f"step {t}: joint_vel != 실제 관절 속도"
        assert np.array_equal(np.asarray(i_r["joint_vel"]), o_r[56:70]), f"step {t}: 원본 동작 가정 변화 감지"
        max_rew_diff = max(max_rew_diff, abs(r_r - r_g))
    ref.close()
    gen.close()
    print(f"    300스텝 동일 action: 관측·보상·종료·info 전부 bitwise 동일 (max reward diff = {max_rew_diff}) — OK")
    print("    joint_vel 수정 확인: 실제 관절 속도 obs[n:2n] 보고, 원본 버그 미계승 — OK")

    print("[3] unhealthy 유예 카운터 검증 (step당 1회 갱신):")
    ref = PlaneJoyDirWorld()
    gen = PlaneJoyDirWorldScalable(n_joints=14)
    ref.reset(seed=0)
    gen.reset(seed=0)
    for env, expect, label in ((ref, 2, "원본(버그: 2/step)"), (gen, 1, "scalable(수정: 1/step)")):
        env._n_step = 1
        env._unhealth_steps = 0
        env._cur_euler_ypr = np.array([0.0, 0.0, 150.0])  # roll 150도: terminating_roll_range(±120) 이탈
        _ = env.is_terminated  # _get_rew에서의 호출에 해당
        _ = env.is_terminated  # step()의 종료 판정 호출에 해당
        assert env._unhealth_steps == expect, f"{label}: counter {env._unhealth_steps} != {expect}"
        print(f"    {label}: 동일 step 내 2회 호출 후 counter={env._unhealth_steps} — OK")
    ref.close()
    gen.close()

    print("all checks passed")
