# Horcrux 학습 가이드

이 디렉토리는 `horcrux_env`의 Stable-Baselines3(SB3) 학습·평가 도구를
제공합니다. 환경 구현과 MuJoCo 모델은 `horcrux_env/`에 있고, 학습 결과는
Git에서 제외되는 `runs/`에 저장됩니다.

이 문서의 명령은 프로젝트 루트에서 PowerShell 7(`pwsh`)로 실행하는 것을
기준으로 합니다.

## 1. Conda 환경 준비

Python 3.11 환경을 만들고 프로젝트와 학습 의존성을 설치합니다.

```powershell
conda create -n horcrux python=3.11 pip -y
conda activate horcrux
pip install -e ".[train]"
```

`.[train]`은 Gymnasium, MuJoCo, Stable-Baselines3, PyTorch, PyYAML,
TensorBoard, MoviePy를 함께 설치합니다. Editable 설치이므로 소스 코드를
수정하면 패키지를 다시 설치하지 않아도 변경 사항이 반영됩니다.

이 PC에서 `conda` 명령이 인식되지 않는다면 먼저 hook을 불러옵니다.

```powershell
(& "$env:USERPROFILE\miniconda3\Scripts\conda.exe" "shell.powershell" "hook") |
    Out-String |
    Invoke-Expression

conda activate horcrux
```

설치 상태를 확인합니다.

```powershell
python -c "import gymnasium, mujoco, stable_baselines3, torch; print(gymnasium.__version__, mujoco.__version__, stable_baselines3.__version__, torch.__version__)"
python -m pip check
```

### NVIDIA CUDA 사용(선택)

기본 pip 설치가 CPU용 PyTorch를 선택했다면 시스템 드라이버에 맞는 공식
CUDA wheel로 교체해야 합니다. 현재 개발 환경(RTX 4090, CUDA 13.x
드라이버)에서 검증한 설치 예시는 다음과 같습니다.

```powershell
python -m pip install `
  --force-reinstall `
  --no-deps `
  torch==2.13.0+cu132 `
  --index-url https://download.pytorch.org/whl/cu132
```

CUDA 연결을 확인합니다.

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

GPU 또는 드라이버가 다르면 [PyTorch 공식 설치 페이지](https://pytorch.org/get-started/locally/)에서
맞는 wheel을 선택하세요. 현재 정책은 작은 MLP이므로 CUDA가 인식되더라도 PPO 학습은
CPU가 더 빠를 수 있습니다. YAML의 `algorithm.device` 또는 CLI의
`--device`로 직접 비교하는 것을 권장합니다.

## 2. Gymnasium 환경만 먼저 확인

학습 전에 환경 생성과 `reset/step`이 정상인지 확인합니다.

```powershell
python training/run_env.py `
  --config training/configs/environment_plane.yaml `
  --steps 1000
```

MuJoCo 화면을 보면서 실행하려면:

```powershell
python training/run_env.py --render-mode human --steps 1000
```

환경 인수는 `training/configs/environment_plane.yaml`의
`environment.kwargs`에서 조정합니다. 보상·비용 가중치, gait, 목표 방향,
종료 조건, 마찰 무작위화와 센서 필터를 설정할 수 있습니다.

## 3. Smoke 학습

본 학습 전에 반드시 짧은 smoke 설정을 실행합니다.

```powershell
python training/train.py --config training/configs/smoke.yaml
```

Smoke 학습은 256 timestep만 실행하며 다음 항목을 확인하기 위한 용도입니다.

- 환경 생성 및 rollout 수집
- PPO 정책 업데이트
- TensorBoard 로그 기록
- `final_model.zip` 저장
- CUDA/CPU 장치 선택

Smoke 결과는 `runs/smoke/`에 저장됩니다. Smoke 학습 성공은 정책 성능이
좋다는 의미가 아니라 학습 파이프라인이 정상이라는 의미입니다.

## 4. PPO 본 학습

기본 평지 PPO 학습을 시작합니다.

```powershell
python training/train.py --config training/configs/ppo_plane.yaml
```

기존 모델과 observation 통계를 이어서 학습하려면 resume 설정이 포함된
fine-tune 프로필을 사용합니다. `training.total_timesteps`는 이 경우 기존
timestep을 포함한 총량이 아니라 추가로 학습할 timestep입니다.

```powershell
python training/train.py --config training/configs/ppo_plane_finetune.yaml
```

resume 모델의 `n_steps`, `batch_size`, `gamma`는 저장 모델과 같아야 합니다.
`learning_rate`와 `n_epochs`는 fine-tune 설정으로 덮어쓸 수 있으며, 누적
timestep은 TensorBoard와 체크포인트 이름에서 계속 유지됩니다.

YAML을 수정하지 않고 일부 값을 덮어쓸 수도 있습니다.

```powershell
python training/train.py `
  --config training/configs/ppo_plane.yaml `
  --device cuda `
  --seed 123 `
  --total-timesteps 1000000 `
  --output-dir runs/manual
```

지원하는 CLI 옵션은 다음 명령으로 확인합니다.

```powershell
python training/train.py --help
```

학습 중 Ctrl+C를 누르면 해당 run 디렉토리에
`interrupted_model.zip`을 저장하고 환경을 안전하게 종료합니다.

### VS Code에서 실행

Run and Debug에서 다음 구성을 선택한 뒤 F5를 누릅니다.

- `Environment: Plane (Headless)`: 환경만 실행
- `Train: Smoke`: 짧은 검증 학습
- `Train: PPO Plane`: PPO 본 학습

워크스페이스는 `horcrux` Conda 인터프리터를 사용하도록 설정되어 있습니다.

## 5. 학습 설정 구조

학습 설정은 `training/configs/ppo_plane.yaml`에 있습니다.

```yaml
experiment:
  name: ppo_plane_baseline
  seed: 42
  output_dir: runs/ppo_plane

environment:
  id: horcrux_env/plane-v0
  kwargs:
    joy_input_random: false
    joy_input: [1.0, 0.0, 0.0]

algorithm:
  name: PPO
  policy: MlpPolicy
  device: auto
  kwargs:
    learning_rate: 0.0003
    gamma: 0.99
    n_steps: 2048
    batch_size: 128
    n_epochs: 10

sampling:
  num_envs: 8
  vec_env: subproc
  start_method: spawn

normalization:
  enabled: true
  clip_obs: 10.0
  epsilon: 1.0e-8

action_normalization:
  enabled: true

training:
  total_timesteps: 1000000
```

주요 규칙은 다음과 같습니다.

- Gymnasium 생성자 인수: `environment.kwargs`
- SB3 PPO 생성자 인수: `algorithm.kwargs`
- 정책 신경망 구조: `algorithm.policy_kwargs`
- 전체 학습량: `training.total_timesteps`
- `sampling.num_envs`: 동시에 실행할 Gymnasium 환경 수
- `sampling.vec_env`: `dummy`는 순차 실행, `subproc`는 프로세스 병렬 실행
- Windows에서는 `sampling.start_method: spawn` 사용
- `n_steps`는 환경 하나가 PPO update 전에 수집하는 step 수
- PPO iteration 하나의 전체 표본 수는 `n_steps × num_envs`
- `n_steps × num_envs`는 `batch_size`로 나누어떨어져야 함
- `normalization.enabled`: observation의 running mean/variance 정규화
- `normalization.clip_obs`: 정규화된 observation의 절댓값 제한
- `action_normalization.enabled`: 정책 action을 `[-1, 1]`로 노출하고 환경의
  물리 action 범위로 변환
- checkpoint와 evaluation 주기는 environment timestep 단위
- 영상 녹화 주기는 PPO iteration 단위

본 학습 설정은 8개의 MuJoCo 환경을 별도 프로세스로 실행합니다. 각 환경은
`seed + rank`를 사용하며 Monitor 로그도 환경별 파일로 분리됩니다. Smoke
설정은 Windows `spawn` 경로까지 빠르게 검사하기 위해 2개 환경을 사용합니다.

관측 정규화가 활성화되면 SB3 `VecNormalize`가 97개 observation 차원마다
평균과 분산을 따로 추정합니다. 입력은 정규화 후 `[-clip_obs, clip_obs]`로
제한되며 reward는 정규화하지 않습니다. 평가와 영상 녹화에는 학습 환경의
동일한 통계가 적용됩니다.

Action 정규화가 활성화되면 기본 Gymnasium 환경의 `[0, 2.7]` 범위는
변경하지 않고 `NormalizeAction` wrapper가 정책에 `[-1, 1]` 범위를
노출합니다. wrapper는 `-1 → 0`, `0 → 1.35`, `1 → 2.7`로 선형 변환하며
학습, 평가 및 영상 녹화에 동일하게 적용됩니다.

## 6. TensorBoard 모니터링

모든 run을 함께 확인합니다.

```powershell
tensorboard --logdir .\runs --port 6006
```

브라우저에서 <http://localhost:6006>을 엽니다. `tensorboard` 실행 파일이
인식되지 않으면 다음과 같이 실행합니다.

```powershell
python -m tensorboard.main --logdir .\runs --port 6006
```

주요 scalar는 다음과 같습니다.

- `rollout/ep_rew_mean`, `rollout/ep_len_mean`
- `train/loss`, `train/value_loss`, `train/policy_gradient_loss`
- `env/x_velocity`, `env/y_velocity`, `env/yaw_velocity`
- `env/reward_*`, `env/cost_*`
- `video/last_recorded_iteration`, `video/last_recorded_timestep`

환경 `info` 값을 TensorBoard에 추가하는 방법은
`training/callbacks/info_metrics.py`와 `training/callbacks/README.md`를
참고하세요.

## 7. 정책 영상 녹화

본 학습 설정은 별도의 평가 환경에서 정책 영상을 녹화합니다.

```yaml
video:
  enabled: true
  start_iteration: 10
  record_every_iterations: 10
  video_length: 100
  deterministic: true
```

이 설정은 PPO update가 10회 완료된 뒤 처음 녹화하고, 이후 10 iteration마다
녹화합니다. 전체 timestep은 `iteration × n_steps × num_envs`로 계산합니다.
예를 들어 `n_steps: 2048`, `num_envs: 8`이면 iteration 10은 약 163,840
timestep입니다.

한 번만 녹화하려면:

```yaml
video:
  enabled: true
  start_iteration: 50
  record_every_iterations: null
  video_length: 200
  deterministic: true
```

영상은 `<run>/videos/`에 MP4로 저장됩니다. `video_length: 100`은 현재
20 FPS 기준 약 5초입니다. 미학습 초기에도 움직임을 확인하려면
`deterministic: false`를 사용할 수 있습니다.

## 8. 결과 디렉토리

각 실행은 이전 결과를 덮어쓰지 않도록 timestamp 디렉토리를 생성합니다.

```text
runs/ppo_plane/20260715-120000-000000_ppo_plane_baseline/
├── final_model.zip          # 최종 SB3 정책
├── interrupted_model.zip    # Ctrl+C 종료 시 생성
├── vecnormalize.pkl         # 최종/중단 모델의 observation 통계
├── resolved_config.yaml     # CLI override까지 반영된 실제 설정
├── metadata.json            # 패키지 버전, Python, Git revision
├── monitor/                 # 환경별 episode 길이와 return
│   ├── env_000.monitor.csv
│   └── env_001.monitor.csv
├── checkpoints/             # 모델과 timestep별 VecNormalize 통계
├── evaluation/              # best_model.zip과 당시 VecNormalize 통계
├── videos/                  # 정책 MP4 녹화
└── tensorboard/             # TensorBoard event 파일
```

`runs/`는 생성 데이터이므로 Git에서 추적하지 않습니다.

## 9. 학습된 모델 평가

`final_model.zip`과 같은 run에 `resolved_config.yaml` 및 `vecnormalize.pkl`이
있으면 평가기가 설정과 observation 통계를 자동으로 찾습니다. 체크포인트와
`best_model.zip`도 파일명에 대응하는 통계를 자동으로 사용합니다.

```powershell
python training/evaluate.py `
  ".\runs\ppo_plane\RUN_DIRECTORY\final_model.zip" `
  --episodes 5
```

화면을 렌더링하려면:

```powershell
python training/evaluate.py `
  ".\runs\ppo_plane\RUN_DIRECTORY\final_model.zip" `
  --episodes 5 `
  --render
```

다른 설정 파일을 명시하려면 `--config`를 사용합니다. 정규화 통계를 직접
선택하려면 `--vecnormalize PATH`를 사용합니다.

## 10. 파일 구조

```text
training/
├── train.py                    # SB3 PPO 학습
├── evaluate.py                 # 저장된 모델 평가
├── run_env.py                  # YAML 기반 Gymnasium 실행
├── configs/
│   ├── environment_plane.yaml  # 환경 전체 인수 예제
│   ├── ppo_plane.yaml          # 본 학습
│   └── smoke.yaml              # 짧은 검증
├── callbacks/
│   ├── info_metrics.py         # info → TensorBoard scalar
│   └── video_recorder.py       # iteration 기반 정책 녹화
└── envs/
    └── README.md
```

## 11. 문제 해결

### `ModuleNotFoundError`

Conda 환경과 editable 설치를 확인합니다.

```powershell
conda activate horcrux
pip install -e ".[train]"
```

### CUDA가 인식되지 않음

```powershell
nvidia-smi
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

PyTorch 버전에 `+cpu`가 표시되면 CUDA wheel을 설치해야 합니다.

### 영상이 정지 화면처럼 보임

초기 deterministic 정책은 action이 0에 가까울 수 있습니다.
`video_length`를 늘리거나 초기 확인에만 `deterministic: false`를 사용하세요.

### 본 학습 전 주의사항

결과를 연구 baseline으로 사용하기 전에 `PROJECT.md`에 기록된 환경 종료
플래그와 시딩 관련 알려진 문제를 먼저 확인하세요. 새로운 환경 변경 후에는
항상 smoke 학습을 다시 실행해야 합니다.
