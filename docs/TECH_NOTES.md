# 기술 노트

규칙이 아니라 참고 자료다. 규칙은 `CLAUDE.md`에 있다.
`AGENTS.md`(2026-07, Windows·PowerShell 기준)의 기술 설명을 리눅스 작업 환경에 맞게 옮기고
고쳤다(2026-10-20). 값은 작성 시점 기준이므로, 실험을 고를 때는 해당 run의
`resolved_config.yaml`과 계보의 `TRAINING_HISTORY.txt`를 먼저 확인한다.

## 1. 실행 환경

- 작업 컴퓨터: 리눅스, 셸은 zsh. conda 환경 이름은 `horcrux`(Python 3.11, CUDA PyTorch).
- 파이썬 경로: `/home/bong/anaconda3/envs/horcrux/bin/python`. 셸의 `python`은 PATH에 없을 수 있다.
- 환경 새로 만들기: `bash scripts/setup_conda_env.sh` (옵션 `--cpu`, `--skip-smoke`).
- 학습 실행: `scripts/launch_training.sh <config.yaml> <tag> [train.py 인자...]`
  - `setsid nohup`으로 띄워 셸·세션이 끝나도 살아남는다.
  - 로그는 `<experiment.output_dir>/console_<tag>.log`, PID는 `<tag>.pid`.
  - 화면이 있으면 로그를 보여 주는 터미널 창을 따로 연다. 그 창을 닫아도 학습은 멈추지 않는다.
  - 멈추기: `kill "$(cat <experiment.output_dir>/<tag>.pid)"`.
- TensorBoard: `tensorboard --logdir runs --port 6006`.
- zsh 주의점
  - `$var`는 단어로 나뉘지 않는다. 인자 여러 개는 배열(`args=(--a 1 --b 2); cmd "${args[@]}"`)로 넘긴다.
  - 일치하는 파일이 없는 glob는 오류가 난다(`setopt +o nomatch`로 끈다).
  - `=단어`는 경로 확장된다(`echo =====` 같은 줄은 따옴표로 감싼다).
- 학습 기록: `train.py`는 run 폴더의 `metadata.json`에 커밋 해시, 수정 여부, 변경분 해시를 남기고,
  수정 상태면 `git_diff.patch`를 저장한다. 되살리기는
  `git checkout <git_revision> && git apply <run_dir>/git_diff.patch`.
  2026-08-07 ~ 2026-10-19 사이 run은 해시만 기록돼 실제 코드와 다를 수 있다.

## 2. 학습 구조

- `training/train.py`: YAML 읽기, 병렬 VecEnv, PPO 학습, TensorBoard, 평가, 체크포인트,
  영상, metadata, 모델·통계 저장.
- `training/evaluate.py`: 저장된 정책 평가. 짝이 맞는 정규화 통계를 자동으로 찾는다.
- `training/configs/smoke.yaml`: 실행 경로 확인용(환경 2개, `[64, 64]`). 학습 성능 기준이 아니다.
- `training/callbacks/`: `info_metrics.py`(환경 info 지표 기록), `video_recorder.py`(분리된 렌더 환경에서
  현재 정책 녹화), `vecnormalize.py`(새 best 모델과 함께 통계 저장).
- 병렬 설정은 `sampling.num_envs`, `vec_env: subproc`. `n_steps`는 환경 하나당 값이라 한 rollout은
  `n_steps × num_envs` 샘플이다. 평가·체크포인트 빈도는 전체 환경 스텝 단위로 적고 내부에서 나눈다.
- 평가·분석 도구: `validate_paths.py`(경로 검증 run/compare, 시드 짝지음), `bench_unified_ckpts.py`
  (고정 시드 체크포인트 벤치마크), `eval_expert_transitions.py`, `eval_phase_rules.py`,
  `path_following.py`(경로 추종 시연·커맨더), `distill_experts.py`(전문가 증류).

## 3. 종료와 시간 제한

`plane_v3.py`는 Gymnasium 의미대로 돌려준다. 로봇 실패는 `terminated=True`, 내부 6,000스텝 제한은
`truncated=True`. PPO는 truncation을 부트스트랩하므로 두 값을 바꾸지 않는다.

## 4. 관측 정규화

- SB3 `VecNormalize`로 한다. 환경은 원래 센서 관측을 그대로 돌려준다.
- 설정: `norm_obs=True`, `norm_reward=False`, `clip_obs: 10.0`, `epsilon: 1e-8`.
  `clip_obs`는 표준화 뒤에 걸리므로 약 10 표준편차를 뜻한다.
- 차원별 이동 평균·분산을 쓴다. `observation_space`의 low/high는 쓰지 않는다.
- 기본 관측 공간은 `Box(-inf, inf, shape=(97,))`.
- 평가는 통계를 고정(`training=False`)해서 쓴다. 영상 추론은 현재 학습 통계로 원래 관측을 정규화한다.
- 짝: `final_model.zip`·`interrupted_model.zip` ↔ `vecnormalize.pkl`,
  `evaluation/best_model.zip` ↔ `evaluation/best_model_vecnormalize.pkl`,
  `checkpoints/ppo_plane_<N>_steps.zip` ↔ `checkpoints/ppo_plane_vecnormalize_<N>_steps.pkl`.
- 명령 방향을 바꿀 때 통계를 그대로 재사용하지 않는다. 고정 명령으로 학습한 정책은 명령 관측의
  분산이 거의 0이라, 다른 명령을 주면 정규화 값이 크게 튄다(전진→왼쪽 전이 때 마지막 명령 3차원을
  초기화해야 했다. 경로 추종 시연의 낡은 관측 결함도 같은 원인으로 ±10에 포화됐다).

## 5. 행동 변환

- 물리 행동 공간은 `Box(0, 2.7, shape=(14,))`(motor 액추에이터 토크 진폭).
- `horcrux_env/wrappers/normalize_action.py`가 정책 공간 `[-1, 1]`을 선형으로 옮긴다
  (−1→0, 0→1.35, +1→2.7). YAML `action_normalization.enabled: true`.
- 학습, EvalCallback, 단독 평가, 영상 모두 같은 래퍼를 쓴다.
- 마지막 환경 호출에만 `tanh`를 붙이지 않는다. 그러려면 PPO 분포의 log-prob 변환도 함께 고쳐야 한다.

## 6. 기본 PPO 설정과 이어 학습

- 범용 기준 `training/configs/ppo_plane.yaml`: lr 3e-4, γ 0.95, `n_steps` 512, batch 512, epoch 5,
  `net_arch [512]×5`, tanh, 7,864,320 스텝. 최신·최선 정책의 설정이 아니다.
- 이어 학습
  - `resume`에 정책 zip과 짝이 맞는 pkl을 함께 적는다.
  - `training.total_timesteps`는 추가 스텝 수다. `reset_num_timesteps=False`라 TensorBoard·평가·체크포인트
    스텝 표기는 누적이다.
  - YAML의 lr·epoch·`target_kl` 덮어쓰기가 불러온 모델에 실제로 적용됐는지 로그로 확인한다.
    예약된(schedule) lr은 이어 학습에서 지원하지 않는다.
- 이미 학습된 정책의 보수적 이어 학습 값(왼쪽 계보 Stage 3 실증): lr 5e-5, epoch 2, `target_kl` 0.04.
  그 계보의 근거이지 모든 정책의 기본값은 아니다.
- 사용자 네트워크 `[512]×5`와 γ는 말없이 바꾸지 않는다. γ 0.95는 유효 지평이 짧다는 지적이 있었으나
  적용하지 않았다.

## 7. 평가·체크포인트 빈도

기준 YAML의 `eval_freq: 10000`, `save_freq: 10000`은 7.86M 스텝에서 평가·체크포인트 약 786회를 만든다.
예전 전체 run은 체크포인트 786개로 약 19.45 GB를 썼고, 평가만으로 최대 2,358만 환경 스텝이 들 수 있다.
긴 run에서는 `eval_freq: 250000`, `n_eval_episodes: 3`, `save_freq: 500000`,
`record_every_iterations: 200`이 실증됐다. 기존 YAML을 바꾸기 전에는 사용자에게 확인한다.

## 8. 알려진 함정

- 실행이 끝났다고 학습이 된 것은 아니다. 2026-07 스모크 run(`runs/smoke_action_normalization/…`)은
  저장·평가 경로는 정상이었지만 x 속도 0.018→0.0009, KL 7e-6, std 0.999로 학습되지 않았다.
- 현재 보상은 제자리에서 건강하게 버티기만 해도 약 2×6,000 = 12,000을 준다. 지역 최적 가능성이
  지적됐으나 재설계하지 않았다.
- `plane_v3`의 `is_terminated` 이중 호출 때문에 종료 스텝의 낙상 페널티가 항상 0이다. 기존 전문가는
  낙상 벌점을 받은 적이 없다. `plane_v3`는 고정이라 고치지 않았다(인계 환경에서만 보정).
- `getMvec(k)`는 역재생 gait면 열 −k를 쓴다(위상 정렬 시 k = −col).
- `gym.make`는 환경 kwarg `max_episode_steps`를 가로챈다. 다른 이름을 쓴다.
- 결정론 평가에서 같은 시드·같은 시작 상태의 에피소드는 거의 똑같다. 강건성 근거가 아니다.
- MuJoCo가 시뮬레이션 발산(QACC가 NaN·Inf)을 만나면 저장소 루트의 `MUJOCO_LOG.TXT`에 경고를 덧붙인다. 2026-07-27~08-11 리부탈 스케일링 실험(관절 수를 바꾼 환경)에서 490번 났고 그 뒤로는 없다. 이 파일은 git에서 뺐다(2026-10-20). 새 줄이 생기면 그 run의 물리 설정을 의심한다.
- `plane_v3`의 reset 잡음은 0이라 시드만 바꾸면 시작 상태가 같다(명령 추첨만 바뀐다).
- TensorBoard의 `env_switch/fail_to_XX` 번호는 `gait_provider.VALIDATED_COMMANDS` 순서다:
  forward, left, right, diag_fl, diag_fr, backward, diag_bl, diag_br, ccw, cw.

## 9. 렌더링

- 영상 환경은 현재 관측 통계와 행동 래퍼를 함께 쓴다. `video_length` 300 프레임.
- 리소스 XML에서 천장 카메라 FOV를 넓히고 바닥을 밝게 했다.
- 영상 렌더는 gymnasium `rgb_array` 뷰어를 쓴다. `MUJOCO_GL=egl` 강제는 이 컴퓨터에서 오류가 났다.
