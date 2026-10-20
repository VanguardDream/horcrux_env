#!/usr/bin/env python3
"""Claude Code PreToolUse 훅: 학습 실행과 고정 환경 파일 수정 앞에서 확인을 요구한다 (2026-10-20).

표준 입력으로 훅 JSON(tool_name, tool_input)을 받고, 확인이 필요하면 permissionDecision "ask" 를
돌려준다. 그 밖에는 아무것도 출력하지 않는다(도구 호출이 그대로 진행된다).

- Bash: 명령에 학습 실행(launch_training.sh, training/train.py)이 들어 있으면 확인.
        보호 파일 이름과 쓰기 흔적(sed -i, >, >>, tee, mv, cp, python ... 파일 수정)이 함께 있으면 확인.
- Edit / Write / MultiEdit / NotebookEdit: 대상이 보호 파일이면 확인.

보호 파일 = 완성 계보가 쓰는 환경 파일 전부 (CLAUDE.md "실험 안전"). 훅은 도구 호출을 잡을 뿐이고
우회될 수 있으므로, 의미 변화는 tests/test_env_regression.py 가 잡는다.
"""
import json
import re
import sys

PROTECTED = (
    "horcrux_env/envs/plane_v3.py",
    "horcrux_env/envs/plane_rotation_v1.py",
    "horcrux_env/envs/plane_unified_v1.py",
    "horcrux_env/envs/plane_moving_init_v1.py",
    "horcrux_env/envs/gait_provider.py",
    "horcrux_env/envs/gait_v2.py",
    "horcrux_env/envs/gait_v3.py",
    "horcrux_env/envs/phase_align.py",
)
TRAIN_RE = re.compile(r"launch_training\.sh|training/train\.py|\btrain\.py\b")
WRITE_RE = re.compile(r"sed\s+-i|>\s*\S|\btee\b|\bmv\b|\bcp\b|write_text|open\([^)]*['\"]w|\.replace\(|truncate")


def ask(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "ask",
                                             "permissionDecisionReason": reason}}, ensure_ascii=False))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}
    if tool == "Bash":
        cmd = str(inp.get("command", ""))
        if TRAIN_RE.search(cmd) and "--help" not in cmd and "py_compile" not in cmd:
            ask("학습 실행 명령입니다. CLAUDE.md '실험 안전': 설계 요약을 보고하고 사용자 승인을 받은 뒤에만 띄웁니다. "
                "(스모크 설정이나 사전 승인된 루프 단계면 승인하세요.)")
            return
        hit = [p for p in PROTECTED if p.split("/")[-1] in cmd]
        if hit and WRITE_RE.search(cmd):
            ask("고정 환경 파일을 셸로 고치려는 것 같습니다: " + ", ".join(hit) +
                ". 완성 계보의 보상·종료·관측 의미는 바꾸지 않습니다(CLAUDE.md). 의도한 변경이면 승인하고, "
                "끝난 뒤 tests/test_env_regression.py 를 돌리세요.")
        return
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = str(inp.get("file_path", inp.get("notebook_path", "")))
        hit = [p for p in PROTECTED if path.endswith(p)]
        if hit:
            ask(f"고정 환경 파일 수정: {hit[0]}. 완성 계보의 보상·종료·관측 의미는 바꾸지 않습니다(CLAUDE.md '실험 안전'). "
                "새 환경 파일이나 기본값이 예전 동작인 kwargs 로 만드는 쪽을 먼저 생각하세요. 의도한 변경이면 승인하고, "
                "끝난 뒤 tests/test_env_regression.py 를 돌리세요.")


if __name__ == "__main__":
    main()
