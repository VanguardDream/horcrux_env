from typing import Optional
import numpy as np

from horcrux_env.envs.gait_v2 import GaitV2

class GaitV3(GaitV2):
    """
    GaitV3 generalizes GaitV2 to an arbitrary joint count n (CoRL 2026 rebuttal,
    joint-count scaling experiment).

    GaitV2's hand-written serpenoid (j_1..j_14) follows one rule:
        odd joint i  (dorsal/vertical,  Y-axis): sin(e_d1 * i + (e_d2/10) * t)
        even joint i (lateral/horizontal, Z-axis): sin(e_l1 * i + (e_l2/10) * t + delta)
    This class vectorizes that rule over i = 1..n_joints. Everything else
    (double-diff -> sign motion matrix, cyclic getMvec, reset) is inherited
    unchanged from GaitV2, so n_joints=14 reproduces GaitV2 bit-for-bit.

    Scaling protocol note: gait params are kept FIXED across n (per rebuttal
    decision), so the number of spatial waves on the body varies with n.
    """
    def __init__(self, params:tuple[float, float, int, int, float, int], n_joints:int = 14, sampling_t = 0.1, model_timestep = 0.005, frame_skip = 20) -> None:
        self.n_joints = n_joints
        super().__init__(params, sampling_t=sampling_t, model_timestep=model_timestep, frame_skip=frame_skip)

    def serpenoid(self, t, e_d1:float, e_l1:float, e_d2:float, e_l2:float, delta:float)->np.ndarray:
        #Hirose (1993) serpenoid curve, vectorized over joint index
        e_d1 = np.radians(e_d1)
        e_l1 = np.radians(e_l1)
        delta = np.radians(delta)

        f1 = (e_d2/10) * t
        f2 = (e_l2/10) * t

        idx = np.arange(1, self.n_joints + 1)
        odd = (idx % 2 == 1)[:, None]

        # 연산 순서를 GaitV2와 동일하게 유지해 비트 단위 동일성을 보장한다
        dorsal = np.sin(e_d1 * idx[:, None] + f1[None, :])
        lateral = np.sin(e_l1 * idx[:, None] + f2[None, :] + delta)

        return np.where(odd, dorsal, lateral)


if __name__ == "__main__":
    # 검증: python -m horcrux_env.envs.gait_v3
    PARAM_SETS = [
        (30, 30, 40, 40, 45),
        (30, 30, 40, 40, 23),
        (30, 30, 40, 40, 0),
        (30, 30, 40, 40, -23),
        (30, 30, 40, 40, -45),
        (30, 30, 40, 40, 23, -1),
        (30, 30, 40, 40, 0, -1),
        (30, 30, 40, 40, -23, -1),
        (15, 45, 20, 60, 90),       # 상이한 시간 파라미터(gcd=20) 조합
    ]

    print("[1] n=14 bitwise equivalence vs GaitV2:")
    for params in PARAM_SETS:
        ref = GaitV2(params)
        gen = GaitV3(params, n_joints=14)
        assert np.array_equal(ref.MotionMatrix, gen.MotionMatrix), f"MotionMatrix mismatch: {params}"
        assert ref.Mvecs == gen.Mvecs and ref.joints == gen.joints
        for k in (0, 1, 7, 100, ref.Mvecs - 1, ref.Mvecs + 5):
            assert np.array_equal(ref.getMvec(k), gen.getMvec(k)), f"getMvec({k}) mismatch: {params}"
        print(f"    params={params}: MotionMatrix {gen.MotionMatrix.shape} identical — OK")

    print("[2] reset() equivalence (params/frame_skip change):")
    ref = GaitV2(PARAM_SETS[0])
    gen = GaitV3(PARAM_SETS[0], n_joints=14)
    ref.reset(params=PARAM_SETS[2], frame_skip=10)
    gen.reset(params=PARAM_SETS[2], frame_skip=10)
    assert np.array_equal(ref.MotionMatrix, gen.MotionMatrix)
    print("    reset 후에도 identical — OK")

    print("[3] n=6/10/20 sanity (독립 루프 구현 대조):")
    def naive_serpenoid(n, t, e_d1, e_l1, e_d2, e_l2, delta):
        e_d1, e_l1, delta = np.radians(e_d1), np.radians(e_l1), np.radians(delta)
        rows = []
        for i in range(1, n + 1):
            if i % 2 == 1:
                rows.append(np.sin(e_d1 * i + (e_d2/10) * t))
            else:
                rows.append(np.sin(e_l1 * i + (e_l2/10) * t + delta))
        return np.array(rows)

    for n in (6, 10, 20):
        params = (30, 30, 40, 40, 0)
        gen = GaitV3(params, n_joints=n)
        assert gen.MotionMatrix.shape[0] == n == gen.joints
        assert set(np.unique(gen.MotionMatrix)).issubset({-1.0, 0.0, 1.0})
        raw_ref = naive_serpenoid(n, gen._t, *params[:5])
        raw_gen = gen.serpenoid(gen._t, *params[:5])
        assert np.array_equal(raw_ref, raw_gen), f"n={n} serpenoid mismatch"
        print(f"    n={n:2d}: MotionMatrix {gen.MotionMatrix.shape}, values in {{-1,0,1}}, 독립 구현과 identical — OK")

    print("all checks passed")
