"""인계 시작(moving-state initialization) 환경 — 전문가 이어 학습용.

plane-v0(PlaneJoyDirWorld)의 보상·종료·관측·행동은 그대로 두고, 에피소드 시작 상태만
두 분포를 섞는다:
  - 정지 시작 (확률 1 - moving_init_prob): 부모와 동일 (초기 자세, k=0)
  - 인계 시작 (확률 moving_init_prob): 이동 상태 은행(bank)에서 다른 gait로 움직이던 몸
    상태(qpos, qvel)를 복원하고, 이 전문가의 gait로 전환한 순간에서 시작한다.
    전환 위상은 align_prob 확률로 위상 정렬(현재 motion vector와 부호 유사도 최대 열,
    역재생 gait는 k=-col), 나머지는 무작위 위상 — 부호 가족 간 전환처럼 정렬이 힘을
    못 쓰는 경우까지 강건하도록.
  인계 시작 에피소드는 moving_episode_horizon 스텝에서 절단한다 (전환 직후 구간이
  학습 신호의 핵심이라 긴 에피소드로 희석되지 않게). 정지 시작은 부모의 6000 유지.

은행 파일(npz): qpos (N,21) qvel (N,20) mvec (N,14) source (N,) kind (N,)
  (training/build_moving_state_bank.py가 생성; xy는 원점으로 평행이동돼 있음)

전문가 설정은 IMU/속도 이동평균이 꺼져 있어 관측이 무기억이므로 상태 복원만으로 정합이
맞는다. info: moving_init, source_cmd, init_aligned.

iteration 3 (2026-09-11) 추가 보상 항 — 인계 시작 에피소드에만 적용, 기본 가중치 0(기존 설정 불변):
  cost_tilt       기울기 벌점. |roll|이 tilt_deadzone_deg(15°)까지는 0, tilt_ref_deg(45°, 불건강 기준)에서
                  -tilt_cost_weight/스텝, 그 사이는 비례, 최대 2배(75° 이상)로 캡.
  cost_push_tilt  기운 채로 세게 밀기 벌점. -push_tilt_cost_weight × (기울기 비율, 0~1) × (평균 진폭/최대 진폭).
  둘 다 정책 관측(IMU 자세)에서 보이는 상태 조건이라 시간 조건 없이 정의된다. 정지 시작 에피소드는 기존 보상 그대로.
"""
from typing import Optional, Sequence

import numpy as np

from horcrux_env.envs.phase_align import RULES, start_k
from horcrux_env.envs.plane_v3 import PlaneJoyDirWorld


class PlaneMovingInitWorld(PlaneJoyDirWorld):
    def __init__(
        self,
        bank_path: Optional[str] = None,
        moving_init_prob: float = 0.5,
        align_prob: float = 0.8,
        moving_episode_horizon: Optional[int] = 1000,
        source_weights: Optional[Sequence[float]] = None,
        tilt_cost_weight: float = 0.0,
        push_tilt_cost_weight: float = 0.0,
        tilt_deadzone_deg: float = 15.0,
        tilt_ref_deg: float = 45.0,
        align_rule: str = "sign",
        **kwargs,
    ) -> None:
        if align_rule not in RULES:
            raise ValueError(f"align_rule must be one of {RULES}, got {align_rule!r}")
        self._align_rule = str(align_rule)
        self._tilt_w = float(tilt_cost_weight)
        self._push_w = float(push_tilt_cost_weight)
        self._tilt_dead = float(tilt_deadzone_deg)
        self._tilt_ref = float(tilt_ref_deg)
        self._amp_max = None
        self._bank_path = bank_path
        self._moving_init_prob = float(moving_init_prob)
        self._align_prob = float(align_prob)
        self._moving_episode_horizon = None if moving_episode_horizon is None else int(moving_episode_horizon)
        self._source_weights = None if source_weights is None else np.asarray(source_weights, dtype=np.float64)
        self._bank = None
        self._bank_p = None
        self._moving_init = False
        self._source_cmd = -1
        self._aligned = False
        self._horizon = None
        kwargs.setdefault("joy_input_random", False)
        super().__init__(**kwargs)

    # ------------------------------------------------------------------ 은행
    def _load_bank(self) -> None:
        if self._bank is not None or not self._bank_path:
            return
        d = np.load(self._bank_path)
        self._bank = {
            "qpos": np.asarray(d["qpos"], dtype=np.float64),
            "qvel": np.asarray(d["qvel"], dtype=np.float64),
            "mvec": np.asarray(d["mvec"], dtype=np.float64),
            "source": np.asarray(d["source"], dtype=np.int64),
        }
        assert self._bank["qpos"].shape[1] == self.model.nq and self._bank["qvel"].shape[1] == self.model.nv, "은행 상태 차원 불일치"
        src = self._bank["source"]
        n = int(src.max()) + 1
        w = np.ones(n) if self._source_weights is None else self._source_weights
        assert len(w) >= n, "source_weights 길이 부족"
        p = w[src].astype(np.float64)
        assert p.sum() > 0, "선택 가능한 출발 상태가 없음"
        self._bank_p = p / p.sum()

    @property
    def bank_size(self) -> int:
        self._load_bank()
        return 0 if self._bank is None else len(self._bank["source"])

    # ------------------------------------------------------------------ reset
    def reset_model(self):
        observation = super().reset_model()  # 정지 시작 상태 + 필터 리셋 + k=0
        self._moving_init = False
        self._source_cmd = -1
        self._aligned = False
        self._horizon = None
        self._load_bank()
        if self._bank is not None and self.np_random.random() < self._moving_init_prob:
            i = int(self.np_random.choice(len(self._bank_p), p=self._bank_p))
            self.set_state(self._bank["qpos"][i].copy(), self._bank["qvel"][i].copy())
            mvec = self._bank["mvec"][i]
            if self.np_random.random() < self._align_prob and np.any(mvec):
                # 시작 위상 규칙 (phase_align.py): 'sign' = 현행 부호 정렬, 'lat' = 가로 부호 우선 (iteration 4)
                self._k = start_k(self._gait, mvec, self._align_rule)
                self._aligned = True
            else:
                self._k = int(self.np_random.integers(self._gait.Mvecs))
            self._motion_vector = self._gait.getMvec(self._k).copy()
            observation = self._get_obs(self._motion_vector)
            self._moving_init = True
            self._source_cmd = int(self._bank["source"][i])
            self._horizon = self._moving_episode_horizon
        else:
            # 부모는 reset에서 _motion_vector를 갱신하지 않으므로 명시 초기화
            self._motion_vector = self._gait.getMvec(self._k).copy()
        return observation

    def step(self, action):
        observation, reward, terminated, truncated, info = super().step(action)
        # 부모(plane_v3)는 is_terminated를 스텝당 두 번 호출(_get_rew, step)해 보상 계산
        # 시점에는 아직 종료 전이므로 종료 스텝에 unhealthy_cost가 실리지 않는다(항상 0).
        # 인계 시작 학습은 낙상 비용이 핵심 신호이므로 종료 스텝에 1회 보정해 싣는다.
        # 종료 타이밍(카운터 이중 증가)은 부모와 동일하게 둔다 (전문가 계보와 정합).
        if terminated and self._terminate_when_unhealthy and float(info.get("cost_unhealthy", 0.0)) == 0.0:
            reward -= self._unhealthy_cost_weight
            info["cost_unhealthy"] = -float(self._unhealthy_cost_weight)
        # iteration 3: 인계 시작 에피소드 한정 기울기 벌점 + 기운 채로 세게 밀기 벌점 (상태 조건, 정책이 관측 가능)
        cost_tilt = cost_push = 0.0
        if self._moving_init and (self._tilt_w > 0.0 or self._push_w > 0.0):
            if self._amp_max is None:
                self._amp_max = max(1e-6, float(np.max(np.abs(self.action_space.high))))
            roll = abs(float(self._cur_euler_ypr[2]))
            x = (roll - self._tilt_dead) / max(1e-6, self._tilt_ref - self._tilt_dead)
            if x > 0.0:
                cost_tilt = -self._tilt_w * min(x, 2.0)
                amp = float(np.mean(np.abs(np.asarray(action, dtype=np.float64)))) / self._amp_max
                cost_push = -self._push_w * min(x, 1.0) * amp
                reward += cost_tilt + cost_push
        info["cost_tilt"] = cost_tilt
        info["cost_push_tilt"] = cost_push
        info["moving_init"] = self._moving_init
        info["source_cmd"] = self._source_cmd
        info["init_aligned"] = self._aligned
        if self._horizon is not None and self._n_step >= self._horizon:
            truncated = True
        return observation, reward, terminated, truncated, info
