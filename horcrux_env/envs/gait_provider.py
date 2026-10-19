"""명령→gait 결정을 환경 밖으로 위임하는 provider 추상화.

현재는 검증된 사전 정의 테이블(CommandGaitTable)이 기본 구현이지만,
인터페이스를 분리해 두어 추후 다음이 같은 자리에 꽂힐 수 있다:
  - 적응형 스케줄러 (지형/상태 기반 gait 전환)
  - 상위 정책이 gait 파라미터를 직접 출력하는 계층적 RL
환경은 reset 시 params_for(joy)를 묻고, 에피소드 중에는
env.set_gait(params)로 임의 시점 교체가 가능하다 (plane_unified_v1 참조).

테이블의 각 항목은 2026-09 방위 캠페인에서 실학습으로 검증된 값이다
(정책 원장: policies/path_tracking/*, policies/rotation/*).
"""
from typing import Optional, Sequence, Tuple

import numpy as np

GaitParams = Tuple[float, ...]

# (이름, joy_input, gait_params) — 10개 검증 명령
S2 = float(np.sqrt(2) / 2)
VALIDATED_COMMANDS: Tuple[Tuple[str, Tuple[float, float, float], GaitParams], ...] = (
    ("forward",  (1.0, 0.0, 0.0),   (30, 30, 40, 40, 0)),
    ("left",     (0.0, 1.0, 0.0),   (30, 30, 40, 40, 45)),
    ("right",    (0.0, -1.0, 0.0),  (30, 30, 40, 40, 225)),
    ("diag_fl",  (S2, S2, 0.0),     (30, 30, 40, 40, 23)),
    ("diag_fr",  (S2, -S2, 0.0),    (30, 30, 40, 40, 203)),
    ("backward", (-1.0, 0.0, 0.0),  (30, 30, 40, 40, 0, -1)),
    ("diag_bl",  (-S2, S2, 0.0),    (30, 30, 40, 40, 203, -1)),
    ("diag_br",  (-S2, -S2, 0.0),   (30, 30, 40, 40, 23, -1)),
    ("ccw",      (0.0, 0.0, 1.0),   (30, 30, 40, 40, 315)),
    ("cw",       (0.0, 0.0, -1.0),  (30, 30, 40, 40, 135)),
)


class GaitProvider:
    """명령(joy_input)에 대응하는 gait 파라미터를 결정한다."""

    def params_for(self, joy_input: Sequence[float]) -> GaitParams:
        raise NotImplementedError


class CommandGaitTable(GaitProvider):
    """검증 테이블 기반 기본 구현. joy 벡터에 가장 가까운 명령을 매칭한다."""

    def __init__(self, commands=VALIDATED_COMMANDS) -> None:
        self._commands = commands
        self._joys = np.array([c[1] for c in commands], dtype=np.float64)

    def __len__(self) -> int:
        return len(self._commands)

    def command_index(self, joy_input: Sequence[float]) -> int:
        joy = np.asarray(joy_input, dtype=np.float64)
        return int(np.argmin(np.linalg.norm(self._joys - joy, axis=1)))

    def name(self, index: int) -> str:
        return self._commands[index][0]

    def joy(self, index: int) -> Tuple[float, float, float]:
        return self._commands[index][1]

    def params(self, index: int) -> GaitParams:
        return self._commands[index][2]

    def params_for(self, joy_input: Sequence[float]) -> GaitParams:
        return self.params(self.command_index(joy_input))
