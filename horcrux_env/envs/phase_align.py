"""전환 순간의 시작 위상(모션 행렬의 열) 선택 규칙 — 인계 시작 env, 통합 env set_gait, 경로 추종 시연이 공유한다.

  sign  현재 모션 벡터와 부호 일치(내적 = 같은 부호 수 − 다른 부호 수)가 최대인 열. 현행 규칙(2026-09-08).
  lat   가로(짝수 관절, 좌우 굽힘 = 미는 방향) 부호 일치를 먼저 최대화하고, 동점이면 세로(홀수 관절, 위아래 굽힘 = 접지 마디)
        부호 일치로 정한다. 2026-09-11 검증: 대표 전문가 8개 × 1,440 상태에서 진입 실패 0.231 → 0.158(집안 간 .340 → .223,
        같은 집안 불변). 근거: 집안(δ+180)을 건널 때는 미는 방향을 잇고 접지 마디를 바꾸는 위상이 그 반대보다 안전하다.

역재생 gait는 getMvec(k)가 열 -k를 읽으므로 시작 k = -col (start_k 참조).

같은 부호 패턴은 행렬(약 3,140열 = 100주기) 안에 주기마다 반복된다. 'sign'은 현행과 똑같이 첫 열(argmax)을 고른다.
'lat'은 동점 열 가운데 행렬 한가운데에 가장 가까운 열을 고른다 — 열 번호가 끝(또는 역재생이면 처음)에 가까우면
몇 스텝 안에 열 번호가 감겨(3139 → 0) 표본 위상이 약 0.3 rad 튀는 작은 불연속이 생기기 때문이다.
"""
from typing import Sequence

import numpy as np

RULES = ("sign", "lat")


def align_column(motion_matrix: np.ndarray, mvec: Sequence[float], rule: str = "sign") -> int:
    """현재 모션 벡터 mvec에 대해 목표 gait 모션 행렬(14 × 열)에서 시작할 열 번호를 고른다."""
    M = np.asarray(motion_matrix, dtype=np.float64)
    v = np.asarray(mvec, dtype=np.float64)
    prod = M * v[:, None]
    if rule == "sign":
        return int(np.argmax(prod.sum(axis=0)))          # 동점이면 첫 열 (현행과 동일)
    if rule == "lat":
        lat_agree = prod[1::2].sum(axis=0)                # 짝수 관절(인덱스 1, 3, ...) = 가로 파동
        dor_agree = prod[0::2].sum(axis=0)                # 홀수 관절(인덱스 0, 2, ...) = 세로 파동
        best = lat_agree == lat_agree.max()
        best &= dor_agree == dor_agree[best].max()
        cands = np.flatnonzero(best)
        return int(cands[np.argmin(np.abs(cands - M.shape[1] / 2))])   # 동점 중 행렬 한가운데에 가장 가까운 열
    raise ValueError(f"unknown align rule: {rule!r} (choose from {RULES})")


def start_k(gait, mvec: Sequence[float], rule: str = "sign") -> int:
    """gait 객체(MotionMatrix, _reverse)와 현재 모션 벡터로 시작 위상 k를 돌려준다."""
    col = align_column(gait.MotionMatrix, mvec, rule)
    return -col if gait._reverse else col
