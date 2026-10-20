#!/usr/bin/env bash
# 학습 결과 백업: runs/, policies/, docs/ 와 git 번들을 백업 디스크로 복사한다 (2026-10-20).
#
#   scripts/backup_to_disk.sh                 # 기본 대상 /mnt/backup8tb/horcrux_env
#   BACKUP_ROOT=/다른/경로 scripts/backup_to_disk.sh
#   scripts/backup_to_disk.sh --dry-run       # 무엇이 복사될지만 본다
#
# 원칙 (CLAUDE.md "실험 안전"):
#   - 추가·갱신만 한다. 원본에서 지운 파일을 백업에서 지우지 않는다 (--delete 없음).
#   - 원본은 건드리지 않는다. 백업이 확인되기 전에는 어떤 run/policy도 지우지 않는다.
#   - 코드는 git 번들로 함께 남겨 백업 디스크만으로 코드+결과를 되살릴 수 있게 한다.
#
# 기록: <대상>/backup_log.txt 에 시작·종료 시각, 전송량, 결과를 한 줄씩 덧붙인다.
# 되살리기: rsync -a <대상>/runs/ runs/ ;  git clone <대상>/horcrux_env.bundle

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-/mnt/backup8tb}"
DEST="$BACKUP_ROOT/horcrux_env"
DRY=""
[[ "${1:-}" == "--dry-run" ]] && DRY="--dry-run"

if ! mountpoint -q "$BACKUP_ROOT"; then
    echo "백업 디스크가 $BACKUP_ROOT 에 마운트돼 있지 않습니다. 중단합니다." >&2
    exit 1
fi
mkdir -p "$DEST"
LOG="$DEST/backup_log.txt"
START="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$START] 시작 ${DRY:+(dry-run)} 원본=$PROJECT_ROOT 대상=$DEST" | tee -a "$LOG"

cd "$PROJECT_ROOT"

# 1) 결과 폴더: 추가·갱신만, 중단돼도 이어서 복사(--partial). 진행률은 찍지 않는다(로그 오염).
#    --delete 를 절대 넣지 않는다.
rsync -a --partial --stats --info=flist0 $DRY \
    --exclude '__pycache__/' \
    runs policies docs "$DEST/" 2>&1 | tail -n 15 | tee -a "$LOG"

# 2) 코드: 전체 git 이력을 번들 하나로 (커밋되지 않은 변경은 포함되지 않으므로 먼저 커밋한다).
if [[ -z "$DRY" ]]; then
    git bundle create "$DEST/horcrux_env.bundle" --all 2>&1 | tail -n 1
    git rev-parse HEAD > "$DEST/horcrux_env.bundle.head"
    DIRTY="$(git status --porcelain | wc -l)"
    echo "git 번들: $(git rev-parse --short HEAD) (커밋되지 않은 변경 ${DIRTY}건)" | tee -a "$LOG"
fi

END="$(date '+%Y-%m-%d %H:%M:%S')"
USED="$(du -sh "$DEST" 2>/dev/null | cut -f1)"
echo "[$END] 끝 대상 크기=$USED 남은 공간=$(df -h "$BACKUP_ROOT" | awk 'NR==2{print $4}')" | tee -a "$LOG"
