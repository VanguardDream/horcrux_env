#!/usr/bin/env bash
# =============================================================================
# Horcrux 학습용 conda 환경 초기 설정 스크립트
#
# 수행 내용:
#   1. 기존 `horcrux` conda 환경 삭제
#   2. Python 3.11 환경 재생성
#   3. pip install -e ".[train]"  (Gymnasium, MuJoCo, SB3, PyTorch 등)
#   4. NVIDIA GPU 감지 시 CUDA wheel로 PyTorch 교체
#   5. 설치 검증 (import, pip check, CUDA 인식)
#   6. 환경 무결성 확인 (run_env 200 steps)
#   7. Smoke 학습 (training/configs/smoke.yaml)
#
# 사용법 (zsh에서 실행 가능):
#   bash scripts/setup_conda_env.sh              # 전체 실행
#   bash scripts/setup_conda_env.sh --cpu        # CUDA torch 교체 생략
#   bash scripts/setup_conda_env.sh --skip-smoke # smoke 학습 생략
#
# 환경 변수로 CUDA wheel 버전 변경 가능:
#   TORCH_VERSION=2.13.0 CUDA_TAG=cu132 bash scripts/setup_conda_env.sh
#   (기본값은 기존 학습 PC와 동일한 torch 2.13.0 + cu132)
# =============================================================================
set -euo pipefail

ENV_NAME="horcrux"
PYTHON_VERSION="3.11"
TORCH_VERSION="${TORCH_VERSION:-2.13.0}"
CUDA_TAG="${CUDA_TAG:-cu132}"
INSTALL_CUDA=1
RUN_SMOKE=1

for arg in "$@"; do
  case "$arg" in
    --cpu)        INSTALL_CUDA=0 ;;
    --skip-smoke) RUN_SMOKE=0 ;;
    *) echo "알 수 없는 옵션: $arg" >&2; exit 1 ;;
  esac
done

step() { echo; echo "=== $1 ==="; }

# --- 프로젝트 루트로 이동 -----------------------------------------------------
cd "$(dirname "$0")/.."
if [[ ! -f pyproject.toml ]]; then
  echo "오류: 프로젝트 루트를 찾을 수 없습니다." >&2
  exit 1
fi

# --- conda 초기화 -------------------------------------------------------------
step "conda 확인"
if ! command -v conda >/dev/null 2>&1; then
  echo "오류: conda를 찾을 수 없습니다. Miniconda/Anaconda 설치 후 다시 실행하세요." >&2
  exit 1
fi
CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda deactivate 2>/dev/null || true
echo "conda base: $CONDA_BASE"

# --- 1. 기존 환경 삭제 --------------------------------------------------------
step "기존 '$ENV_NAME' 환경 삭제"
if conda env list | grep -qE "^${ENV_NAME}[[:space:]]"; then
  conda env remove -n "$ENV_NAME" -y
  echo "삭제 완료."
else
  echo "기존 환경 없음. 건너뜀."
fi

# --- 2. 환경 재생성 -----------------------------------------------------------
step "'$ENV_NAME' 환경 생성 (Python $PYTHON_VERSION)"
conda create -n "$ENV_NAME" "python=$PYTHON_VERSION" pip -y
conda activate "$ENV_NAME"
python --version

# --- 3. 프로젝트 + 학습 의존성 설치 -------------------------------------------
step "pip install -e \".[train]\""
pip install -e ".[train]"

# --- 4. CUDA PyTorch 교체 -----------------------------------------------------
if [[ "$INSTALL_CUDA" -eq 1 ]]; then
  step "CUDA PyTorch 설치 (torch ${TORCH_VERSION}+${CUDA_TAG})"
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,driver_version --format=csv,noheader || true
    if ! pip install --force-reinstall --no-deps \
        "torch==${TORCH_VERSION}+${CUDA_TAG}" \
        --index-url "https://download.pytorch.org/whl/${CUDA_TAG}"; then
      echo "경고: ${CUDA_TAG} wheel 설치 실패. pip 기본 torch를 유지합니다." >&2
      echo "      GPU 드라이버에 맞는 wheel을 https://pytorch.org/get-started/locally/ 에서 확인하세요." >&2
    fi
  else
    echo "경고: nvidia-smi를 찾을 수 없어 CUDA 교체를 건너뜁니다 (CPU torch 유지)." >&2
  fi
else
  echo; echo "=== CUDA 교체 생략 (--cpu) ==="
fi

# --- 5. 설치 검증 -------------------------------------------------------------
step "설치 검증"
python - <<'PY'
import gymnasium, mujoco, stable_baselines3, torch
print("gymnasium         :", gymnasium.__version__)
print("mujoco            :", mujoco.__version__)
print("stable-baselines3 :", stable_baselines3.__version__)
print("torch             :", torch.__version__)
print("CUDA available    :", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU               :", torch.cuda.get_device_name(0))
PY
python -m pip check || echo "경고: pip check에서 충돌이 보고되었습니다. 위 출력을 확인하세요."

# --- 6. 환경 무결성 확인 ------------------------------------------------------
step "Gymnasium 환경 확인 (run_env 200 steps, headless)"
python training/run_env.py --config training/configs/environment_plane.yaml --steps 200

# --- 7. Smoke 학습 ------------------------------------------------------------
if [[ "$RUN_SMOKE" -eq 1 ]]; then
  step "Smoke 학습 (256 timesteps)"
  python training/train.py --config training/configs/smoke.yaml
  echo
  echo "Smoke 결과: runs/smoke/ 확인"
else
  echo; echo "=== Smoke 학습 생략 (--skip-smoke) ==="
fi

# --- 완료 ---------------------------------------------------------------------
step "설정 완료"
cat <<'EOF'
다음 단계:
  conda activate horcrux
  python training/train.py --config training/configs/ppo_plane.yaml        # 본 학습
  tensorboard --logdir ./runs --port 6006                                  # 모니터링

기존 정책 이어서 학습 (resume):
  python training/train.py --config training/configs/ppo_plane_left_continue_stage3.yaml
EOF
