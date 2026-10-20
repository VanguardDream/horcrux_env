# Claude Code 변경 이력

이 파일은 Claude Code가 이 레포지토리에 가한 모든 코드 변경사항을 기록합니다.
각 항목은 사용자의 요청 내용(Context), 변경된 파일, 변경 내용 요약을 포함합니다.

---

## 2026-01-16 — MovingAverageFilter reset 메서드 추가

**커밋:** `a58eb57`
**요청:** `MovingAverageFilter` 클래스들에 동적으로 윈도우 크기를 조정할 수 있도록 `reset()` 메서드를 추가해달라는 요청.
**파일:** `horcrux_env/envs/plane_v3.py`
**변경:** `MovingAverageFilter` 및 관련 클래스에 `reset()` 메서드 추가. (56 insertions, 55 deletions)

---

## 2026-03-30 — CLAUDE_CHANGES.md 생성

**커밋:** (미커밋)
**요청:** 프로젝트를 지속적으로 이어가기 위해 Claude가 생성하는 모든 코드 변경점과 요청 Context를 담는 `.md` 파일을 레포지토리 최상단에 추가해달라는 요청.
**파일:** `CLAUDE_CHANGES.md` (신규 생성)
**변경:** 변경 이력 추적 파일 생성. 날짜, 커밋 해시, 요청 내용, 변경 파일, 변경 요약을 항목별로 기록하는 형식 정의.

---

## 2026-03-30 — PROJECT.md 생성

**커밋:** (미커밋)
**요청:** 프로젝트의 중요성과 향후 개발 방향을 기록하고, Context가 끊겨도 개발 일관성을 유지할 수 있도록 이정표 역할을 하는 중심 전략 문서를 추가해달라는 요청. 변경 이력(CLAUDE_CHANGES.md)과는 별도 파일로 분리.
**파일:** `PROJECT.md` (신규 생성)
**변경:** 프로젝트 정체성(Why), 현재 구현 상태(v0.0.1), 핵심 설계 원칙 5가지, 4단계 개발 로드맵(기반완성→커리큘럼→Sim-to-Real→패키지성숙), 미결 설계 질문, 용어 정의를 포함하는 전략 문서 작성.

---

## 2026-07-22 — conda 환경 초기 설정 스크립트 추가

**커밋:** (미커밋)
**요청:** 학습 PC를 기존 Windows 머신에서 현재 컴퓨터(zsh, NVIDIA GPU)로 이전. 기존 `horcrux` conda 환경을 삭제 후 재생성하고, 의존성 설치부터 smoke 학습까지 초기 설정을 자동화해달라는 요청.
**파일:** `scripts/setup_conda_env.sh` (신규 생성)
**변경:** 환경 삭제→재생성(Python 3.11)→`pip install -e ".[train]"`→CUDA torch 교체(기본 2.13.0+cu132, 환경변수로 변경 가능)→설치 검증→run_env 200스텝 확인→smoke 학습 순으로 수행하는 스크립트 작성. `--cpu`, `--skip-smoke` 옵션 지원.

---

## 2026-07-22 — setup_conda_env.sh Linux CUDA wheel 설치 방식 수정

**커밋:** (미커밋)
**요청:** `setup_conda_env.sh` 스크립트의 유효성을 검증하고 실행해달라는 요청. 검증 중 Linux에서 깨질 수 있는 설치 옵션 발견.
**파일:** `scripts/setup_conda_env.sh`
**변경:** CUDA torch 교체 시 `--no-deps` 제거. Windows wheel과 달리 Linux cu132 wheel은 CUDA 라이브러리를 내장하지 않고 `cuda-toolkit==13.2.1`, `nvidia-cudnn-cu13`, `nvidia-nccl-cu13`, `triton` 등을 의존성으로 선언하므로(wheel 메타데이터로 확인), `--no-deps` 설치 시 라이브러리 누락/버전 불일치로 `import torch`가 실패할 수 있음. 의존성 해석을 허용하고 PyTorch 인덱스에 없는 패키지는 PyPI에서 받도록 `--extra-index-url https://pypi.org/simple` 추가.

---

## 2026-07-22 — 우측(-Y) 게걸음 정책 학습 준비

**커밋:** (미커밋)
**요청:** 오른쪽 게걸음으로 이동하는 정책을 학습하기 위해 추천 gait 파라미터를 설정하고 학습을 준비해달라는 요청.
**파일:** `training/configs/ppo_plane_right_from_scratch_long.yaml` (신규), `policies/path_tracking/right/TRAINING_HISTORY.txt` (신규)
**변경:** 좌측 gait(delta=45)의 x-z 평면 거울상 분석으로 우측 gait `delta=225` 도출 (lateral 관절 부호 반전 = delta+180; delta=-45는 거울상이 아님을 MotionMatrix 수치 검증으로 확인 — delta=225는 dorsal 100% 일치/lateral 100% 부호 반전, delta=-45는 lateral 일치율 50%). `joy_input=[0,-1,0]`, 보상/PPO 설정은 검증된 좌측 Stage 1 레시피를 그대로 미러링한 학습 YAML 작성. 우측 gait 파라미터로 환경 200스텝 headless 구동 검증 완료. 우측 정책 이력 원장 생성. 학습 실행은 하지 않음(사용자 명시 요청 대기).

---

## 2026-07-22 — 후진(-X) gait 파라미터 도출 및 학습 준비

**커밋:** (미커밋)
**요청:** 우측 학습이 도는 동안 남는 컴퓨팅 자원으로 뒤로 가는(후진) gait 학습을 병행하고자, 후진 gait 파라미터를 찾아달라는 요청.
**파일:** `training/configs/ppo_plane_backward_from_scratch_long.yaml` (신규), `policies/path_tracking/backward/TRAINING_HISTORY.txt` (신규)
**변경:** 좌/우측과 달리 후진은 해석적 변환이 불가능함을 확인(몸체 머리-꼬리 비대칭으로 x축 거울상이 파라미터 공간에 없음). GaitV2 reverse 플래그는 MotionMatrix 시간 역재생이 정확함을 수치 검증했으나 bang-bang 토크+마찰의 비가역성으로 실변위가 거의 0이라 기각. 공간 위상 부호 (±30,±30) × delta 그리드 개루프 실측(진폭 1.35, 방법은 좌 +85.7도/우 -87.3도 재현으로 교차검증)으로 후진 포켓 (30,-30,40,40,340~346)을 발견, 1000/2000/4000/6000 스텝 전부 순 dX<0인 유일 지점 **delta=345** 채택 → `gait_params=[30,-30,40,40,345]`, `joy_input=[-1,0,0]`. 보상/PPO 설정은 우측 Stage 1과 동일하게 좌측 검증 레시피 미러링. 실제 학습 kwargs로 headless 200스텝 구동 검증 완료. 학습 실행은 하지 않음(사용자 명시 요청 대기).

---

## 2026-07-22 — 분리 실행 학습 런처 추가 및 후진 Stage 1 학습 시작

**커밋:** (미커밋)
**요청:** 새로 학습을 시작하고, 완료 후 로그의 KL 등을 근거로 하이퍼파라미터를 바꿔 3회 추가 학습을 진행해달라는 요청. 단 하이퍼파라미터는 "정책에 큰 영향을 주지 않고 학습 성능에만 영향을 주는" 것만 변경. 또한 Claude 세션과 무관하게 동작하고 사용자도 로그를 실시간으로 볼 수 있도록 별도 터미널에서 학습을 띄워달라는 요청.
**파일:** `scripts/launch_training.sh` (신규 생성)
**변경:** `setsid nohup`으로 학습 프로세스를 호출 셸(Claude 세션 포함)에서 완전히 분리해 실행하고, 별도 gnome-terminal 창을 띄워 콘솔 로그를 `tail -f`로 보여주는 런처 작성. 뷰어 창은 관찰 전용이라 닫아도 학습은 계속된다. YAML의 `experiment.output_dir`를 읽어 `console_<tag>.log`와 `<tag>.pid`를 그 아래에 기록하고, 같은 태그의 런이 살아있으면 중복 실행을 거부한다. 이 런처로 후진 Stage 1 baseline 학습(`ppo_plane_backward_from_scratch_long.yaml`, 태그 `run1_baseline`)을 시작. 대상은 사용자 선택(우측 대신 후진, 3회 실험은 순차 실행).

---

## 2026-07-23 — learning_rate 스케줄 지원 및 후진 하이퍼파라미터 실험 3종 추가

**커밋:** (미커밋)
**요청:** (앞 항목과 동일 요청의 후속) 후진 baseline 학습 완주 후 로그의 KL 등을 분석해 하이퍼파라미터를 바꿔 3회 순차 학습.
**파일:** `training/train.py`, `training/configs/ppo_plane_backward_run2_epochs10.yaml` (신규), `training/configs/ppo_plane_backward_run3_lrdecay.yaml` (신규), `training/configs/ppo_plane_backward_run4_bigrollout.yaml` (신규)
**변경:** Run 1(baseline) 로그 분석 결과 — approx_kl이 1.4e-4 → 4.3e-2로 단조 증가하는 동안 정책 action std가 1.00 → 0.569으로 축소. 가우시안 KL은 (Δμ)²/σ²이므로 고정 lr에서도 후반으로 갈수록 스텝의 KL 비용이 커지는 구조. 초반(0~10M)은 approx_kl이 target_kl의 1/100, clip_fraction=0으로 트러스트 리전이 완전히 유휴 상태였고, 후반(20M+)은 반대로 `Early stopping ... max kl`이 172회 발생(대부분 epoch step 0~1)해 롤아웃이 통째로 버려지며 평가 리턴이 ~1,230에서 평탄화.

`train.py`에 `build_algorithm_kwargs()` 추가 — `learning_rate`를 float 대신 매핑(`schedule: linear`, `initial`, `final`)으로 줄 수 있게 하여 SB3의 `get_linear_fn`으로 progress_remaining 기반 선형 감쇠 스케줄을 구성. resume 경로는 스케줄이 재시작돼 의미가 깨지므로 `validate_config`에서 명시적으로 거부. 스모크 테스트로 2 iteration 중 2번째에 lr=1.5e-4(=3e-4×0.5) 확인.

실험 3종은 **최적화 하이퍼파라미터만** 변경(사용자 제약: 정책이 학습하는 목적함수에 영향을 주지 않을 것). 환경/보상 가중치/gait/joy_input/gamma/net_arch/activation/normalization/seed는 baseline과 동일함을 주석 제거 diff로 확인:
  - run2 `n_epochs: 2 → 10` (초반 언더피팅 해소, target_kl이 후반 자동 스로틀)
  - run3 `learning_rate: 1e-4 상수 → linear 3e-4 → 0` (std 축소 속도에 스텝 크기를 정합)
  - run4 `n_steps: 512 → 2048`, `batch_size: 512 → 1024`, `n_epochs: 2 → 4` (업데이트당 샘플 4배로 그래디언트 분산 감소, total_timesteps는 롤아웃 정수배인 28,409,856으로 조정)

Run 1 결과: 28,413,952 스텝 / 20,562초(5.7h, 1381 fps) 완주, 평가 리턴 -6,757 → **+1,265 @ 28.1M**, 최종 x_velocity -0.401(후진 방향 일치), direction_similarity 0.762, explained_variance 0.997. 단 `ep_len_mean`이 전 구간 ~50에 고정 — 약 20스텝 만에 unhealthy 진입 후 미회복. 환경/보상 측 이슈로 이번 실험군에서는 미변경, 기록만 유지.

---

## 2026-07-23 — 우측 Stage 1 학습 완주 및 이력 기록

**커밋:** (미커밋)
**요청:** 우측 게걸음 학습을 시작하고 완료 시 보고해달라는 요청의 후속. (이후 3회 하이퍼파라미터 실험은 사용자 선택으로 후진 gait에 적용되어 별도 진행 중.)
**파일:** `policies/path_tracking/right/TRAINING_HISTORY.txt`
**변경:** 우측 Stage 1(run 20260722-200128-406969) 완주 결과 기록 — 최고 평가 리턴 162,525.5 @ 28.3M, y_velocity -0.458, direction_similarity 0.754, abs_com_yaw 9.4도(게걸음 확인), 말기 approx_kl 0.0038/clip 0.019(트러스트 리전 유휴). 좌측 Stage 1과 거울상 수준으로 유사한 학습 곡선 확인. Stage 2 권장값(n_epochs 2→3) 기록, 실행은 대기. 세션 종료로 중단됐던 첫 시도(~3.75M 스텝)는 계보 제외로 명시.

---

## 2026-07-23 — Run 2 완주 결과 반영, Run 3/4를 Run 2 기준 단일변수 델타로 재설계

**커밋:** (미커밋)
**요청:** (동일 요청의 후속) 3회 실험을 순차 실행하되 각 실행 결과를 보고 다음을 조정.
**파일:** `training/configs/ppo_plane_backward_run3_lrdecay.yaml`, `training/configs/ppo_plane_backward_run4_bigrollout.yaml`
**변경:** Run 2(`n_epochs 2→10`)가 baseline을 명확히 이김 — 최고 평가 리턴 **1,695 @ 23.0M vs 1,265**, 최종 10회 평균 **1,492 vs 1,235**, 그리고 baseline의 *최종* 점수를 **4.1M 스텝만에** 통과. 벽시계 시간도 17,035초로 baseline 20,562초보다 짧았다(우측 런 종료로 CPU 여유가 생겨 fps 1381→1667).

따라서 Run 3/4의 기준선을 run 1에서 **run 2로 변경**하고, 각각 run 2로부터 **단일 변수만** 바꾸도록 재설계(주석 제거 diff로 확인). Run 2가 해결하지 못한 것은 트러스트 리전 포화 — 8M 이후 approx_kl이 target_kl 0.04 대비 0.03~0.07로 상시 포화, clip_fraction 0.3~0.4, 조기 중단 **4,843회**(baseline 172회), 평가 리턴은 마지막 20M 구간에서 1,237~1,695 사이 무추세 진동. 이 정체의 두 가지 경합 가설을 각각 검증:
  - run3 = run2 + `learning_rate: 1e-4 상수 → linear 1e-4 → 0` (가설: 트러스트 리전이 구속조건 → 스텝 크기를 std 축소에 맞춰 감쇠). `n_epochs`는 10으로 채택. 초기 lr을 3e-4에서 1e-4로 낮춘 것은 run 2가 이미 초반부터 KL 포화 상태라 증량 여지가 없기 때문.
  - run4 = run2 + `n_steps: 512 → 2048`, `batch_size: 512 → 1024` (가설: KL 예산이 그래디언트 노이즈에 소모 → 업데이트당 샘플 4,096 → 16,384). `n_epochs`는 10 유지.

**보고 시 밝힌 계획과의 차이:** 직전 보고에서는 run3를 "n_epochs 2 + lr 3e-4→0", run4를 "n_epochs 4 + 큰 롤아웃"으로 예고했으나, 사용자가 순차 실행을 택한 취지(앞 결과를 다음에 반영)에 따라 위와 같이 조정.

---

## 2026-07-23 — 우측 Stage 2 연속 학습 시작 (n_epochs 2→3)

**커밋:** (미커밋)
**요청:** 우측 3회 학습을 이어서 진행하되, 각 stage 시작 시 이전 결과 기반으로 하이퍼파라미터를 튜닝하고, 사용자가 로그를 볼 수 있게 터미널 창을 띄워 학습해달라는 요청.
**파일:** `training/configs/ppo_plane_right_continue_stage2.yaml` (신규)
**변경:** Stage 1 final(누적 28.4M) + vecnormalize.pkl에서 resume하는 Stage 2 YAML 작성. 튜닝 근거: Stage 1 말기 approx_kl 0.0038(target의 1/10)·clip 0.019·조기중단 2회로 트러스트 리전 유휴 → `n_epochs` 2→3 (동일 상황에서 좌측 Stage 2가 리턴 173K→259K를 달성한 검증 레시피; 후진 run2의 n_epochs 10은 KL 포화 레짐이라 성숙 정책 연속 학습에는 미채택). lr 1e-4/target_kl 0.04/환경/gait/보상/네트워크 동결. `scripts/launch_training.sh`(태그 stage2)로 분리 실행 + gnome-terminal 뷰어 창 오픈. 시작 로그에서 resume 모델·누적 timestep 28,413,952·optimizer 오버라이드 적용 확인. 추가 28.4M 스텝, 목표 누적 56.8M.

---

## 2026-07-23 — 후진 Run 3(lr 선형감쇠) 완주, Run 4 시작

**커밋:** (미커밋)
**요청:** (동일 요청의 후속) 3회 실험 순차 실행.
**파일:** (config 변경 없음 — 실행 및 결과 기록)
**변경:** Run 3(`run2 + learning_rate linear 1e-4 → 0`) 28,413,952 스텝 완주(17,078초, 1663 fps). **최고 평가 리턴 1,735 @ 28.1M**로 run2의 1,695를 넘어 신기록. 최종 10회 평균 **1,654 vs run2 1,492**, 최종 30회 표준편차 **42 vs run2 120**으로 안정성이 크게 개선. 최종 x_velocity -0.493, direction_similarity 0.792.

트러스트 리전 가설은 **부분적으로만** 성립. lr을 9.3e-5 → 2.1e-5로 4.5배 줄였는데도 중후반 approx_kl은 0.037~0.059로 여전히 target_kl 0.04를 초과했다 — std가 동시에 0.911 → 0.258로 3.5배 축소되어 (Δμ)²/σ²의 분자·분모가 상쇄되었기 때문. 다만 조기 중단은 4,843 → 1,919회로 감소했고, 감쇠 덕분에 run2처럼 후반에 무너지지 않고(run2는 18~20M에서 1,475→1,390) 끝까지 단조 개선을 유지했다. 최종 구간에서 lr 1.44e-8 / approx_kl 5.5e-6 / clip_fraction 0 / entropy_loss +0.749로 정책이 의도대로 결정론적 수렴.

이어서 Run 4(`run2 + n_steps 2048 / batch_size 1024`, 그래디언트 노이즈 가설) 시작. 동 시각 별도 세션의 우측 Stage 2 학습(PID 457438)이 병행 중이라 16 env / 32코어로 경합하나 여유 범위.

세 런 공통으로 `ep_len_mean`이 ~50에 고정되어 평가 리턴이 1,700 부근에서 막히는 천장이 관찰됨. 최적화 하이퍼파라미터로 넘을 수 있는 한계에 근접한 것으로 보이며, 환경/보상 측(unhealthy 조기 종료) 조정이 다음 과제.

---

## 2026-07-23 — 후진 Stage 1 하이퍼파라미터 실험 4런 완료 및 이력 정리

**커밋:** (미커밋)
**요청:** (동일 요청의 완결) baseline 1회 + 하이퍼파라미터 변형 3회 순차 학습 후 결과 보고.
**파일:** `policies/path_tracking/backward/TRAINING_HISTORY.txt`
**변경:** 4런 전부 28.4M 스텝 완주. 결과 및 분석을 이력 원장에 기록하고 권장 정책을 run 3로 확정.

| 런 | 델타 | 최고리턴 | 최종10평균 | 말기표준편차 | n_updates | 조기중단 |
|---|---|---|---|---|---|---|
| 1 baseline | lr 1e-4 상수, n_epochs 2 | 1,265 | 1,235 | 16 | 13,864 | 172 |
| 2 | n_epochs 2→10 | 1,695 | 1,492 | 120 | 32,377 | 4,843 |
| **3** | **run2 + lr linear 1e-4→0** | **1,735** | **1,654** | **42** | 62,097 | 1,919 |
| 4 | run2 + n_steps 2048/batch 1024 | 1,495 | 1,414 | 40 | 10,710 | 841 |

**권장: run 3** (`runs/ppo_plane_backward_run3_lrdecay/20260723-064255-313390_.../final_model.zip`). baseline 대비 최고 리턴 +37%, 최종 10회 평균 +34%, x_velocity -0.493, direction_similarity 0.792, abs_com_yaw 3.5도.

결론: (1) 초반 언더피팅이 지배적 병목 — `n_epochs 2→10` 단일 변경으로 +34%, baseline이 28.4M에 도달한 점수를 4.1M만에 통과(샘플 효율 ~7배). (2) lr 선형감쇠의 이득은 "더 높이"가 아니라 "안 무너짐" — run2가 18~20M에서 1,625→1,390으로 붕괴하고 말기 표준편차 120인 반면 run3는 단조 상승, 표준편차 42. (3) 트러스트 리전 가설은 절반만 성립 — lr을 4.5배 줄여도 std가 3.5배 동시 축소되어 (Δμ)²/σ²이 상쇄, approx_kl은 계속 target 0.04 초과. (4) 큰 롤아웃(run 4)은 기각 — 노이즈 감소 효과는 실측(조기중단 841회로 최소, KL 포화 최지연)됐으나 정책 업데이트 횟수 1/4 손실을 보상 못 함. **이 환경에서는 업데이트 횟수 > 업데이트 품질.** (5) 벽시계 비용은 n_epochs 10에서 거의 없음 — run2/3/4 fps가 1,663~1,672로 동일(target_kl이 대부분 epoch를 조기 중단). run1의 낮은 fps는 우측 Stage 1과의 CPU 경합 탓.

**미해결:** `ep_len_mean`이 4런 전부 예외 없이 ~50(약 20스텝 만에 unhealthy 진입 후 미회복). 1,700 부근 공통 천장은 최적화 파라미터가 아닌 환경/보상 측 제약으로 판단. 사용자 제약상 미변경, 다음 과제로 기록. 또한 좌/우측(에피소드 6,000스텝)과는 리턴 스케일이 3자릿수 달라 직접 비교 불가하며 x_velocity / direction_similarity로 비교해야 함을 명시(후진 run3 -0.493/0.792 vs 좌측 Stage 1 0.485/0.782로 대등).

---

## 2026-07-23 — 우측 Stage 2 완주(+40%), Stage 3 보수화 연속 학습 시작

**커밋:** (미커밋)
**요청:** (우측 3회 학습 요청의 후속) stage 종료 시 결과를 판단해 튜닝 후 다음 학습을 자동 진행.
**파일:** `training/configs/ppo_plane_right_continue_stage3.yaml` (신규), `policies/path_tracking/right/TRAINING_HISTORY.txt`
**변경:** Stage 2(run 20260723-103627) 완주 — 최고 평가 리턴 226,875 @ 56.2M(Stage 1 대비 +39.6%), y_velocity -0.566, direction_similarity 0.846, abs_com_yaw 3.9도. 단 말기 approx_kl 0.047~0.063으로 target 0.04 초과 포화, clip 0.415, 조기중단 731회(후반 집중), std 0.435, 평가 리턴 말미 정체 — 좌측 Stage 2와 동일 진단. 이에 Stage 3는 좌측 검증 보수화 처방 lr 1e-4→5e-5, n_epochs 3→2(target_kl 유지)로 Stage 2 final에서 resume하는 YAML 작성 후 launch_training.sh(태그 stage3, 뷰어 창 포함)로 시작. 시작 로그에서 누적 56,827,904 재개 및 오버라이드 적용 확인. 이력 원장에 Stage 2 결과와 Stage 3 계획 기록.

---

## 2026-07-23 — GaitV2 reverse 플래그 gait 학습 config 추가 및 학습 시작

**커밋:** (미커밋)
**요청:** 후진 학습이 잘 진행되지 않는 것 같으니 `gait_params: [30, 30, 40, 40, 0, -1]`로 설정해 학습을 진행해달라는 요청. 더불어 기존 config와 이름이 비슷해 헷갈리지 않도록 해달라는 요청.
**파일:** `training/configs/ppo_plane_gaitrev_delta0.yaml` (신규 생성)
**변경:** 6번째 원소 `-1`은 GaitV2 reverse 플래그로, `GaitV2.getMvec`에서 인덱스 k를 음수화해 MotionMatrix를 시간 역재생한다(코드 확인). 공간/시간 파라미터는 검증된 전진 gait와 동일(30,30,40,40)하고 delta만 23→0이며 시간이 역행한다.

**이름 구분:** 기존 4개 `ppo_plane_backward_*` config는 전부 개루프로 도출한 `[30,-30,40,40,345]` gait를 공유하는 하나의 비교 가능한 실험군이다. 이번 런은 gait 생성 메커니즘 자체가 달라 그 실험군과 수치 비교가 불가하므로 `backward` 접두어를 쓰지 않고 `ppo_plane_gaitrev_delta0`로 명명(experiment.name, output_dir 동일). config 상단에도 명명 근거를 기록.

**개루프 사전 측정(진폭 1.35, 좌 +85.7도/우 -87.3도 재현으로 교차검증된 동일 방법):** 이 gait의 순 dX는 1000/2000/4000/6000 스텝 전부 **양수**(+0.27/+0.72/+0.33/+0.48)로 후진이 아니라 미세 전진이며, 이동량(0.4~0.8)이 전진 prior(2.4~5.5)나 기존 후진 prior(1.7~3.8) 대비 거의 정지 수준이다. 이는 앞서 기각했던 `[30,30,40,40,23,-1]`(0.04~0.62)과 동일한 양상으로, MotionMatrix 시간 역재생은 정확하나 bang-bang 토크+지면 마찰이 비가역이라 순변위가 상쇄되기 때문이다. 즉 **prior가 후진이 아닌 거의 0에서 출발**한다. 검증된 전진 gait도 개루프에서 약 49도 어긋났음에도 RL이 학습에 성공한 전례가 있어 학습 자체는 가능할 수 있으나, 보상이 prior의 역할까지 떠맡아야 하므로 초반 진행이 느리고 천장이 낮을 가능성이 있음을 config에 명시.

PPO 설정은 4런 비교 우승 레시피(run 3: `n_epochs 10` + `learning_rate linear 1e-4 → 0`)를 채택, 나머지는 backward 계열과 동일하게 유지해 gait만이 유일한 환경 측 차이가 되도록 했다. 스모크 테스트 통과 후 `scripts/launch_training.sh`로 태그 `gaitrev_delta0` 학습 시작(PID 664162, 28,413,952 스텝).

---

---

## 2026-07-23 — 우측 Stage 3 완주, 3단계 학습 캠페인 종료

**커밋:** (미커밋)
**요청:** (우측 3회 학습 요청의 완결) Stage 3 종료 후 종합 보고.
**파일:** `policies/path_tracking/right/TRAINING_HISTORY.txt`
**변경:** Stage 3(run 20260723-161607, lr 5e-5/n_epochs 2) 완주 — 최고 평가 리턴 244,043 @ 81.3M(Stage 2 대비 +7.6%), y_velocity -0.600, direction_similarity 0.865, abs_com_yaw 3.2도, explained_variance 0.900. 조기중단 731→481회로 완화됐으나 말기 KL 0.043~0.063으로 target 상회 지속 — 추가 stage 시 lr 2.5e-5 재보수화를 후보로 기록. 대표 우측 정책을 Stage 3 evaluation/best 조합으로 갱신하고 계보(01→02→03)와 확인 명령을 원장에 기록. 3회 학습 요청 완료, 추가 학습은 실행하지 않음.

## 2026-07-24 — gaitrev_delta0 학습 완주: ep_len 천장 해결, 후진 권장 정책 교체

**커밋:** (미커밋)
**요청:** (앞 항목과 동일 요청의 결과) `gait_params: [30, 30, 40, 40, 0, -1]` 학습.
**파일:** `policies/path_tracking/backward/TRAINING_HISTORY.txt`
**변경:** 28,413,952 스텝 완주(24,461초, 1161 fps). **기존 후진 계열 4런 전부를 막고 있던 `ep_len ~50` 천장이 이 gait에서 완전히 사라졌다.**

| | ep_len | 최고리턴 | 최종10평균 | per-step | x_vel | dir_sim |
|---|---:|---:|---:|---:|---:|---:|
| bwd 계열 최고 (run 3) | 51 | 1,735 | 1,654 | 32.6 | -0.493 | 0.792 |
| **gaitrev_delta0** | **6,000** | **199,592** | **198,699** | 33.1 | **-0.529** | **0.835** |

`ep_len`이 첫 평가(100K)부터 끝까지 6,000이다 — 이 gait에서는 로봇이 애초에 unhealthy에 빠지지 않는다. 리턴 100배 차이는 대부분 에피소드 길이 차이이며 스텝당 보상은 33.1 vs 32.6으로 동등하다. 실질 개선은 "스텝당 더 잘한다"가 아니라 **"안 넘어지고 120배 오래 간다"**. abs_com_yaw 4.45도로 몸체 전진 자세를 유지한 진짜 후진이다. 권장 후진 정책을 run 3에서 gaitrev_delta0로 교체.

**사전 예측 정정:** 학습 시작 전 개루프 측정(순 dX 전 구간 양수, 이동량 0.4~0.8)을 근거로 "prior가 후진이 아니므로 초반이 느리고 천장이 낮을 수 있다"고 예측했으나 **틀렸다.** 측정치는 맞았고 추론이 틀렸다. 원인은 개루프 변위 크기를 prior 품질의 대리 지표로 삼은 것 — `[30,-30,40,40,345]`의 큰 개루프 변위는 로봇을 불안정하게 만드는 동작에서 나왔고, 그 불안정성이 ~20스텝 만의 unhealthy 진입으로 이어져 에피소드 길이 천장을 만들었다. reverse 플래그 gait의 "거의 0인 변위"는 약한 prior가 아니라 **안정적인 prior**였다. 향후 gait 도출 시 개루프 스캔에 **자세 안정성 지표를 반드시 포함**해야 함을 이력 원장 6절에 기록.

**부수 결과:** 이제 좌/우측과 직접 비교 가능하다(셋 다 ep_len 6,000). 좌측 Stage 1 173,122 / dir_sim 0.782, 우측 162,525 / 0.754 대비 후진 gaitrev 199,592 / 0.835로 **세 방향 중 가장 좋다.** 기존 `ppo_plane_backward_*` 4런은 하이퍼파라미터 비교(KL 진단 결론)로서는 유효하나 후진 정책 계보로는 폐기 대상으로 명시.

---

## 2026-07-27 — 머지 커밋에 포함된 충돌 마커 해결 (plane_v3.py, README.md)

**커밋:** (미커밋)
**요청:** GD 대조군 전진 학습 요청 처리 중 발견 — 머지 커밋 `b1970c0`이 `<<<<<<<`/`=======`/`>>>>>>>` 충돌 마커를 그대로 포함한 채 커밋되어 `import horcrux_env` 자체가 SyntaxError로 실패하는 상태였음.
**파일:** `horcrux_env/envs/plane_v3.py`, `README.md`
**변경:** 양쪽 부모(987761d GD 대조군 커밋 vs c3ad6d8 WS 커밋)를 비교한 결과, WS 쪽은 CRLF 줄바꿈의 리팩토링 이전 구버전이고 고유 내용이 전혀 없음을 확인. 두 파일 모두 987761d 버전으로 해결(바이트 단위 일치 검증 완료). `plane-v0`(97차원)과 `plane-direct-torque-v0`(83차원) 모두 스모크 테스트 통과.

---

## 2026-07-27 — GD 대조군(direct torque) 전진 정책 5단계 학습 파이프라인 구축 및 시작

**커밋:** (미커밋)
**요청:** Gait Decomposition 대조군 학습 시작. 먼저 전진 정책부터, `policies/path_tracking/forward`의 기존 GD 전진 정책과 최대한 공정하게 비교할 수 있도록 이미 진행된 전진 학습 yaml과 같은 파라미터로 학습 진행 요청.
**파일:** `training/configs/ppo_plane_dt_forward_stage{1..5}.yaml` (신규), `scripts/run_dt_forward_pipeline.sh` (신규)
**변경:** GD 전진 정책 계보(01→05, 누적 ~47.6M 스텝)를 단계별로 정확히 미러링하는 5개 설정 작성. 환경만 `plane-direct-torque-v0`(torque ±2.7, 관측 83차원)로 교체하고 나머지(seed 42, joy [1,0,0], 8 SubprocVecEnv, VecNormalize, action normalization, [512×5] tanh, 각 단계의 lr/epochs/target_kl/timestep 예산, 평가/체크포인트/비디오 주기)는 전부 동일. 단계 전환도 GD와 동일하게 stage1→2는 evaluation **best**, 이후는 final에서 resume. `run_dt_forward_pipeline.sh`는 5단계를 자동 체이닝하는 분리 실행(detached) 오케스트레이터로, `runs/ppo_plane_dt_forward_pipeline/console_pipeline.log`에 로그, `pipeline.pid`에 PID 기록. 예상 소요 시간 약 15~18시간.

---

## 2026-07-28 — GD 대조군(direct torque) 전진 5단계 파이프라인 완주 및 결과

**커밋:** (미커밋)
**요청:** (앞 항목 파이프라인의 실행 결과 기록)
**파일:** `runs/ppo_plane_dt_forward_stage{1..5}/` (학습 산출물)
**변경:** 2026-07-27 18:57 ~ 07-28 00:24 (약 5.5시간, RTX 5090에서 ~3,800 fps) 5단계 전부 완주. 총 gradient 경험량은 GD와 동일한 ~47.6M 스텝 (타임스텝 카운터는 stage1 best가 3.7M 지점이어서 43.4M으로 표시 — resume 되감기 효과이며 실제 학습량 차이가 아님).

| | GD (treatment) | Direct Torque (control) |
|---|---:|---:|
| 최고 평가 리턴 | 208,913 | **512,361** |
| 마지막 평가 리턴 | 208,703 | 75,569 |
| 최종 구간(Q4) 평가 평균 ± 표준편차 | ~208k ± 미미 | 205,951 ± **154,458** |
| 평가 ep_len 6000 달성률 (stage5) | 사실상 100% | **31/307 (10%)** |
| 최종 rollout x 속도 | 0.519 m/s | **1.19~1.26 m/s** |
| 최종 direction_similarity | 0.840 | 0.73~0.79 |

**핵심 발견:** (1) Direct torque는 GD prior 없이도 훨씬 빠른 전진 보행(2.3배 속도, 스텝당 보상 ~85 vs ~35)을 스스로 발견했다. (2) 그러나 47.6M 스텝 내내 안정화에 실패 — 평가 리턴이 13k~512k 사이를 진동하고 90%의 평가에서 로봇이 넘어져 조기 종료된다. GD의 motion vector prior가 제공하는 실질 가치는 탐색 가속이 아니라 **자세 안정성(넘어지지 않음)과 정책 일관성**임이 이 대조 실험에서 드러났다. (3) stage1에서 3.7M 만에 GD 최고치의 2배가 넘는 429k를 찍고 붕괴하는 등 각 단계에서 GD보다 훨씬 극단적인 불안정을 보였고, target_kl 0.04 (stage4~5)로도 진동을 잡지 못했다. 배포 가능한 조합은 `runs/ppo_plane_dt_forward_stage5/.../evaluation/best_model.zip` + `best_model_vecnormalize.pkl` (512,361 @ 42.8M)이지만 재현 일관성이 없어 단독 배포 부적합.

---

---

## 2026-07-23 — 우측 정책 3단계 run을 policies/path_tracking/right로 정리

**커밋:** (미커밋)
**요청:** 학습된 우측 정책을 다른 정책들과 같이 policy 디렉토리에 정리해달라는 요청.
**파일:** `policies/path_tracking/right/{00_aborted_session_terminated,01_right_from_scratch_long,02_right_continue_stage2,03_right_continue_stage3}/` (runs/에서 이동), `policies/path_tracking/right/TRAINING_HISTORY_cluade.txt`, `training/configs/ppo_plane_right_continue_stage2.yaml`, `training/configs/ppo_plane_right_continue_stage3.yaml`
**변경:** 좌측 규약대로 timestamped run 전체(모델·정규화 통계·평가·체크포인트·영상·TensorBoard·monitor·resolved config)를 번호 디렉터리로 이동하고 각 stage 콘솔 로그/pid 파일도 함께 보관. 빈 runs/ppo_plane_right_* 디렉터리 제거. 원장(TRAINING_HISTORY_cluade.txt)의 run 경로·평가/TensorBoard 명령을 새 위치로 갱신, stage 2/3 YAML resume 경로를 policies/ 경로로 갱신(좌측 YAML과 동일 방식). 이동 후 무결성 검증: 새 위치의 best_model.zip 1-episode 평가에서 리턴 242,865/6,000스텝으로 학습 시 평가(242,808~244,043)와 일치, vecnormalize 자동 매칭 확인.

**미해결 플래그:** right/에 원장이 2개 존재 — TRAINING_HISTORY.txt(delta=-45 근거의 사전 초안, 존재하지 않는 run 20260722-232233 기록, plane_v3.py의 미검증 방향 주석 인용)와 TRAINING_HISTORY_cluade.txt(실학습 기록). 실제 학습된 3단계는 모두 resolved_config 기준 delta=225이며 -45는 MotionMatrix 수치 검증에서 거울상이 아님이 확인된 값. 사용자가 만든 파일이므로 통합/정리는 사용자 확인 대기.

## 2026-08-04 — 후진 정책(gaitrev_delta0) Stage 2 연속 학습 시작

**커밋:** (미커밋)
**요청:** gaitrev_delta0 Stage 1 학습 결과 확인 후, 정책을 더 훈련시킬 수 있는 설정으로 Stage 2를 이어서 진행하고(이전 스테이지와 동일한 학습 시간), 예상 완료 시간을 알려달라는 요청.
**파일:** `training/configs/ppo_plane_gaitrev_delta0_stage2.yaml` (신규), `policies/path_tracking/backward/01_gaitrev_delta0_stage1/` (Stage 1 산출물 보존 복사), `policies/path_tracking/backward/TRAINING_HISTORY.txt` (8절 추가)
**변경:** Stage 1(최고 평가 리턴 199,592 @ 27.9M, x_vel -0.529, 완주 확인)을 우측 계보 규약대로 `01_gaitrev_delta0_stage1/`에 보존하고 이를 resume 소스로 하는 Stage 2 설정 작성. 환경·보상·네트워크·seed는 Stage 1과 동일하게 동결, 추가 28,413,952 스텝(누적 56.8M). lr은 train.py의 resume 시 스케줄 거부 제약에 따라 상수 5e-5(= Stage 1 감쇠 스케줄의 시간 평균이자 평가가 187k→199k로 오르던 후반부 실효 구간). 우측과 달리 Stage 1의 trust region이 활발했으므로(early stop 1,680/6,937회, 24%) n_epochs 10과 target_kl 0.04는 유지. `scripts/launch_training.sh`로 15:45:03 KST 분리 실행(pid 16980), resume 정상 확인(누적 28.45M부터 시작, ep_rew_mean 1.94e+05 유지). Stage 1 실측 24,461초(1,161 fps) 기준 완료 예상 22:33 KST 전후.

---

## 2026-08-04 — 후진 정책 Stage 2 완주 및 결과

**커밋:** (미커밋)
**요청:** (앞 항목 Stage 2 학습의 실행 결과 기록)
**파일:** `runs/ppo_plane_gaitrev_delta0_stage2/` (학습 산출물), `policies/path_tracking/backward/TRAINING_HISTORY.txt` (8절 결과 추가)
**변경:** 15:45~20:26 KST(4시간 41분, 평균 1,685 fps) 28.4M 스텝 완주(누적 56.8M). 최고 평가 리턴 202,236 @ 54.9M(Stage 1 대비 +1.3%), 최종 10회 평균 200,545(+0.9%), x_vel -0.54, dir_sim 0.845, ep_len 6,000 유지. 곡선은 완만한 단조 상승으로 종료 시점에도 미상승. 핵심 진단: 6,937 iteration 중 6,935회(99.97%)가 KL early stop — 상수 5e-5는 이 정책 상태에서 과대하며 실효 갱신량을 target_kl이 전부 결정(말기에는 iteration당 1~2 epoch만 실행, fps가 Stage 1보다 45% 빠른 것도 이 때문). 권장 후진 정책을 이 run의 `evaluation/best_model.zip`(202,236 @ 54.9M)으로 갱신. Stage 3 시 lr 2.5e-5 이하 권장이나 수익 체감이 뚜렷해 방향 통합 커리큘럼 전환이 더 가치 있을 수 있음을 기록.

---

## 2026-08-04 — 후진 정책 Stage 3 연속 학습 시작 (KL 병목 해소)

**커밋:** (미커밋)
**요청:** Stage 2 결과 보고 후 사용자가 Stage 3 진행을 결정 ("일단 stage3 수행하자").
**파일:** `training/configs/ppo_plane_gaitrev_delta0_stage3.yaml` (신규), `policies/path_tracking/backward/02_gaitrev_delta0_stage2/` (Stage 2 산출물 보존 복사), `policies/path_tracking/backward/TRAINING_HISTORY.txt` (9절 추가)
**변경:** Stage 2를 `02_gaitrev_delta0_stage2/`에 보존하고 그 final_model에서 resume하는 Stage 3 설정 작성. Stage 2 진단(99.97% KL early stop = 상수 5e-5 과대)에 따라 좌/우측 검증 레시피대로 lr을 절반(2.5e-5)으로 인하. n_epochs 10은 유지 — 목표가 epoch 활용률 회복이므로 epoch까지 줄이면 역효과이고 target_kl 0.04가 안전 상한. 나머지(환경·보상·네트워크·seed·주기)는 동결, 추가 28,413,952 스텝(누적 85.2M). 20:30:16 KST 분리 실행(pid 25184), resume 정상 확인. 완료 예상 08-05 02:00~03:20 KST. 판정 기준도 기록: early stop이 여전히 90%+면 lr 추가 인하 대신 방향 통합 커리큘럼 전환 권장.

---

## 2026-08-04 — CLAUDE.md 생성 (작업 착수 전 계획 합의 지침)

**커밋:** (미커밋)
**요청:** 작업 수행 전에 어떤 방법·순서로 진행할지 먼저 제시하고 피드백을 받은 뒤 착수하도록 하는 지침을 프로젝트 전역 설정에 추가해달라는 요청. 사용자가 방법론 관련 지식을 쌓을 수 있게 하는 것이 목적.
**파일:** `CLAUDE.md` (신규 생성)
**변경:** 저장소 루트에 프로젝트 전역 지침 파일 생성. (1) 작업 착수 전 방법·순서·근거(대안 포함)를 제시하고 피드백 후 진행 — 상태를 바꾸지 않는 단순 조회는 예외, (2) 기존 관행인 CLAUDE_CHANGES.md 변경 이력 기록 의무를 명문화.

---

## 2026-08-05 — 후진 정책 Stage 3 완주 및 결과

**커밋:** (미커밋)
**요청:** (앞 항목 Stage 3 학습의 실행 결과 기록)
**파일:** `runs/ppo_plane_gaitrev_delta0_stage3/` (학습 산출물), `policies/path_tracking/backward/TRAINING_HISTORY.txt` (9절 결과 추가)
**변경:** 08-04 20:30 ~ 08-05 01:19 KST(4시간 49분, 1,638 fps) 28.4M 스텝 완주(누적 85.2M). 최고 평가 리턴 209,908 @ 85.2M(마지막 평가가 곧 최고치), 최종 10회 평균 207,924(Stage 2 대비 +3.7%), x_vel -0.544, dir_sim 0.849, std 0.208. lr 절반 인하가 유효했음(Stage 2 +0.9% vs Stage 3 +3.7%). 단 KL early stop이 후반부 92.5%로 재포화 — 사전 판정 기준(90%+)에 따라 후진 단독 개선은 종료하고 방향 통합 커리큘럼 전환을 권장으로 기록. 권장 후진 정책을 이 run의 `evaluation/best_model.zip`(209,908)로 갱신. 계보 누적 성과: 3단계 85.2M 스텝, 199,592 → 209,908 (+5.2%).

---

## 2026-08-05 — 후진 정책 3단계 산출물을 policies/path_tracking/backward로 보존 정리

**커밋:** (미커밋)
**요청:** 완성된 정책뿐 아니라 모든 stage를 컨벤션대로 따로 보존해달라는 요청. 계획 제시 후 runs/ 중복본은 "검증 후 삭제"로 사용자 승인.
**파일:** `policies/path_tracking/backward/{01_gaitrev_delta0_stage1,02_gaitrev_delta0_stage2,03_gaitrev_delta0_stage3}/`, `policies/path_tracking/backward/TRAINING_HISTORY.txt` (경로 갱신 + 10절 추가), `runs/ppo_plane_gaitrev_delta0*` (제거)
**변경:** 좌/우측 계보 컨벤션(이동 방식)대로 정리. Stage 3는 timestamped run 전체 + 콘솔 로그/pid를 `03_gaitrev_delta0_stage3/`로 직접 이동. Stage 1·2는 기존 보존 복사본을 `diff -rq` 전체 대조로 runs/ 원본과 바이트 단위 동일함을 확인한 뒤 원본 삭제(중복 5.8GB 해소, 이동과 동일한 최종 상태). 빈 runs/ 디렉터리 제거. 원장의 runs/ 경로 참조를 전부 새 위치로 갱신하고 1절에 최신 권장(9절) 포인터 추가. 이동 후 무결성 검증: 03 best_model 1 에피소드 평가 리턴 209,249/6,000스텝으로 학습 시 평가(209,908)와 일치. Stage 2/3 YAML의 resume 경로는 원래 policies/를 가리켰으므로 갱신 불요.

---

## 2026-08-05 — CoRL 2026 리부탈용 관절 수 스케일링 MJCF 생성기 및 n-DOF 모델 추가

**커밋:** (미커밋)
**요청:** CoRL 2026 Submission #676 리부탈의 관절 수 스케일링 실험(리뷰어 Hhic Q5)을 위해 14-DOF 모델을 임의 n-DOF로 확장한 새 환경 구성. 진행 중인 학습 보호를 위해 기존 환경(`resources/`, `plane_v3.py`)은 일절 수정하지 않기로 합의. 생성 스크립트는 역할이 분명하도록 scripts/가 아닌 리소스 디렉토리에 README와 함께 배치(사용자 지정).
**파일:** `horcrux_env/resources_rebuttal/{generate_scalable_mjcf.py, README.md, __init__.py, horcrux_n{06,10,14,20}.xml, horcrux_plane_n{06,10,14,20}.xml}`
**변경:** 원본 `horcrux_p.xml`을 파싱해 head/h-link/v-link 바디를 템플릿으로 추출하고 관절 수 n짜리 체인으로 재조립하는 생성기 작성(에셋은 `../resources/assets/` 상대경로 공유). n=6/10/14/20 모델과 평지 월드 생성. 검증: 각 n의 차원(nq=7+n, nu=n, nsensordata=5n+10) 확인 + 재생성 n=14 모델이 원본과 물리 파라미터 완전 일치·동일 토크 2000스텝 롤아웃 max|qpos diff|=0.0(비트 단위 동일)임을 확인. 초기 구현에서 com 카메라 바디가 체인 앞으로 밀려 body id 순서가 어긋나는 문제를 원위치 삽입으로 수정.

---

## 2026-08-05 — n-DOF 모델 미리보기 렌더링을 resources_rebuttal에 추가

**커밋:** (미커밋)
**요청:** MuJoCo 렌더링/스크린샷을 리소스 폴더에 함께 기재해달라는 요청. 일회성 스크린샷 대신 재현 가능한 방식으로 구현.
**파일:** `horcrux_env/resources_rebuttal/{generate_scalable_mjcf.py, README.md, previews/horcrux_n{06,10,14,20}.png}`
**변경:** 생성기에 `--render-previews` 옵션 추가(headless EGL 렌더링, 몸길이 비례 카메라 프레이밍). n=6/10/14/20 미리보기 PNG를 `previews/`에 생성하고 README에 파일 표·재생성 명령·이미지 표(모델 미리보기 섹션)를 추가.

---

## 2026-08-05 — GaitV3: gait 생성기 관절 수 일반화 (CoRL 리부탈 스케일링 실험)

**커밋:** (미커밋)
**요청:** 관절 수 스케일링 실험을 위한 gait 생성기 일반화. 스케일링 프로토콜은 파동 수 고정(e_d1 재스케일) 대신 **파라미터 고정**으로 사용자 결정. 기존 `gait_v2.py`는 무수정 유지.
**파일:** `horcrux_env/envs/gait_v3.py` (신규)
**변경:** `GaitV3(GaitV2)` 서브클래스 작성 — `n_joints` 파라미터 추가, 손으로 풀어 쓴 j_1..j_14의 규칙(홀수 관절 `sin(e_d1·i + f1)`, 짝수 관절 `sin(e_l1·i + f2 + δ)`)을 관절 인덱스로 벡터화해 `serpenoid()`만 오버라이드. 연산 순서를 GaitV2와 동일하게 유지해 비트 단위 동일성 확보. 검증(`python -m horcrux_env.envs.gait_v3`): ① n=14에서 8방향 파라미터 + 역방향 + 상이한 gcd 조합 등 9개 세트 전부 GaitV2와 MotionMatrix·getMvec 비트 단위 동일, ② reset() 후에도 동일, ③ n=6/10/20은 독립 루프 구현과 대조해 동일 확인. `envs/__init__.py`는 수정하지 않음(신규 env 등록 시점에 일괄 처리 예정).

---

## 2026-08-05 — PlaneJoyDirWorldScalable: n-DOF 환경 구축 및 차원·등가성 검증

**커밋:** (미커밋)
**요청:** n=6/10/14/20 환경 구축. 관절 수에 따라 달라지는 action/observation 차원 검증 필수(사용자 지정). Env 부모는 PlaneJoyDirWorld로 합의.
**파일:** `horcrux_env/envs/plane_v3_scalable.py` (신규), `horcrux_env/__init__.py` (register 블록 1개 추가 — 기존 등록 무변경)
**변경:** `PlaneJoyDirWorldScalable(PlaneJoyDirWorld)` 작성 — `n_joints`로 `resources_rebuttal/horcrux_plane_n{N}.xml` 모델과 GaitV3 사용, action `(n,)`·obs `(6n+13,)` 공간, 관측/info 슬라이스를 n 기반 공식으로 재정의(n=14일 때 원본 리터럴과 일치). `step()`은 110줄 복제 대신 부모 호출 후 n 의존 info 항목 5개만 덮어쓰는 방식으로 중복 최소화. gym ID `horcrux_env/plane-scalable-v0` 등록(entry point를 모듈 직접 경로로 지정해 `envs/__init__.py` 무수정). 검증(`python -m horcrux_env.envs.plane_v3_scalable`): ① n=6/10/14/20 각각 action (n,)·obs (6n+13,) = (49/73/97/133), motion vector·touch 이진화·info 구조 확인, ② n=14 vs 원본 300스텝 동일 action에서 관측·보상·종료·info 전부 bitwise 동일(max reward diff=0.0), ③ gym.make 경로 4종 + 기존 plane-v0 회귀 확인. 참고: 원본 plane_v3.py의 info["joint_vel"] 슬라이스(-41:-27)는 실제로 touch_bot 구간을 가리키는 기존 이슈가 있으나, 등가성 보존을 위해 동일 공식을 유지하고 docstring에 명시(실제 관절 속도는 observation[n:2n]).

---

## 2026-08-05 — 신규 scalable env의 info["joint_vel"] 버그 수정

**커밋:** (미커밋)
**요청:** 새 env는 아직 학습에 사용된 적이 없으므로, 발견된 joint_vel 버그를 계승하지 말고 수정하기로 사용자 결정. 원본 plane_v3.py는 무수정 유지.
**파일:** `horcrux_env/envs/plane_v3_scalable.py`
**변경:** `info["joint_vel"]` 슬라이스를 원본 버그 호환 공식 `-(2n+13):-(n+13)`(touch_bot 구간)에서 실제 관절 속도 `n:2n`으로 수정. docstring의 "원본 공식 보존" 서술을 "의도된 차이" 명시로 교체. 검증 갱신: n=14 등가성 비교에서 joint_vel을 bitwise 비교 목록에서 빼는 대신 ① 신규 env가 실제 관절 속도 obs[n:2n]을 보고하는지, ② 원본이 여전히 obs[56:70](touch_bot)을 보고하는지(원본 동작 가정 감지) 양쪽을 명시적으로 assert. 차원 검증에도 n별 joint_vel==obs[n:2n] 확인 추가. 전체 검증 재실행 통과 — 관측·보상·종료·나머지 info는 여전히 bitwise 동일(max reward diff=0.0).

---

## 2026-08-05 — 스케일링 실험 준비: unhealthy 유예 수정, no-GD 비교군 env, config 8종

**커밋:** (미커밋)
**요청:** 이전 GD vs 직접토크 비교에서 물리적으로 불가능한 행동으로 높은 보상을 얻는 exploit(평균 에피소드 길이는 매우 짧음)이 관찰되어, unhealthy 상태에서 reset까지의 유예를 타이트하게 조정하고 이를 YAML에 명시하기로 함. 동시 다중 학습(n별 병렬)을 위한 config 구성.
**파일:** `horcrux_env/envs/plane_v3_scalable.py` (mixin 추가), `horcrux_env/envs/plane_direct_torque_scalable.py` (신규), `horcrux_env/__init__.py` (register 1개 추가), `training/configs/ppo_plane_scaling_{gd,dt}_n{06,10,14,20}.yaml` (신규 8개)
**변경:** ① 분석 중 원본 `is_terminated` property가 step당 2회 호출(_get_rew의 unhealthy_cost + 종료 판정)되며 호출마다 카운터를 증가시켜 **실효 유예가 설정값의 절반**(30 → 15스텝=0.75s)임을 발견. `SingleEvalTerminationMixin`으로 step당 1회 갱신으로 수정해 설정값=실제 유예 스텝이 되도록 함(양 scalable env 공통 적용, 원본 무수정). ② `PlaneDirectTorqueWorldScalable` 작성 — action/obs 공간은 부모가 model.nu/sensordata에서 자동 유도, 관측·info 슬라이스만 n 공식화(obs 5n+13). gym ID `plane-direct-torque-scalable-v0` 등록. 검증: n=6/10/14/20 차원(43/63/83/113), n=14 등가성(unhealthy 미진입 궤적 300스텝 bitwise 동일), 유예 카운터 1/step 확인 — 전부 통과. ③ config 8종: 논문 stage-1 레시피(lr 3e-4, n_epochs 5, net 512×5, 7,864,320스텝)를 전 조합 동일 적용, gait 파라미터 n 무관 고정(30,30,40,40,23), **unhealthy_max_steps: 10**(0.5s, 실효=설정값). 의도적 이탈(save_freq 250000, video 200 iter — 디스크/렌더 부담)은 8개 전부 동일 적용으로 공정성 유지, 주석 명시. 시드는 launch 시 --seed 오버라이드(42/43/44 예정). 8개 config 전부 gym.make 스모크 테스트 통과.

---

## 2026-08-05 — InfoMetricsCallback 확장: env info 전체 TensorBoard 로깅

**커밋:** (미커밋)
**요청:** 환경 info dict의 데이터를 TensorBoard에서 모두 볼 수 있게 확장.
**파일:** `training/callbacks/info_metrics.py`
**변경:** 기존 15개 스칼라 + com_yaw만 로깅하던 콜백을 전면 확장. `env/` 네임스페이스: 누락 스칼라 3종(x/y_displacement, distance_from_origin) 추가, com 위치(x/y/z)·자세(yaw/pitch/roll deg + abs) 분해, 벡터 크기 집계(action/jpos/jvel abs_mean·abs_max, head_angvel/linacc norm) — 총 34태그. `env_detail/` 네임스페이스(신설): joint_pos·joint_vel·action·motion_vector 성분별 + head_quat/angvel/linacc·joy·friction·step_ypr·rew_ori 성분별 — n=6 기준 46태그(n에 비례). 제외 항목(motionMatrix, gait_params, init_*, step)과 이유를 docstring에 명시. 기존 태그명은 전부 유지해 이전 run과의 TB 비교 연속성 보존, env에 없는 키는 조용히 스킵(DT env의 motion_vector 등). `per_component=False`로 상세 로깅 비활성 가능. 검증: GD/DT n=6 config로 8,192스텝 실학습 스모크 — GD env/34+detail/46, DT env/34+detail/40(mvec 없음 확인) 태그 기록 확인.

---

## 2026-08-05 — 스케일링 웨이브1 재시작: eval 오버헤드 완화

**커밋:** (미커밋)
**요청:** (웨이브1 GD 4런 실행 중 발견된 문제의 자율 조치) 사용자 승인 계획 "웨이브당 ~2시간, 마감 전 6웨이브 완료"가 eval 오버헤드로 불가능해져 프로토콜 수정 후 재시작.
**파일:** `training/configs/ppo_plane_scaling_{gd,dt}_n{06,10,14,20}.yaml` (evaluation 절), `runs/_aborted_wave1_evalfreq10k/` (보존)
**변경:** 웨이브1 첫 실행 실측 — 에피소드가 6000스텝으로 길어지자 eval_freq 10000(vec step) × 5에피소드가 학습 스텝의 ~3배를 평가에 소모(n=10에서 101회 eval/1.01M 스텝), 실효 처리량 100~250fps로 저하(n=20 ETA 17시간). 8개 config의 evaluation을 gaitrev 계열 검증 주기(eval_freq 100000, n_eval_episodes 3)로 완화 — 전 조합 동일 적용으로 공정성 유지, 학습 곡선은 monitor CSV 담당, 사유 주석 명시. 기존 웨이브1 산출물은 `runs/_aborted_wave1_evalfreq10k/`에 보존 후 GD 4런 재시작(pid 50638/50648/50694/50739). 보존물 중 gd_n06 완주 run(구 프로토콜)에서 유의미한 발견: 17,186 에피소드 전부 ~34스텝 종료(뒤집힘 반복 퇴행 정책) — n=6에서 고정 게이트 파라미터가 몸통에 반 파동만 싣는 문제의 실증. 참고: 첫 보고의 "ep_len 4.43" 등은 콘솔 표 지수 표기(4.43e+03)를 정규식이 잘못 읽은 것으로 정정(실제 4,430스텝, 학습 자체는 정상 진행 중이었음).

## 2026-08-06 — 스케일링 실험 24런 완료 및 분석

**커밋:** (미커밋)
**요청:** (승인된 실험 계획의 실행·분석 단계) GD vs DT × n=6/10/14/20 × 시드 42/43/44 매트릭스 학습 및 표본 효율 분석.
**파일:** `scripts/analyze_scaling_experiment.py` (신규), `runs/ppo_plane_scaling_{gd,dt}_n{06,10,14,20}/` (24런), `runs/scaling_analysis/` (그림·표·매니페스트)
**변경:** 24런 전체 완료(8/5 20:04 ~ 8/6 오전, 4런 동시 슬롯 방식). 분석: monitor CSV 병합 → 100k 스텝 빈 학습 곡선 → F_n(GD 최종 10% 평균), L_n=0.8F_n, 도달 스텝(검열 처리), 정규화 AUC. **결과: n=10에서 GD가 3.2배 빠르게 기준 도달(1.25M vs 4.05M), n=14/20에서는 DT 3시드 전부 예산(7.86M) 내 미도달(비율 하한 ≥3.0×/≥2.5×). n=6은 GD 0/3, DT 1/3 성공 — 고정 게이트 파라미터(반 파동)가 n=6에서 prior 이득을 상실시킴(정직 보고 대상).** 물리 타당성 검증: DT 고보상 정책(dt_n10 40.9만, dt_n06 24.7만)은 결정론 롤아웃에서 평균 관절 속도 6.3~6.5 rad/s로 XM430-W250 무부하 한계(5.97 rad/s) 초과 — 하드웨어 불가 영역의 시뮬 전용 행동. GD는 평균 2.4 rad/s로 실기체 타당 영역(순간 피크는 양쪽 다 초과 가능, 평균이 판별 기준). horcrux env에 matplotlib/pandas 설치.

## 2026-08-06 — GD gait δ=23→0 정정 및 스케일링 실험 디렉토리 분리

**커밋:** (미커밋)
**요청:** 사용자 확인 — 직진(+X) 게이트의 delta는 0 (완료된 GD 런의 δ=23은 대각선용 파라미터). 아울러 스케일링 실험의 정책 결과·config·분석 그림이 다른 실험과 섞이지 않도록 디렉토리 정리 요청.
**파일:** `runs/corl2026_scaling/` (신설 + README), `training/configs/corl2026_scaling/` (config 8종 이동, GD는 δ=0·경로·이름 갱신), `scripts/analyze_scaling_experiment.py` (--gd-variant 옵션, 새 레이아웃)
**변경:** 경위 — GD arm config가 δ=23을 쓴 것은 기존 forward stage1이 gait_params 미지정으로 생성자 기본값 (30,30,40,40,23)을 상속했기 때문(7/16 커밋부터 동일). 코드의 8방향 매핑상 →(+X)는 (30,30,40,40,0)이며 사용자가 δ=0으로 확정. 참고 실측: open loop(진폭 1.35, 4000스텝)에서 δ=23은 +27° 전방 대각(dX +2.11), δ=0은 -135°(dX -4.71) — δ=23 학습 정책이 몸통을 ~90° 돌린 sidewinding으로 수렴한 원인. 조치: ① 완료 산출물 전부 `runs/corl2026_scaling/`로 이동(gd_delta23_n{NN} 이름으로 보존 — prior 방향 ablation 자료, dt_n{NN}은 gait 무관이라 본 실험에 재사용), ② config를 전용 디렉토리로 이동하고 GD는 δ=0·output_dir·실험명 갱신, ③ 분석 스크립트에 --gd-variant delta0|delta23 추가, ④ δ=0 GD 웨이브1(n=6/10/14/20, 시드 42) 재실행 시작(pid 111150/111160/111205/111251). DT 12런은 재학습 불필요.

## 2026-08-06 — 스케일링 실험 config·분석 스크립트를 실험 디렉토리로 자체 포함화

**커밋:** (미커밋)
**요청:** 기본 scripts/, training/configs/ 폴더에 두지 말고 corl2026_scaling 안에 모아, 학습별 config가 run 폴더 하위에 있도록 하는 정리 방식 선호(사용자).
**파일:** `runs/corl2026_scaling/{configs/,analyze_scaling_experiment.py,README.md}` (이동·갱신), `training/configs/corl2026_scaling/` (제거), `scripts/analyze_scaling_experiment.py` (이동됨)
**변경:** config 8종을 `runs/corl2026_scaling/configs/`로, 분석 스크립트를 실험 루트로 이동. 스크립트 경로 기준을 EXP_ROOT(자기 위치) 상대로 수정하고 delta23 분석 재실행으로 동작 확인(결과 동일). README의 경로·실행 예시 갱신. 참고: `.gitignore`가 `/runs/`를 무시하므로 이 트리의 config/스크립트/README는 git 미추적 상태 — 각 run 폴더의 resolved_config.yaml 스냅샷으로 재현성은 유지되며, 추적을 원하면 .gitignore 예외 추가 필요(사용자 결정 사항). 진행 중인 δ=0 학습(설정은 launch 시점에 로드됨)에는 영향 없음.

## 2026-08-06 — δ=0 GD 12런 완료: 스케일링 실험 최종 매트릭스 확정

**커밋:** (미커밋)
**요청:** (사용자 위임 자율 진행) δ=0 GD 전 시드·전 n 완주 후 알림.
**파일:** `runs/corl2026_scaling/gd_delta0_n{06,10,14,20}/` (12런), `runs/corl2026_scaling/analysis_delta0/` (최종 분석)
**변경:** δ=0 GD 12런 완주(8/6 10:39 ~ 저녁, 4슬롯 자동 backfill). 최종 결과(GD δ=0 vs DT, 논문 예산 7.86M): 도달 스텝 비율 **n=10 2.45× → n=14 ≥2.65×(DT 1시드 검열) → n=20 ≥3.65×(DT 1시드 검열)로 n에 대해 단조 증가** — "GD 이득이 관절 수와 함께 커진다" 주장 실증. n=6은 양쪽 퇴행(δ 무관, 반 파동 한계). 특이사항: gd_delta0_n20 시드 42는 2.6M에 21.4만 도달 후 후반 정책 붕괴(최종 8.5k) — 3/3 시드 보행 학습에는 성공했으나 1/3이 후반 불안정(stage-1 레시피에 target_kl 없음과 연관 추정), 분석 F_n이 이 시드로 인해 하향(157k). δ=23 매트릭스와 비교: n=10/14는 δ 간 동등, n=20은 δ=23이 더 안정적(3/3 성공, 30만). 상세 수치는 analysis_delta0/scaling_summary.csv.

## 2026-08-07 — heading-aligned GD 계보 시작 (yaw 패널티 10.0)

**커밋:** (미커밋)
**요청:** δ=0 정책들이 몸통을 ~90° 돌린 게걸음(sidewinding)으로 수렴하는 문제 — 방위를 올바르게 학습시키기 위해 orientation 패널티 계수 상향(사용자, 프로브 없이 전체 진행·별도 디렉토리 지시).
**파일:** `runs/corl2026_scaling/configs/ppo_plane_scaling_gd_heading_n{06,10,14,20}.yaml` (신규), `runs/corl2026_scaling/gd_delta0_heading_n{NN}/` (신규 계보)
**변경:** 가중치 조사 결과 — 활성 방위 비용은 `rotation_norm_cost_weight`(기본 0.5, 0.025/도/스텝: yaw 90°에 2.25/스텝 vs 이동 보상 ~42/스텝이라 crab이 최적)뿐이고, `side_cost_weight`(60)·`rotation_orientation_cost_weight`(0.05)는 `_get_rew`에서 미사용인 죽은 파라미터. 후진 계보의 검증된 U턴 방지값과 동일하게 **10.0**(0.5/도/스텝, yaw 90°에서 이동 보상 상쇄)으로 설정한 heading 변형 config 4종 작성(δ=0 유지, 보상 변경이므로 표본 효율 매트릭스와 비교 불가 명시). 웨이브1(시드 42, pid 149422/149432/149474/149524) 시작, 12런 자동 backfill + 완료 시 알림 예정.

## 2026-08-07 — heading-aligned GD 12런 완료: 방위 정렬 보행 학습 성공

**커밋:** (미커밋)
**요청:** (전날 지시의 자율 완주) yaw 패널티 10.0 계보 12런 완료 및 방위 정렬 검증.
**파일:** `runs/corl2026_scaling/gd_delta0_heading_n{06,10,14,20}/` (12런 완료)
**변경:** 밤 사이 12런 자동 완주. 결정론 롤아웃(2000스텝) 검증 결과 — **n=10/14/20 각각 3시드 중 2시드가 몸통 yaw ±4° 이내 + 이동각 ±5° 이내의 방위 정렬 직진 보행 학습 성공** (n10 0.29-0.30 m/s, n14 0.51-0.59 m/s, n20 0.40-0.45 m/s). 게걸음(yaw ±90°) 문제 해소 확인. 속도는 sidewinding판(0.43-0.83 m/s) 대비 낮음 — 정렬 제약의 대가. 각 n에서 1/3 시드는 불안정(조기 종료/부분 정렬), n=6은 여전히 전멸(반 파동 한계, 보상 구조와 무관 재확인). 몸통 roll은 ~36-46°로 잔존(패널티가 yaw만 대상). 데모/영상(P6)·보행 품질 표(P2)에는 이 계보의 성공 시드 사용 권장.

## 2026-08-07 — DT heading 계보 시작 (heading 보상 하의 쌍대 비교군)

**커밋:** (미커밋)
**요청:** heading 보상(가중치 10.0)으로 GD만 학습하면 비교가 불공정하므로 DT도 동일 보상으로 재학습(사용자 지적·확인).
**파일:** `runs/corl2026_scaling/configs/ppo_plane_scaling_dt_heading_n{06,10,14,20}.yaml` (신규), `runs/corl2026_scaling/dt_heading_n{NN}/` (신규 계보)
**변경:** DT config에 `rotation_norm_cost_weight: 10.0` 추가한 heading 비교군 4종 작성(원본 dt_* 런과 비교 불가 명시). 참고: 기존 표본 효율 매트릭스(gd_delta0 vs dt, 가중치 0.5 양쪽 동일)는 여전히 공정·유효 — heading 계보는 별도의 쌍대 실험. 웨이브1(시드 42, pid 181453/181463/181509/181554) 시작, 12런 자동 backfill 예정.

## 2026-08-07 — DT heading 12런 완료: heading 보상 쌍대 분석 및 정책 검증

**커밋:** (미커밋)
**요청:** (사용자 지시의 자율 완주) DT heading 계보 완료 후 분석.
**파일:** `runs/corl2026_scaling/dt_heading_n{06,10,14,20}/` (12런), `runs/corl2026_scaling/analysis_heading/`, `analyze_scaling_experiment.py` (--dt-variant 옵션 추가)
**변경:** DT heading 12런 완주. heading 보상 기준 도달 스텝 비율: n=10 ≥1.10×, n=14 0.92×(역전), n=20 ≥1.33× — **원 보상 매트릭스(2.45×→≥3.65×)와 달리 GD 우위가 크게 축소**. 단, 정책 검증(2000스텝 롤아웃) 결과 DT heading 정책들은 방위 정렬(yaw ±7°)·고속(0.66~1.41 m/s)이지만 **평균 관절 속도 5.96~6.96 rad/s로 XM430 무부하 한계(5.97) 이상에서 동작** — 하드웨어 재현 불가 영역의 시뮬 전용 해(9시드 중 dt_n14 s44 3.77 rad/s만 예외적). GD heading 성공 시드는 평균 2.4 rad/s로 실기체 타당. 결론: heading 보상 하 표본 효율 수치는 DT의 비전이성 해로 오염되어 리부탈 Q5에는 **원 보상 매트릭스(analysis_delta0)를 헤드라인으로 유지**하고, heading 계보는 ① GD 데모/영상용 정렬 정책, ② "제약을 줘도 자유 토크 RL은 시뮬 허점(초과 관절 속도)으로 회피한다"는 형태학적 prior 논거 보강 자료로 활용 권장.

## 2026-08-08 — GD vs DT 다차원 성능 비교 (multimetric)

**커밋:** (미커밋)
**요청:** 에피소드 보상·길이 외 다차원에서 GD/DT 비교, 코드·데이터·그림을 한 폴더에 자체 포함 정리(사용자 승인 지표: 이동 성능·CoT·전이성·안정성·주기성·강건성 스윕).
**파일:** `runs/corl2026_scaling/multimetric/{evaluate_multimetric.py, README.md, data/, figures/, eval_console.log}`
**변경:** 144 롤아웃(2 보상 쌍 × n=10/14/20 × 2 arm × 3시드 × 4조건) 평가. 핵심(original 쌍 nominal): GD가 평균 관절 속도 2.3–2.6 rad/s(한계 5.97 여유) vs DT 4.0–6.4(n=10은 평균부터 초과), 평균 토크 1.2–1.3 vs 2.3–2.4, CoT(n≥14) 4.3–4.5 vs 5.4–7.1, 완주율(n=14/20) 1.0/0.67 vs 0.33/0.0, 주기성 0.28–0.29 vs 0.18–0.25. 절대 속도는 DT 우세(정직 보고) — 단 비지속·하드웨어 비현실 영역. 방법론 발견 2건: ① any-joint 순간 초과 지표는 GD도 피크로 높아 변별력 약함 → 평균 관절 속도가 올바른 전이성 판별자, ② 강건성 스윕 유지율은 조기 종료 시드로 분산 큼 → 보조 자료로 강등. GD 실패 시드 2개(orig n10 s43 후방 퇴행, n20 s42 붕괴)는 raw CSV에 그대로 기록.

## 2026-08-10 — dt_tau2 계보 시작 (DT 토크 예산 ablation, ±2.0 N·m)

**커밋:** (미커밋)
**요청:** DT용 새 비교 환경 — 토크 범위 [-2, 2]로 생성해 이전 dt와 동일하게 학습(사용자). 신규 env 클래스 불필요(기존 scalable env의 torque_min/max 인자 활용).
**파일:** `runs/corl2026_scaling/configs/ppo_plane_scaling_dt_tau2_n{06,10,14,20}.yaml` (신규), `runs/corl2026_scaling/dt_tau2_n{NN}/` (신규 계보)
**변경:** dt_* config에서 torque_min/max만 ±2.0으로 변경(원 보상·stage-1 레시피·unhealthy 10 동일, 주석에 ablation 목적 명시 — GD는 ±2.7 유지이므로 쌍대가 아닌 "현실적 토크 예산 하 DT" ablation). 웨이브1(시드 42, pid 226558/226568/226614/226660) 시작, 12런 자동 backfill + 완료 시 알림 예정.

## 2026-08-10 — dt_tau2 12런 완료 및 분석: 토크 예산 ablation 결과

**커밋:** (미커밋)
**요청:** (사용자 지시의 자율 완주) dt_tau2(±2.0) 12런 완료 후 기존 계보 대비 분석.
**파일:** `runs/corl2026_scaling/dt_tau2_n{06,10,14,20}/` (12런), `analysis_delta0_vs_dt_tau2/`, `multimetric/data/metrics_dt_tau2.csv`, `analyze_scaling_experiment.py` (--dt-variant tau2 추가)
**변경:** 표본 효율(GD δ=0 vs dt_tau2): n=10 3.24×, n=14 1.60×, n=20 ≥5.06× — 토크 제약이 n=14에서 DT를 부분 정규화(원 DT 7.55M→4.55M 도달)했으나 GD 우위는 전 구간 유지. 물리 지표(nominal): dt_tau2 평균|τ| 1.76(캡 준수), 그러나 **평균|ω| 3.9~5.6 rad/s로 여전히 GD(2.3~2.6)의 1.5~2.4배** — 토크를 줄이자 속도로 대체하는 회피. 모터 τ-ω 엔벨로프 분석(XM430 12V: no-load 5.97 rad/s, stall 3.0 N·m 선형 근사): GD 평균 작동점(1.25 N·m, 2.4 rad/s)은 허용속도 3.5 rad/s 안(실현 가능), dt_tau2(1.76, 5.0)는 허용 2.5의 2배 초과, 원 DT(2.4, 5.2)는 허용 1.2의 4배 초과 — **DT는 토크 예산을 조여도 동시 토크-속도 실현 가능 영역 밖에서 동작**. CoT는 dt_tau2가 n≥14에서 3.0~3.9로 개선(GD 4.3~4.5보다 낮음, 정직 보고). 완주율 n=20 0.33으로 여전히 저조.

## 2026-08-10 — motor-model 계보 시작: DC 모터 back-EMF 액추에이터 물리 도입

**커밋:** (미커밋)
**요청:** DT의 비현실적 움직임(액추에이터 한계 초과)이 나오지 않도록 환경을 조이는 방법 — 보상 페널티 대신 액추에이터 물리 자체를 수정하는 방안 제안·실행(사용자가 env 수정 허용).
**파일:** `horcrux_env/resources_rebuttal/{generate_scalable_mjcf.py(--motor-model 옵션), horcrux_n{10,14,20}_motor.xml, horcrux_plane_n{10,14,20}_motor.xml}`, `horcrux_env/envs/plane_v3_scalable.py`·`plane_direct_torque_scalable.py` (model_variant kwarg, 기본값은 기존 동작), `runs/corl2026_scaling/configs/ppo_plane_scaling_{gd,dt}_motor_n{10,14,20}.yaml`
**변경:** MJCF `<motor>`를 affine bias `<general>`로 교체하는 생성기 옵션 추가 — **τ_net = ctrl − 0.503·ω** (XM430 12V: stall 3.0 N·m, no-load 5.97 rad/s의 선형 DC 모터 근사). 검증: ① 법칙 직접 확인 ctrl=3.0에서 ω=0→τ3.0 / ω=3→1.49 / ω=5.97→0 / ω=8→−1.02(제동), ② bang-bang 동적 테스트 max|ω| 20.9→6.4 rad/s로 엔벨로프 내 구속, ③ 기존 env 검증 스위트 회귀 통과(model_variant 기본값 무영향). 물리 변경이므로 **양 비교군 공통 적용** — gd_motor/dt_motor 계보(n=10/14/20, n=6 제외, 3시드 예정 = 18런). 웨이브1(dt n10/14/20 + gd n10, 시드 42) 시작. 가설(사용자): 실기체 수준 액추에이터 물리에서는 DT가 학습 실패 또는 급감할 것 — GD는 이미 엔벨로프 내 동작이라 유지 예상. **추가(사용자):** n=6도 포함해 24런(4n × 2군 × 3시드)으로 확장, 시드 단위로 전체 n 동시 실행(동시 6~8런, 코어 초과 감수). 기존 mjcf에는 legacy ideal-torque 설명 주석을 생성기 헤더로 추가·재생성(물리 등가성 재검증 통과), motor 변형에는 back-EMF 설명 주석 추가. n06 motor 파일·config 생성, gd/dt_motor_n06 s42 투입(pid 259092/259102, 동시 6런).

## 2026-08-10 — motor 계보 24런 완료: 가설 판정 및 분석

**커밋:** (미커밋)
**요청:** (사용자 지시의 자율 완주) back-EMF 모터 물리 하 GD/DT 24런(n=6/10/14/20 × 3시드) 완료 후 분석.
**파일:** `runs/corl2026_scaling/{gd,dt}_motor_n*/` (24런), `analysis_motor/`, `multimetric/data/metrics_motor.csv`
**변경:** 표본 효율(GD vs DT, motor 물리): n=6 0.56×, n=10 1.86×, n=14 1.92×, n=20 1.07× — 검열 없음, **양쪽 모두 이전보다 훨씬 빨리 학습(GD n=14 0.65M vs 이상 물리 2.85M)**. 물리 지표: 양 군 모두 평균 관절 속도 1.2~3.0 rad/s로 엔벨로프 내(물리가 강제) — 환경 수정 목적(비현실 동작 차단)은 달성. **사용자 가설("실기체 물리에서 DT 학습 불가")은 기각** — DT도 실현 가능 보행을 학습(n=6 제외: 정지 생존 exploit, 0.001 BL/s로 6000스텝 완주). 다만 GD가 전 n에서 표본 효율 우위 유지(1.1~1.9×), 최고 정책도 GD(n=20: 0.72 m/s, CoT 1.1, 완주 100%, 방향 오차 3.8°). back-EMF의 유효 감쇠가 양 군 학습을 안정화(정규화 효과)한 것으로 해석. 주의: dt n10 CoT 1643은 저변위 시드의 분모 폭주 아티팩트(중앙값 사용 권장). **리부탈 권고: Q5 헤드라인은 논문 물리 기준 원 매트릭스 유지**(격차 단조 증가 2.45×→≥3.65×), motor 계보는 "DT의 극적 우위는 시뮬 물리 허점 산물이며, 실기체 물리에선 사라진다 + GD는 물리 충실도와 무관하게 일관 우위"의 강건성 증거로 활용(단, motor 환경에서 격차 단조 증가는 성립 안 함 — 과장 금지).

## 2026-08-10 — 횡이동 원인 최종 판정 및 진단 런 중단

**커밋:** (미커밋)
**요청:** "그동안 forward/backward는 잘 됐는데 갑자기 횡이동만 나온다"는 사용자 문제 제기 → 원인 확정 후 진단 런 중단 지시.
**파일:** (조사·중단만, 코드 무변경) `runs/corl2026_scaling/diag_*` 5런 중단
**변경:** 전 계보 config의 rotation_norm_cost_weight 전수 조사로 **수수께끼 해소** — 정렬 보행에 성공한 from-scratch 계보(backward 4런·gaitrev 3스테이지·left·right)는 **전부 10.0을 명시**, 기본값 0.5로 성공한 사례는 forward stage-01(Windows, 표본 1)이 유일. Linux에서 0.5로 돌린 10런(스케일링 6 + 진단 4 중간판정)은 전부 횡이동. 결론: **약한 yaw 패널티(0.5)에서는 sidewinding이 지배 어트랙터이고, 정렬 보행은 10.0으로 강제하는 것이 이 프로젝트의 사실상 표준이었음**(forward-01은 희귀 추첨/플랫폼 표본 1). 스케일링 config가 forward 레시피(0.5)를 물려받은 것이 횡이동의 원인이며, heading 계보(10.0)가 올바른 표준 복원. 유예·시맨틱스·모델·코드 가설은 모두 실측 기각(grace15 3/3 횡이동, plane-v0 원본 재현도 횡이동). 진단 런 5개 중단(사용자 지시). 부수 사고: 중단 과정에서 사용자 편집기(gnome-text-editor, train.py) 프로세스를 학습 프로세스로 오인해 종료 — 확인 후 종료 순서를 지키지 못한 실수로 기록.

---

## 2026-08-10 — (이전 항목) 횡이동 원인 3차 진단: 시맨틱스 가설 철회, A/A 재현 실험 설계

**커밋:** (미커밋)
**요청:** 기존 학습도 새 반환문으로 진행했다는 사용자 정정 — 시맨틱스 가설 재검토.
**파일:** `runs/corl2026_scaling/configs/diag_planev0_replica.yaml`, `runs/corl2026_scaling/diag_planev0_replica/`, diag_grace15 시드 43/44 추가
**변경:** 검증 — c87d53d(01 런 당일 커밋)의 step 반환문이 이미 `terminated, truncated` 올바른 형태임을 확인, **시맨틱스 가설 철회**(metadata의 13e0329는 더티 워킹트리로 인한 뒤처진 기록 — train.py/normalize_action.py 부재로 교차 확인). c87d53d→HEAD 잔여 diff는 동작 중립 리팩토링뿐. 남은 후보: ① 유예 실효 15 vs 10, ② 확률적 어트랙터 추첨(원본은 from-scratch 1런뿐), ③ 플랫폼(Windows/Linux) 부동소수점 실현 차이. 검증 확장: diag_grace15 시드 43/44 추가(3시드화), **diag_planev0_replica 시작** — 원본 env 클래스(plane-v0)·원본 설정(unhealthy 30, δ=23 기본값) 그대로 Linux A/A 재현(pid 324379). 판정 로직: replica 횡이동 → 확률/플랫폼 요인, replica 정면 → scalable 스택 내 미발견 차이 존재.

---

## 2026-08-10 — (구 항목, 철회됨) 횡이동 원인 재진단: 종료 시맨틱스(terminated/truncated 슬롯) 차이 발견

**커밋:** (미커밋)
**요청:** 유예 시간이 원인일 것 같지 않다는 사용자 지적 — 파일 비교 재수행.
**파일:** `horcrux_env/envs/plane_v3_scalable.py` (legacy_termination 옵션 추가), `runs/corl2026_scaling/configs/diag_gd_legacy_full_n14.yaml`, `runs/corl2026_scaling/diag_legacy_full_n14/`
**변경:** 기존 forward 계보의 학습 리비전이 metadata.json 기록상 **13e0329(Windows WS)**임을 확인하고 현재 코드와 전수 diff. **결정적 차이: 13e0329의 step()은 `return obs, reward, False, terminated, info` — Gym terminated 슬롯이 항상 False, 뒤집힘 종료가 truncated 슬롯으로 반환**되어 SB3가 가치 부트스트랩(죽음 아님)으로 학습. 현재 코드는 올바른 API(뒤집힘=진짜 terminal, V=0)라 학습 초기 roll 회피 압력이 극단적으로 강해져 sidewinding(저분산 고정 roll 자세) 어트랙터로 수렴한 것으로 추정. 기타 diff는 전부 중립(world XML 색상, np.random→np_random(비활성 경로), 리팩토링). 이전 유예 가설은 부차 요인으로 강등. 검증 설계: 진단 런 2종 병행 — ① grace15만(기존 실행 중), ② grace15+legacy_termination(13e0329 시맨틱스 완전 재현, pid 323088). ②가 정면 수렴하고 ①이 횡이동이면 시맨틱스가 주범으로 확정.

---

## 2026-08-10 — (구 항목) 횡이동 원인 1차 진단: unhealthy 유예 변경 가설

**커밋:** (미커밋)
**요청:** 스케일링 이전 학습은 정면 이동이었는데 이후 학습은 전부 횡이동 — 원인 규명(사용자).
**파일:** `runs/corl2026_scaling/configs/diag_gd_delta23_grace15_n14.yaml`, `runs/corl2026_scaling/diag_grace15_n14/` (진단 런)
**변경:** 기존 forward 계보 정책 실측 — stage 1(01_initial_sb3_baseline)부터 몸통 yaw -3°·이동각 -4°의 정면 보행 확인(사용자 기억 정확). 동일 δ=23·시드 42·예산의 스케일링 런(gd_delta23_n14)은 yaw -90° 횡이동. 전수 대조 결과 학습 동역학 차이는 **unhealthy 유예 하나**: 기존 실효 15스텝(설정 30 + 더블카운트 버그) vs 스케일링 10스텝(버그 수정 + 사용자 요청 강화). 정면 보행도 평균 |roll| 51°로 횡이동과 자세 수준이 유사 → 유예가 초기 탐색의 회복 시간 분포를 바꿔 수렴 어트랙터를 바꾼 것으로 추정(스케일링 6+ 시드 전부 횡이동 = 체계적 효과). 확인 실험: δ=23·n=14·시드 42·unhealthy_max_steps 15 진단 런 시작(pid 320813) — 정면 수렴 시 원인 확정.

## 2026-08-10 — gd_bodyscaled 계보 시작(파동 수 고정 + 정렬 레시피) 및 아카이브 정리

**커밋:** (미커밋)
**요청:** 방향 정렬이 잘 됐던 backward(gaitrev_delta0) config를 베이스로, gait 공간 파라미터를 몸길이에 따라 보정(예전 제안한 파동 수 고정 프로토콜)한 전진 학습 구성. 기존 학습 결과는 안 쓸 것 같으니 corl 디렉토리 안에서 이동(사용자).
**파일:** `runs/corl2026_scaling/configs/ppo_plane_scaling_gd_bodyscaled_n{06,10,14,20}.yaml` (신규), `runs/corl2026_scaling/gd_bodyscaled_n{NN}/` (신규 계보), `runs/corl2026_scaling/archive_20260810/` (기존 36개 run 계보 이동 — 삭제 없음)
**변경:** ① 아카이브: 기존 run 계보 전부(gd_delta23/delta0/heading/motor, dt/heading/tau2/motor, diag_*, _aborted)를 archive_20260810/로 이동, 분석 산출물(analysis_*, multimetric)·configs·README는 최상위 유지. ② 새 계보: backward 레시피 그대로(yaw 패널티 10.0, lr 1e-4 linear→0, n_epochs 10, target_kl 0.04, 28,413,952스텝, unhealthy 30) + joy [1,0,0], gait [e,e,40,40,0]에서 **e = 30×14/n** (n=6→70, 10→42, 14→30, 20→21) — 몸통 위상 스팬 420°로 전 n 동일함을 스모크로 확인. 웨이브1(시드 42, pid 8309/8319/8361/8409) 시작, 완료 시 시드 43/44 자동 backfill 예정. 참고: unhealthy 30은 scalable env에서 정확 30스텝(기존 backward의 실효 15보다 관대) — 정렬은 yaw 패널티가 담당하므로 영향 제한적 예상. **추가(사용자, 야간 자율 위임):** DT 비교군 config 4종(`ppo_plane_scaling_dt_bodyscaled_n*.yaml`) 생성 — GD와 동일 레시피(yaw 10.0, run-3, 28.4M), gait 없음, 토크 ±2.7. dt_bodyscaled 시드 42 웨이브 투입(pid 15266/15277/15318/15366)으로 8런 동시 가동, 24런(GD/DT × 4n × 3시드) 완주까지 자동 backfill + 완료 시 푸시 예정.

## 2026-08-11 — bodyscaled 캠페인 재편: 예산 7.86M 단축, GD/DT 분리 웨이브

**커밋:** (미커밋)
**요청:** 28.4M 학습이 너무 길어 중단하고 7M 수준으로 단축, 모든 시드·모든 n을 GD와 DT 분리 웨이브로 진행(사용자). 이후 "믿고 잔다, 모든 학습을 끝내달라" 야간 전권 위임.
**파일:** `runs/corl2026_scaling/configs/ppo_plane_scaling_{gd,dt}_bodyscaled_n*.yaml` (total_timesteps 28413952→7864320), `archive_20260810/bodyscaled_28M_partial/` (28.4M 부분 산출물 8런 보존)
**변경:** 8런 중단 후 부분 산출물 아카이브(분석 시 final_model 부재로 자동 제외됨). 예산을 stage-1과 동일한 7,864,320으로 단축(사용자 "7M 정도" — 기존 매트릭스와 비교 가능성 유지 목적으로 이 값 선택). 실행 구조: 한 웨이브 = 한 비교군 × 전체 n(4런 동시), GD 12런(시드 42→43→44) 완주 후 DT 12런 순차. GD 시드 42 웨이브 시작(pid 38353/38363/38410/38488), 모니터 재무장. 24런 완료 시 정렬 측정 + 표본 효율 분석 + 푸시 예정.

## 2026-08-11 — bodyscaled 캠페인 24런 완료 및 종합 분석

**커밋:** (미커밋)
**요청:** (야간 전권 위임의 완주 보고) GD/DT × n=6/10/14/20 × 3시드, 7.86M, yaw 패널티 10.0 + 파동 수 고정 gait.
**파일:** `runs/corl2026_scaling/{gd,dt}_bodyscaled_n*/` (24런), `analysis_bodyscaled/` (곡선·표·alignment_feasibility.csv)
**변경:** 24런 완주. **정렬 성공률**: GD n10 3/3·n14 3/3·n20 1/3·n6 0/3, DT n10 3/3·n14 2/3·n20 0/3·n6 0/3. GD 성공 정책 전부 몸통 yaw ±3°(정면 이동 목표 달성). **관절 속도**: GD 2.3~2.5 rad/s(실기체 타당) vs DT 4.0~4.9(한계 5.97 근접·초과 왕복) — DT의 n10 속도 우위(0.55~0.58 m/s vs GD 0.27)는 이상 물리 의존 재확인. 표본 효율(유의미 구간): n=10 DT 0.72×(DT 우세), n=14 GD ≥1.37×. n=6은 파동 수 보정(e=70)에도 양쪽 전멸 — 플랫폼 설계 하한으로 결론. n=20은 7.86M 예산 부족(GD 1/3, backward 검증 레시피는 28.4M이었음) — 필요 시 n20만 28.4M 재실행 권고. 분석 표에서 n=6/20은 F_n 음수로 임계값 로직 퇴화(해당 행 무시, alignment 표가 정본).

## 2026-08-11 — jvlim 계보: 관절 속도 unhealthy 조건 도입 + 1M 고속 반복

**커밋:** (미커밋)
**요청:** 공정 비교를 위해 unhealthy reset 조건에 (DT를 겨냥한) 모터 한계 속도를 추가하고, 빠른 반복을 위해 1M 예산으로 전 매트릭스 학습(사용자).
**파일:** `horcrux_env/envs/plane_v3_scalable.py`·`plane_direct_torque_scalable.py` (jvel_limit kwarg — mixin의 is_terminated에 관절 속도 조건 통합, 기본 None=기존 동작), `runs/corl2026_scaling/configs/ppo_plane_scaling_{gd,dt}_jvlim_n*.yaml` (8종), `{gd,dt}_jvlim_n*/` (계보)
**변경:** SingleEvalTerminationMixin 확장 — jvel_limit(rad/s) 설정 시 임의 관절 |ω|>한계도 roll 이탈과 동일하게 unhealthy로 취급(동일 유예 카운터 공유, 양 비교군 공통 적용). 단위 검증: ω=8→카운트 증가, ω=2→리셋, 기본값 None 회귀 무영향. config: bodyscaled 레시피 + jvel_limit 5.97(XM430 무부하) + total_timesteps 1,000,000. GD 시드 42 웨이브 시작(pid 116751~116854), GD 12→DT 12 순차, 런당 ~15-20분 예상(전체 ~2.5-3h). 주의사항 기록: 유예 카운터 공유라 한계 초과를 unhealthy_max_steps(30스텝=1.5s) 연속으로 유지해야 종료 — 간헐적 초과는 허용되는 설계(결과 보고 시 명시 예정).

## 2026-08-11 — jvel 한계를 즉시 terminate로 정정, 학습 사전 협의 원칙 확립

**커밋:** (미커밋)
**요청:** jvel 한계는 unhealthy 유예가 아니라 즉시 에피소드 종료로(사용자). 아울러 앞으로 학습은 먼저 시작하지 말고 개요·방식을 논의한 뒤 시작하라는 작업 원칙 지시 — 메모리(feedback)에 영구 저장.
**파일:** `horcrux_env/envs/plane_v3_scalable.py` (mixin 수정), jvlim config 주석 갱신, `archive_20260810/jvlim_gracever_partial/` (유예판 4런 부분 산출물)
**변경:** 유예판으로 돌던 gd_jvlim 4런 중단·아카이브. mixin에서 jvel 조건을 유예 카운터에서 분리 — **초과 시 즉시 terminated** (roll 이탈은 기존 유예 30 유지). 검증: ω=8→즉시 종료, ω=2→정상, roll 150°→유예 카운트, 기본값 회귀 무영향, 전체 검증 스위트 통과. 재학습은 사용자 승인 대기.

## 2026-08-11 — jvlim 판정(전멸) 및 bsmotor 캠페인 시작 (back-EMF + 정렬 레시피)

**커밋:** (미커밋)
**요청:** jvlim 결과 보고 후 선택지 논의 → 사용자 승인으로 XM430 모터 물리 적용 학습 시작. XML은 기존 파일 무수정(별도 *_motor.xml 변형 사용)임을 확인 문답.
**파일:** `runs/corl2026_scaling/analysis_jvlim/` (판정 데이터), `configs/ppo_plane_scaling_{gd,dt}_bsmotor_n*.yaml` (8종 신규), `{gd,dt}_bsmotor_n*/` (계보)
**변경:** jvlim(즉시 종료) 24런 판정 — 전 정책이 롤아웃 1~2스텝 사망(첫 스텝 max|ω| 6~10): 이상 물리에서 정지→한 컨트롤 스텝만에 무부하 한계 초과가 가능해 규칙이 모든 토크 사용을 금지하는 효과 → 설계 폐기, 데이터는 보존. 대안(사전 협의)으로 bsmotor 계보 승인·시작: bodyscaled 레시피(yaw 10.0, 파동 수 고정 gait) + model_variant motor(τ=ctrl−0.503ω, 물리로 엔벨로프 강제, jvel 규칙 불필요), 1M × 24런, GD 시드 42 웨이브 시작(pid 150009~150111), GD→DT 분리 순차.

## 2026-08-11 — bsmotor 집중 재편: 아카이브 정리 + 전체 캠페인 README

**커밋:** (미커밋)
**요청:** bsmotor에 집중 — 다른 학습 계보는 아카이브로 이동, 각 정책(캠페인)이 어떻게 수행됐는지 README 작성(사용자).
**파일:** `runs/corl2026_scaling/archive_20260811/` (bodyscaled·jvlim 계보 이동), `runs/corl2026_scaling/README.md` (전면 재작성)
**변경:** 최상위에는 bsmotor 8개 패밀리 + 분석/설정/문서만 유지. README를 캠페인 9개(δ 오지정 → 원 보상 매트릭스 → heading → tau2 → motor → 28.4M 부분 → bodyscaled → jvlim → bsmotor)의 시간순 수행 결과·분석 위치·핵심 교훈 5개(yaw 10.0 표준, 한계는 물리로, DT의 초과 속도 의존, n=6 하한, metadata 주의)로 전면 재작성. bsmotor 7.86M 재실행은 사용자 승인 대기.

## 2026-08-11 — R6 도메인 랜덤화 강건성 평가 (dr_robustness)

**커밋:** (미커밋)
**요청:** 가장 학습이 많이 된 전진 정책(policies/path_tracking/forward/05_forward_x_long, 47.6M step)을 활용해 R6(도메인 랜덤화 강건성, Hhic Q4·Ntmk W2) 실험을 재학습 없이 평가만으로 수행. corl 실험 디렉토리 하위에 결과 저장.
**파일:** `runs/corl2026_scaling/dr_robustness/` (신규 — evaluate_dr_robustness.py, plot_dr_robustness.py, data/, figures/, README.md)
**변경:** 평가 전용 DR 스윕 101 롤아웃(8워커 병렬, horizon 3000, 결정론 정책). 마찰 μ~U(0.65±δ), δ∈{15,30,45,60}% / 액추에이터 지연 d~U(0,x), x∈{10..50}ms (do_simulation을 5ms 물리 프레임 단위로 분해해 직전 제어 유지로 구현) / 결합(δ30%+30ms). 결과: 마찰 ±60%에서도 리턴 89% 유지·완주 100%(매우 강건), 지연은 실제 15ms까지 83%→20ms 55%→25ms(제어주기 절반) 이상 리턴 붕괴(이동거리는 ~40% 유지, 낙상 없음). 결합 53%/67%. 그림 2장 + 레벨별 요약 CSV 생성.

## 2026-08-11 — bsmotor 7.86M 캠페인 시작

**커밋:** (미커밋)
**요청:** 스케일링 MJCF는 이 실험 전용이라 병렬 작업과 충돌 없음 확인 후 7M(=7.86M) 학습 승인(사용자). 병렬로 별도 세션에서 리부탈 실험(dr_robustness 등) 진행 중.
**파일:** bsmotor config 8종(total_timesteps 7864320), `archive_20260811/bsmotor_1M/` (1M 시도 24런 이동 — 새 run과 분석 혼입 방지)
**변경:** 1M run 디렉토리 24개를 resolved_config 기준으로 선별해 아카이브. GD 시드 42 웨이브 시작(pid 181936~182073), GD 12→DT 12 순차, 런당 ~1.5-2h 예상(전체 ~12-14h). 완료 시 정렬·표본 효율·실현성 분석 + 푸시 예정.

## 2026-08-11 — R6 그림 MATLAB 이식 (dr_robustness/matlab)

**커밋:** (미커밋)
**요청:** R6 figure를 사용자가 MATLAB에서 직접 수정할 수 있도록 m 파일 + 데이터 mat 파일 생성.
**파일:** `runs/corl2026_scaling/dr_robustness/matlab/` (신규 — export_mat.py, dr_data.mat, plot_dr_retention.m), `runs/corl2026_scaling/dr_robustness/README.md` (파일 목록 갱신)
**변경:** dr_raw.csv를 scipy savemat로 변환(raw 101 에피소드 + 레벨별 유지율 mean/std 집계 + 지연 산점도 배열 + nominal 기준값·상수). plot_dr_retention.m은 파이썬 그림 2장(3패널 유지율, 지연 산점도)을 동일 색·구성으로 재현하며 집계가 mat에 들어 있어 순수 플로팅만 수행(스타일 파라미터 상단 분리, R2016b+ 로컬 함수 사용). 라운드트립 값 검증 완료, MATLAB 미설치라 실행 검증은 사용자 몫.

## 2026-08-11 — R6 ABCD 4패널 그림 (X-Y 궤적 패널 D 추가)

**커밋:** (미커밋)
**요청:** ABC 유지율 그림에 실제 전진 정책의 X-Y 이동 궤적 패널(D)을 추가해 4패널로 구성 (MATLAB 버전은 보류, 요청 시 진행).
**파일:** `runs/corl2026_scaling/dr_robustness/record_trajectories.py`·`plot_dr_abcd.py` (신규), `data/trajectories.npz`, `figures/dr_retention_abcd.png`, README.md 갱신
**변경:** 대표 조건 7개(nominal, μ=0.26/1.04, 지연 10/20/30ms, 결합 μ=0.466+30ms)를 명시적 파라미터로 재롤아웃해 CoM 궤적 기록(3000스텝, 결정론). 4패널 그림(사용자 요청으로 1행 A|B|C|D 배치, D는 X-Y 평면이므로 axis equal 1:1 비율): 단축 레이블 적용(friction range ±δ (%), max actuator delay (ms), retention (nominal = 1)), D는 조건 유형별 색(회색/aqua/보라 램프/빨강), 범례는 우하단 빈 영역에 1열 배치. 궤적이 붕괴 양상 규명: 지연 30ms·고마찰은 낙상이 아니라 방향 이탈(-Y 대각)로 실패. δ60% 실추첨 최대 μ=0.957(81%)와 경계값 μ=1.04(45%, 대각 이탈)의 정합성 확인 — 고/저마찰 비대칭 존재, README에 명시.

## 2026-08-11 — R6 그림 재구성: 궤적 패널 A로 이동, 15초 롤아웃, 마찰 눈금 통일

**커밋:** (미커밋)
**요청:** 궤적 패널을 D→A로 이동, 궤적의 마찰 조건을 유지율 패널과 같은 눈금(0/+15/+30/+45/+60%)으로 통일, 롤아웃을 약 15초로 단축.
**파일:** `record_trajectories.py` (조건 9개·TRAJ_HORIZON=300), `plot_dr_abcd.py` (패널 순서 A=궤적/B=마찰/C=지연/D=결합), `data/trajectories.npz`·`figures/dr_retention_abcd.png` 재생성, README 갱신
**변경:** 궤적을 15초(300 step)로 재기록 — nominal 7.1 m 직진, 마찰 +15~+60%(aqua 명암 램프) 6.7→5.8 m로 완만 감속·직진 유지, 지연 10 ms는 nominal과 포개짐, 지연 30 ms·결합(보라 램프·빨강)은 -Y로 이탈(X ~2.9 m). "+50%"는 기존 눈금(60%)의 오타로 해석해 +60% 적용. 범례는 우하단 빈 영역에 앵커 고정(3회 렌더링 확인으로 겹침 해소).

## 2026-08-11 — R6 패널 A 마찰 전용 정리 + Y축 0 중심 대칭

**커밋:** (미커밋)
**요청:** 패널 A(X-Y 궤적)에서 마찰 계수 변화만 남기고 지연·결합 제거, 축 1:1 유지하되 Y축은 0이 중간에 오도록 [-2.5, 2.5] 대칭 범위로.
**파일:** `plot_dr_abcd.py`, `figures/dr_retention_abcd.png` 재생성, README 갱신
**변경:** 패널 A를 마찰 계열 5개(nominal, μ +15~+60% aqua 램프)만 플롯. ylim(-2.5, 2.5) + axis equal — 횡드리프트가 최대 -0.7 m뿐이라 0 중심 대칭에서 직진성이 명확히 드러남. 지연·결합 궤적 데이터는 trajectories.npz에 보존(플롯만 제외). 범례는 마찰 5개 항목만 우하단 3열 배치.

## 2026-08-11 — R6 그림 정렬 마무리: 제목 정렬·패널 A 정방형·x축 정렬

**커밋:** (미커밋)
**요청:** 패널별 제목 텍스트 높이 정렬, A를 정방형(1:1 스케일 유지)으로, A의 x축을 B/C/D와 정렬.
**파일:** `plot_dr_abcd.py`, `figures/dr_retention_abcd.png` 재생성
**변경:** 원인은 axis equal로 A의 축 상자가 세로 수축·중앙 배치되던 것 — X·Y 범위를 동일한 8.2 m(xlim -0.6~7.6, ylim -4.1~4.1, 0 중심 유지)로 잡고 set_box_aspect(1)을 추가해 정방형 상자가 셀 높이를 채우게 함 → 제목 상단·x축 하단이 B/C/D와 자동 정렬. D의 2줄 제목도 어긋남 원인이라 "D. Combined" 한 줄로 줄이고 조건(δ=30% + ≤30 ms)은 패널 내부 회색 주석으로 이동(오차 막대와 겹치지 않게 막대 사이 배치). figsize (17,4)→(15,4), A 폭 비율 3.3으로 축소.

## 2026-08-11 — R6 그림: C 범례 추가, D를 단독 vs 결합 3그룹 비교로 재구성

**커밋:** (미커밋)
**요청:** C에 B와 같은 범례 추가, B/C 음영(±1 s.d.)과 에피소드 수 정보 명시, D의 의미 전달 개선(3그룹 비교 추천안 채택).
**파일:** `plot_dr_abcd.py`, `figures/dr_retention_abcd.png` 재생성, README 갱신
**변경:** B·C 범례에 시리즈 2개 + 회색 패치("±1 s.d. (10 episodes/level)") 추가, C에도 동일 범례 표시. D를 "D. Single vs. combined"로 재구성 — μ ±30% / delay ≤30 ms / both 3그룹 × 2지표 막대(그룹 내 간격 포함): 단독 99%/80~87% vs 결합 53~67%로 결합 스트레스의 초가산적 저하가 한 패널에서 읽히도록. D 폭 비율 1.1→1.9, figsize (15.8, 4). 후속 요청으로 D에도 범례 추가 — 파랑/주황 패치 + 검정 오차막대 프록시("±1 s.d. (10 episodes/cond.)"), ylim 상한 1.42로 올려 좌상단에 배치.

## 2026-08-11 — R6 확정 4패널 그림 MATLAB 이식

**커밋:** (미커밋)
**요청:** 확정된 ABCD 4패널 그림을 MATLAB 파일로 생성.
**파일:** `runs/corl2026_scaling/dr_robustness/matlab/export_mat.py` (궤적 5개 traj_* + D 3그룹 집계 sv_* 필드 추가), `dr_data.mat` 재생성, `plot_dr_abcd.m` (신규), README 갱신
**변경:** plot_dr_abcd.m이 파이썬 dr_retention_abcd.png와 동일한 1행 4패널을 재현 — A: 궤적(daspect+pbaspect 1:1 정방형, X/Y 8.2 m 동일 범위), B/C: 유지율 곡선+음영(±1 s.d. 회색 패치 범례 포함), D: 단독 vs 결합 3그룹 막대(오차막대 프록시 범례). tiledlayout(1,16)을 5/4/4/3 칸으로 분할해 폭 비율 근사. bar 폭 인자 중복·tex 미지원 \blacksquare(char(9632)로 대체)·다중행 틱 라벨 등 MATLAB 문법 이슈 사전 수정. mat 라운드트립 값 검증 완료(sv 집계 = 그림 수치 일치), MATLAB 미설치라 실행 검증은 사용자 몫. 구버전 plot_dr_retention.m은 보존.

## 2026-08-11 — P1 준비: compare_gd_openloop 정리 + open-loop 최적 파라미터 도출

**커밋:** (미커밋)
**요청:** GD vs open-loop 비교 실험(P1) 준비 — compare_gd_openloop 폴더 정리, serpentine/sidewinding open-loop 코드 확인, 최적 파라미터 도출(사용자가 하드코딩 값 존재 언급, xml 모델은 사용자가 models/에 수집).
**파일:** `runs/corl2026_scaling/compare_gd_openloop/` — README.md·optimal_params.yaml·run_openloop.py (신규), openloop_head_trajectories.npz (스모크 산출물)
**변경:** open-loop 본체는 open_loop_controller/mjx_grid_search.py (Hirose serpenoid + 모션행렬 m_serp/m_side/m_ones)로 확인. 최적 파라미터는 하드코딩("OP", 719-721행)과 그리드서치 .mat argmax가 일치 — serpentine [233,18,φ180]→(A 0.8/1.2 rad, ω 5.97/3.18 rad/s, ν 234°/19°), sidewinding [220,198,φ0]→(0.9/1.3, 동일 ω, 221°/199°). side는 φ=19° 근소 우세 대안 존재(기본은 하드코딩 버전). snake_circle_contact_servo.xml 로드 검증 + 14 s 스모크 롤아웃 성공(serp +X 0.69 m, side Y 1.24 m — 게이트 특성 재현). 비교 모델/재최적화/지표는 사용자 합의 대기.

**교정 (사용자 지적: serpentine δ=0, sidewinding δ=45여야 함):** Hirose 표기(mjx_grid_search)는 다른 파라미터 체계로 폐기. 올바른 체계는 GD 논문 serpenoid (a_d,a_l,e_d1,e_l1,e_d2,e_l2,δ,Ts) — GD_paper_rev의 5개 스크립트(test.py:796~ 등) 하드코딩과 opti_step/op_*.mat Motion_lambda가 일치: **serpentine_op (45,45,19,19,59,59,0), slithering_op (45,45,15,15,56.5,28.25,0), sidewinding_op (45,45,27,27,53,53,45)**. 대안 계열(traj_J.py REV2 재최적화, ac_* 가속도 포함, scipy 파인튜닝)도 yaml에 기록. run_openloop.py를 serpenoid.Gait 기반(curve=순수/mat=Gk 게이팅)으로 재작성, env_snake_v1_contact_servo.xml 10 s 스모크 성공 — 단 serpentine curve의 진행 방향 대각 드리프트 관찰(과도응답/변형 선택은 설계 시 확인 필요).

## 2026-08-11 — open-loop curve 롤아웃 화면 녹화

**커밋:** (미커밋)
**요청:** curve 계열 확정, 실험 결과를 확인할 수 있게 화면 녹화.
**파일:** `compare_gd_openloop/record_openloop_videos.py` (신규), `videos/*.mp4` 6개, README 갱신
**변경:** 두 계열(표준 op / traj_J op) × 3게이트를 curve 변형으로 10 s 롤아웃하며 head 추적 카메라(EGL 헤드리스, 960×540, 50 fps 실시간)로 mp4 저장. 10 s 변위 — std: serp (+0.44,+0.79) 대각, slit (+0.27,−1.89) −Y, side (+2.44,+2.24) / trajJ: serp (−0.10,+0.03) 정체, **slit (+1.71,+0.13) 깨끗한 +X 전진**, **side (+6.61,−5.59) 최고속(0.87 m/s)**. 프레임 추출로 렌더링 품질 검증 완료.

## 2026-08-11 — P1 본 실험: GD-RL vs 최적화 open-loop 비교 완료

**커밋:** (미커밋)
**요청:** trajJ_slithering_op·std_sidewinding_op(curve)를 open-loop 비교군으로, GD forward·left 정책과 CoT/방향 유지/속도/궤적 4지표 10시행 비교. 개루프 편차는 초기 위상 랜덤 + 1% 명령 노이즈(합의안).
**파일:** `compare_gd_openloop/evaluate_comparison.py`·`plot_comparison.py` (신규), `data/comparison_{raw,summary}.csv`·`trajectories_comparison.npz`, `figures/comparison_{trajectories,metrics}.png`, README 갱신
**변경:** 조건당 10시행 × 10 s (open-loop: t0~U(0,1.2 s)+N(0,0.028 rad), GD: 결정론+정규화 액션 노이즈 N(0,0.02)), 무차원 지표 중심(다른 모델: servo vs 토크). 결과 — GD forward 0.475 BL/s·오차 3.4°·CoT 5.75 vs OL slithering 0.177·8.4°·45.5 / GD left 0.611·1.9°·4.05 vs OL sidewinding 0.332·33.4°·11.0. **GD가 속도 2.7×/1.8×, CoT 7.9×/2.7×, 방향 오차 2.4×/17× 우세.** 궤적 오버레이·지표 막대 그림 생성(렌더링 검증).

## 2026-08-11 — P1 그림 개편: 명령 정렬 프레임·명칭 통일·스냅샷·성능 맵

**커밋:** (미커밋)
**요청:** ① 횡이동도 전진처럼 +X로 표현(머리 −Y 배치와 동치), ② 게이트 원형 명칭 통일(GD serpentine/sidewinding, OL slithering→serpentine), ③ 천장 수직 카메라 정방형 스냅샷 롤아웃당 6장(리뷰어용), ④ 막대 대신 인상적인 그래프.
**파일:** `plot_comparison.py` (개편), `record_snapshots.py` (신규), `figures/comparison_{trajectories,performance_map,metrics,snapshots}.png`, `figures/snapshots/*.png`, README 갱신
**변경:** ① 횡이동 쌍은 플롯에서 월드 −90° 회전(명령 정렬 프레임; open-loop은 물리 회전과 완전 동치, GD는 관측 분포 보존을 위해 표현만 회전)해 궤적 그림을 2행 공유 X축으로 재구성. ② 전 그림·README 명칭 교체. ③ trial 0 동일 시드 재현 롤아웃에서 탑다운(elevation −90) 720² 스냅샷 t=0~10 s 6장 × 4조건 + 4×6 몽타주 — 카메라는 궤적 bbox 자동 커버, 횡이동은 azimuth 180으로 명령=화면 오른쪽 통일(GD env는 offscreen 버퍼 확장 필요했음). ④ 신규 성능 맵: (A) 속도 vs CoT(log) 시행별 산점 + ideal 코너 화살표 — GD sidewinding이 이상 코너 점유, (B) 방향 나침반(극좌표, 각도=명령 편차·반경=속도) — GD 0° 밀집 vs OL sidewinding −20~−55° 부채꼴. 막대 그림은 보조로 유지. 전 그림 렌더링 검증.

## 2026-08-11 — P1 스냅샷·산점도 다듬기 (배경 통일, 공통 카메라, 그리드·눈금)

**커밋:** (미커밋)
**요청:** ① OL xml의 바닥 체커 색을 GD와 동일하게(수정 허용), ② 스냅샷 카메라를 4조건 동일 위치·스케일로, ③ CoT 산점도에 그리드, ④ y축 "4×10⁰"식 눈금을 자연스럽게.
**파일:** `GD_paper_rev/resources/env_snake_v1_contact_servo.xml` (texplane rgb .55/.75·mark 제거·reflectance 0·texrepeat 1 — 물리 무관 시각만), `record_snapshots.py` (공통 카메라: 4조건 trial-0 궤적 합집합 뷰 프레임으로 lookat·거리 통일, GD env 헤드라이트 밝기 OL과 일치), `plot_comparison.py` (그리드 + ScalarFormatter 눈금 4/6/10/20/40), 그림 재생성
**변경:** 몽타주 4행이 동일 배경·동일 스케일·동일 구도가 되어 행간 이동거리 직접 비교 가능(GD 두 행은 화면 우단 도달, OL serpentine은 1/3 지점, OL sidewinding은 우하향 이탈). 산점도는 회색 그리드(뒤) + 자연수 눈금.

## 2026-08-11 — P1 다중노출(크로노포토) 합성 그림

**커밋:** (미커밋)
**요청:** 4×6 몽타주는 지면을 너무 차지 — 스냅샷을 다중노출처럼 1장에 합성하고, 그 위에 사진과 같은 비율(미터 스케일)의 X-Y 궤적 + 스냅샷 시점 점을 얹은 그림.
**파일:** `compare_gd_openloop/make_multiexposure.py` (신규), `figures/comparison_multiexposure.png`, README 갱신
**변경:** 공통 카메라 스냅샷 6장에서 픽셀 중앙값으로 배경 추정 → 색 차 임계 마스크로 로봇 픽셀만 추출 → 시간순 알파 램프(0.4→1.0, 이른 포즈일수록 반투명)로 1장에 합성. 상단에 같은 가로 범위·equal aspect 궤적 스트립(스냅샷 시점 6개 ● 표시)을 정렬. 조건 4열 × (스트립+사진) 구성, 사진은 유효 영역(-3.4~1.3 m)으로 세로 크롭. 렌더링 검증 완료 — GD 두 열은 포즈가 화면 끝까지 등간격 전진, OL serpentine은 1.7 m에 밀집, OL sidewinding은 우하향 곡선 이탈이 한눈에 보임.

## 2026-08-11 — P1 통합 다중노출: 궤적 오버레이 + 게이트별 GD/OL 합성 2패널

**커밋:** (미커밋)
**요청:** 궤적을 사진 위에 직접 표현하고, 같은 게이트의 OL·GD를 한 그림에 합쳐 2개 그림으로 축약.
**파일:** `compare_gd_openloop/make_multiexposure_merged.py` (신규), `figures/comparison_multiexposure_merged.png`, README 갱신
**변경:** 게이트별(serpentine/sidewinding)로 GD·OL 스냅샷 잔상을 한 배경(GD 조건의 중앙값 배경)에 합성 — 두 조건이 공통 카메라 뷰 프레이밍을 공유해 픽셀↔미터 대응이 성립. 제어기 구분을 위해 로봇 픽셀에 색 틴트 35%(GD 파랑/OL 주황) + 시간순 알파 램프 유지. CoM 궤적(선+스냅샷 시점 ●)을 imshow 위에 데이터 좌표로 직접 오버레이, 반투명 흰 배경 범례. 2패널 상하 배치(공유 X축, figsize 10.5×5.6)로 기존 4열 대비 지면 추가 절약. 4열 버전(comparison_multiexposure.png)은 대안으로 보존.

## 2026-08-11 — P1 궤적 그림 정방형 1행 재배치

**커밋:** (미커밋)
**요청:** comparison_trajectories를 정방형 패널로 바꾸고 1행(좌우)으로 나열.
**파일:** `plot_comparison.py`, `figures/comparison_trajectories.png` 재생성
**변경:** X(-0.6~7.2)·Y(-3.9~3.9, 0 중심 대칭) 동일 스팬 7.8 m + set_box_aspect(1)로 두 패널 모두 정방형·1:1 스케일, 1행 2열 배치(figsize 11×5.6). 범례는 양쪽 모두 빈 우상단, suptitle 간격 조정. 렌더링 검증 완료.

## 2026-08-11 — P1 성능 맵 패널 A 다듬기 (로그 minor 그리드·정방형·범례 박스)

**커밋:** (미커밋)
**요청:** A(속도–CoT 산점)에 minor 그리드를 추가해 로그 스케일임을 명확히, 패널 정방형화, 범례에 박스 추가.
**파일:** `plot_comparison.py`, `figures/comparison_performance_map.png` 재생성
**변경:** LogLocator(subs 2~9) minor 눈금 + 연회색(#ececec) minor 그리드(major #d5d5d5와 구분), set_box_aspect(1) 정방형, 범례 frameon(흰 배경·회색 테두리·framealpha 0.95). 그리드 간격이 위로 갈수록 압축되어 로그 스케일이 시각적으로 드러남.

## 2026-08-11 — P1 3그림 통합 1행 최종본 (comparison_combined)

**커밋:** (미커밋)
**요청:** multiexposure_merged·trajectories·performance_map 3그림을 1행 한 장으로 합치고 제목·축 설명 컴팩트화.
**파일:** `compare_gd_openloop/plot_combined_row.py` (신규, 기존 스크립트의 헬퍼·합성 함수 재사용), `figures/comparison_combined.png`, README 갱신
**변경:** 사용자 배치 교정 반영 — [다중노출 상하] [궤적 정방형 좌우] [성능 맵 좌우]의 진짜 1행: 2×5 그리드(figsize 17.5×3.9), 열1만 내부 2단((a),(b) 다중노출), (c)(d)(e)(f)는 전체 높이 스팬. 제목은 (a)~(f) 패널 문자 + 최소 문구, 축은 x/y (m)·speed (BL/s)·CoT (log)로 압축, 범례는 (a) 제어기 색 2항목·(e) 게이트×제어기 4항목만. 정방형 패널이 스팬 셀 중앙에 떠서 제목이 어긋나는 문제를 set_anchor('N')으로 해결((f) 폴라는 제외 — 앵커 시 suptitle 침범), 3회 렌더링 반복으로 제목 라인 정렬 확인.

## 2026-08-11 — P1 통합 그림 축 정렬 마무리

**커밋:** (미커밋)
**요청:** 제목은 정렬됐지만 그래프 축 상자가 어긋남 — 축 정렬 수정.
**파일:** `plot_combined_row.py`, `figures/comparison_combined.png` 재생성
**변경:** box_aspect/anchor 방식(상자가 셀보다 작아 중앙 부유) 폐기. (c)(d)는 fig.canvas.draw() 후 셀의 실제 종횡비를 측정해 y 범위를 두 패널 동일하게 산출(±7.8·ratio/2) → 1:1 스케일을 유지하면서 상자가 셀을 정확히 채움. (e)는 aspect 기본(셀 채움). 중간에 시도한 adjustable="datalim"은 패널별 범위가 제각각 바뀌는 문제(원점 마커 잘림, c·d 범위 불일치)로 폐기. 결과: (a)~(f) 제목 라인과 축 상자 상·하단 모두 정렬, (c)(d) 동일 범위 유지.

## 2026-08-11 — P1 통합 그림 마이너: 메인 타이틀 제거·정보 재배치·(c)(d) 그리드

**커밋:** (미커밋)
**요청:** 메인 타이틀 제거(정보는 그림 안으로 — 예: 2초마다 노출), (c)(d)에 major 그리드.
**파일:** `plot_combined_row.py`, `figures/comparison_combined.png` 재생성
**변경:** suptitle 삭제 후 정보 재배치 — 노출 간격·잔상 의미는 (b) 하단 흰 주석("poses & ● every 2 s (fainter = earlier)"), 롤아웃 길이는 (c)(d) 제목("10 trials × 10 s"), 명령 방향은 (a) 흰색·(c) 회색 "command →" 라벨(기준선 옆). (c)(d)에 연회색 major 그리드 추가(set_axisbelow). 주석이 (a) 범례와 겹치던 첫 시도는 (b)로 이동해 해결, 렌더링 검증 완료.

## 2026-08-11 — P1 통합 그림: command 라벨 제거·안내 문구 강조

**커밋:** (미커밋)
**요청:** (a)·(c)의 "command →" 텍스트 삭제, 안내 문구를 쨍한 파랑 볼드로.
**파일:** `plot_combined_row.py`, `figures/comparison_combined.png` 재생성
**변경:** command 라벨 2곳 제거(명령 방향은 캡션 담당으로), (b)의 "poses & ● every 2 s (fainter = earlier)" 주석을 #0d6bff 볼드로 변경. 렌더링 확인 완료.

**후속 교정:** 파랑 별로 + 문구 단축 요청 → "exposure every 2 s" 검정 텍스트 + 범례와 동일한 반투명 흰 배경 박스(alpha 0.85)로 변경. (b) 우하단 배치, 렌더링 확인 완료.

## 2026-08-11 — P1 통합 그림: (c)(d) 범례 + 시행 노이즈 표기

**커밋:** (미커밋)
**요청:** (c)(d)에 범례 추가, 10시행에 어떤 노이즈를 줬는지 대략 표기.
**파일:** `plot_combined_row.py`, `figures/comparison_combined.png` 재생성
**변경:** 범례 라벨에 노이즈 정보를 통합 — "GD-RL — 1% action noise" / "open-loop — 1% ctrl noise + rand. phase". (c)(d) 모두 상단(궤적 없는 영역)에 박스 범례((e)와 동일 스타일), 렌더링 확인 완료. 후속: 범례가 길어 "open-loop — 1% ctrl noise"로 단축(랜덤 위상은 캡션 담당).

## 2026-08-12 — bsmotor 7.86M 캠페인 완료: 최종 판정

**커밋:** (미커밋)
**요청:** (승인된 캠페인의 완주 보고) back-EMF 물리 + 정렬 레시피 + 파동 수 고정, 24런.
**파일:** `runs/corl2026_scaling/{gd,dt}_bsmotor_n*/` (7.86M 24런), `analysis_bsmotor7M/` (곡선·표·alignment_feasibility.csv)
**변경:** 24런 완주(6슬롯 야간 자동 진행). GD 최종 성능이 n과 함께 단조 증가(F_n 8.7k→47k→95k→158k, 전 캠페인 중 유일) — 모터 감쇠가 긴 체인을 안정화. 정렬: GD n≥10 **9/9 시드 정면 보행**(yaw ≤5°, |ω| 1.1-1.9 rad/s), DT n≥10 8/9(yaw ≤8°, |ω| 2.5-3.1 — 물리 덕에 전 정책 엔벨로프 내). **정직 판정: 이 체계에서는 DT가 표본 효율(도달 스텝 0.52~0.81×)과 최고 속도(n=20에서 0.92 vs GD 0.59 m/s) 모두 우세** — 물리가 실현 가능성을 강제하는 순간, prior의 제약 비용이 이 예산에서는 이득을 상회. GD의 잔여 우위는 시드 일관성(9/9 vs 8/9)과 보수적 관절 속도. n=6은 양쪽 모두 보행 실패(GD는 정지 생존 습득) — 설계 하한 재확인. 리부탈에는 논문 물리 기준 원 매트릭스가 여전히 정본이며, bsmotor 결과는 저널 확장판의 "actuator 충실도가 prior 이득에 미치는 영향" 논의 자료로 분류 권고.

## 2026-08-12 — bsmotor GD 보존 + 링크 정렬(대칭성) 보상 항 구현

**커밋:** (미커밋)
**요청:** 잘 학습된 bsmotor GD를 섞이지 않게 보관. DT는 U자 자세로 heading 패널티(chordal 평균 yaw의 좌우 상쇄 허점)를 우회 중 — 각 링크의 오리엔테이션을 개별 반영하는 보상 항 설계(사용자).
**파일:** `policies/corl2026_scaling/bsmotor_gd/` (GD 12런 + README + 성능 CSV 이동 보존), `horcrux_env/envs/plane_v3_scalable.py`(link_alignment_cost 헬퍼 + link_align_cost_weight kwarg), `plane_direct_torque_scalable.py`(동일 반영)
**변경:** ① GD 12런을 policies 트리로 이동, README에 설정·성능표·사용법 기록. ② 신규 비용 항: mean_i(1 − cos(링크 i x축 vs joy 방향)) × weight — 링크별 계산이라 U자 우회 불가, serpenoid 파동은 허용. 검증: 직선 0.000 / 파동 ±30° 0.034 / U자(누적 210°) 1.058, step 통합·기본값(0) 회귀 무영향·전체 스위트 통과. DT 재학습은 계획 제시 후 승인 대기.

## 2026-08-12 — dt_bsmsym 캠페인 시작 (링크 정렬 항 적용 DT 재학습, 8런 동시)

**커밋:** (미커밋)
**요청:** 링크 정렬 항 가중치 30으로 DT 재학습, 8런 동시 실행(사용자 승인).
**파일:** `runs/corl2026_scaling/configs/ppo_plane_scaling_dt_bsmsym_n*.yaml` (4종 신규), `dt_bsmsym_n*/` (계보)
**변경:** bsmotor DT 설정 + link_align_cost_weight 30.0, 7.86M, 12런(4n × 3시드). 웨이브1 = 8런 동시(전 n × 시드 42/43, pid 609696~610019), 완료분부터 시드 44 backfill. 스모크: back-EMF + link_align 30 + info cost 기록 확인. 비교 기준은 보존된 bsmotor GD (policies/corl2026_scaling/bsmotor_gd — GD의 링크 정렬 비용은 파동 수준 ~1/스텝이라 무시 가능, 필요 시 GD 동일 항 재학습 별도 결정).

## 2026-08-12 — bsmotor_dt 보존본 README 작성

**커밋:** (미커밋)
**요청:** policies/corl2026_scaling에 보존된 스케일링 정책(GD/DT) 확인 후, README가 없던 DT 대조군 폴더에 문서 작성.
**파일:** `policies/corl2026_scaling/bsmotor_dt/README.md` (신규)
**변경:** bsmotor_gd README와 같은 형식 — GD와의 차이(direct-torque env, prior 없음, ±2.7 N·m)만 분리하고 공통 설정(motor 물리, yaw 10.0, run-3 레시피 7.86M, 시드 42/43/44)·성능 표(alignment_feasibility.csv DT 12행)·정직 판정(이 물리에서는 DT 우세, GD 잔여 우위는 시드 일관성·보수적 |ω|)·용도 분류를 기록. 확인 결과 12런 전부 final_model 존재(완결), 현재 학습 중인 것은 별도 후속 계보 dt_bsmsym(8프로세스)임을 명시.

## 2026-08-12 — compare_gd_dt: 관절 수 스케일링 다중노출 3패널

**커밋:** (미커밋)
**요청:** bsmotor GD vs DT를 n=10/14/20 다중노출(merged 방식)로 3패널 좌우 배열, 각 조건 최고 리턴 시드 사용, 자료는 runs/corl2026_scaling/compare_gd_dt에 정리.
**파일:** `runs/corl2026_scaling/compare_gd_dt/` — record_snapshots_gd_dt.py·make_multiexposure_gd_dt.py·README.md (신규), data/trajectories_gd_dt.npz, figures/snapshots/*.png(36장), figures/gd_dt_multiexposure.png
**변경:** 시드 선택 = evaluations.npz 최대 평균 리턴(GD/DT 모두 n10→s43, n14→s44, n20→s43). 2패스 기록(궤적→공통 카메라 프레이밍 산출→재현 assert 후 720² 탑다운 6장/런), 10 s 결정론 롤아웃(노이즈 없음). 합성은 merged 방식(배경 중앙값+마스크, GD 파랑/DT 주황 35% 틴트, 알파 0.4→1.0) + CoM 궤적·● 오버레이. 1×3 공통 스케일(half extent 5.13 m), 세로 크롭 ±1.4 m. 변위: GD 1.2/2.8/5.3 m vs DT 3.0/4.9/8.7 m (n10/14/20) — README에 "이 물리에서는 DT가 멀리 감, 캡션에서 원 매트릭스와의 관계 설명 필수" 명시.

## 2026-08-12 — compare_gd_dt 개편: DT 최악 시드 + |ω| 패널 추가

**커밋:** (미커밋)
**요청:** DT는 최악(최저 리턴) 시드의 다중노출로 교체, |ω| 비교 패널을 왼쪽에 추가.
**파일:** `record_snapshots_gd_dt.py` (DT 시드 교체: n10 s44 11.6k·n14 s43 147k·n20 s44 238k), `make_multiexposure_gd_dt.py` ((a) |ω| 패널 + (b~d) 재배치), 스냅샷·npz·`figures/gd_dt_multiexposure.png` 재생성, README 갱신
**변경:** 1×4 구성 — (a) alignment CSV 시드별 평균 |ω| 점(표시 시드 채운 마커, 나머지 반투명, XM430 무부하 5.97 한계선): GD 1.4~1.9 vs DT 2.5~3.1 rad/s 대비. (b~d) GD 최고 vs DT 최악: 10 s 변위 GD 1.2/2.8/5.3 m vs DT 0.0(보행 실패)/3.4/4.6 m — n10에서 DT 정체, n20에서 GD 우세 역전. 그림 높이 2.35in로 (a)와 사진 축 정렬. 범례 라벨에 시드 기준 명시("best seed"/"worst seed").

## 2026-08-12 — compare_gd_dt 재편: 상하 배치·제목 교체·CoT 패널

**커밋:** (미커밋)
**요청:** |ω| 패널 제거(가시성), 다중노출 3장 상하 배치, 제목에서 n 기호 제거("10 joints" 식 — n이 다른 그림에서 시행 수로 쓰임), CoT 비교를 전 관절 수로 추가.
**파일:** `evaluate_cot.py` (신규 — 24런 CoT 평가), `data/cot_gd_dt.csv`, `make_multiexposure_gd_dt.py` (재구성), `figures/gd_dt_multiexposure.png`, README 갱신
**변경:** 3×2 그리드 — 좌 (a)(b)(c) 다중노출 상하(x라벨은 최하단만), 우 (d) CoT vs 관절 수(시드별 반투명 점 + 평균 선, 실패 런 NaN 제외). CoT 결과: GD 4.6/4.6/2.6/2.2 vs DT 17.2/4.9/3.3/2.0 (n=6/10/14/20) — n≤14 GD 효율 우위(n6 3.7×), n20 동등. GD n6은 유효 1시드뿐임을 README 명시.

## 2026-08-12 — compare_gd_dt_heading: only_heading_dt 비교 그림

**커밋:** (미커밋)
**요청:** 새 비교 대상 only_heading_dt(policies에 보존된 dt_heading 계보)와의 그림 작성.
**파일:** `runs/corl2026_scaling/compare_gd_dt_heading/` — record_snapshots_heading.py·evaluate_cot.py·make_multiexposure_heading.py·README.md (신규), data/{trajectories_heading.npz, cot_heading.csv}, figures/gd_dt_heading_multiexposure.png + snapshots 36장
**변경:** 공정 짝은 동일 물리(원 물리)·동일 보상(yaw 10.0)의 gd_delta0_heading(archive_20260810)으로 선정(bsmotor GD는 물리 달라 제외). GD 최고(전부 s42) vs DT 최악(n10 s44 1.3k, n14 s44 405k, n20 s43 12k) 시드, compare_gd_dt와 동일 형식(다중노출 상하 + CoT 로그축 전 관절). 조기 종료 run은 스냅샷 시점을 에피소드 길이에 분배하도록 record 스크립트 개선(낙상 과정 포착). 결과 — DT 최악: n10 1.25 s 낙상, n20 y −6.25 m 대각 이탈, n14는 11.7 m 고속 직진. CoT: GD 45/10.4/6.1/9.3 vs DT 69/11.3/7.3/8.8. 평균 |ω|: GD 2.2~2.5 vs DT 4.8~6.5 — n10/n20에서 무부하 한계(5.97) 초과, README에 캡션 필수 언급으로 기록.

## 2026-08-12 — heading 비교 확장: 섭동 스윕 + 보행 품질 패널

**커밋:** (미커밋)
**요청:** GD vs DT 섭동 스윕(마찰 변경 + 노이즈 추가) 진행, 보행 품질을 그림에 추가.
**파일:** `compare_gd_dt_heading/evaluate_quality.py`·`evaluate_sweep.py` (신규), `data/{quality,sweep}_heading.csv`, `make_multiexposure_heading.py` (우측 열 3단: (d) CoT/(e) 속도 CV/(f) 섭동 유지율), 그림 재생성, README 갱신
**변경:** 품질 24런(주기성·횡편차 RMS·속도 CV·|Δa|·토크 포화율) + 스윕 90런(마찰 ×0.7/×1.3, 액션 노이즈 σ1%/3%, 1500스텝, 유지율=시드별 nominal 대비). 정직 결과 — (e) 속도 CV: GD 0.07~0.20 vs DT 0.13~0.36 (GD 우위, 채택). 주기성은 GD 우위 아님(이산 게이팅의 고조파 확산; 그림 제외, CSV 보존). (f) 섭동: 평균 유지율 양쪽 96~108%로 차별화 없음(이 강도에서 DT 취약 가설 기각), 단 DT 분산이 GD 대비 훨씬 큼(±25~35% 밴드) — 예측 가능성 논거. 토크 포화율 양쪽 ~100%(원 물리)라 비판별적.

## 2026-08-12 — bsmotor 비교에도 품질·섭동 패널 적용 (compare_gd_dt)

**커밋:** (미커밋)
**요청:** heading에 적용한 것과 똑같은 확장(품질 평가 + 섭동 스윕 + (d)(e)(f) 패널)을 gd_dt(bsmotor) 비교에도 적용.
**파일:** `compare_gd_dt/evaluate_quality.py`·`evaluate_sweep.py` (heading에서 이식), `data/{quality,sweep}_gd_dt.csv`, `make_multiexposure_gd_dt.py` (우측 열 3단), `figures/gd_dt_multiexposure.png`, README 갱신
**변경:** 동일 프로토콜(품질 24런 3000스텝, 스윕 90런 1500스텝). 정직 결과 — heading과 **반대 방향**: (e) 속도 CV는 DT가 더 일정(0.018~0.085 vs GD 0.048~0.067; back-EMF가 몸부림 차단), (f) 저마찰 μ×0.7에서 GD 0.84(최저 0.55) vs DT 1.00으로 DT가 강건. GD 잔여 우위는 CoT(n≤14)·직진성(횡편차 RMS)·액션 스무스니스. README에 "이 그림 (e)(f)는 DT 유리 — 리부탈 본문용은 heading 버전, bsmotor는 저널 확장(actuator 충실도 × prior) 논의용" 재확인 기록.

## 2026-08-12 — compare_gd_dt 최종 그림: 좌 다중노출 / 중 n=20 밀집 단독 / 우 CoT

**커밋:** (미커밋)
**요청:** 최종 구성 확정 — 좌 [다중노출 3장], 중 [n=20 GD 상/DT 하 단독 다중노출, 1초 간격 노출로 DT의 이상 보행을 리뷰어가 직접 보게], 우 [CoT]. bsmotor 정책.
**파일:** `compare_gd_dt/record_n20_dense.py`·`make_final_figure.py` (신규), `figures/snapshots_dense/*.png`(22장), `data/dense_n20_framing.npz`, `figures/gd_dt_final.png`, README 갱신
**변경:** n=20 GD(s43 최고)·DT(s44 최악)를 1 s 간격 11장으로 재촬영(두 런 전용 타이트 카메라 half extent 3.33 m — 로봇 형상 확대), 단독 패널 합성(틴트·알파 램프 유지). 최종 그림 6행×3열 그리드(좌 3패널×2행, 중 2패널×3행, 우 1패널×6행). 결과 — (d) GD는 규칙적 serpentine S자 파형이 등간격 전진, (e) DT는 구겨진 비정형 몸 말림이 밀집 노출에 그대로 노출: "수치로 표현 안 되는 이상 보행"의 시각 증거 확보.

## 2026-08-12 — gd_dt_final 다듬기: 제목 정리·로그 그리드·간격 축소·축 정렬

**커밋:** (미커밋)
**요청:** (d)(e) 제목의 best/worst seed 문구 삭제, (f)에 major+minor 그리드, 패널 간 공간 축소, 축 정렬.
**파일:** `make_final_figure.py` (수동 레이아웃으로 재작성), `figures/gd_dt_final.png`
**변경:** gridspec 대신 인치 단위 수동 배치 — 각 이미지의 데이터 종횡비에서 패널 폭을 유도(좌 h/w 0.41, 중 0.30)해 세 열의 상단 제목선·하단 x축이 정확히 일치, 열 간격 0.6~0.7 in로 축소(그림 15.4×5.0 in). (d)(e) 제목 "GD-RL/DT, 20 joints — exposure every 1 s"로 단순화(시드 정보는 좌측 범례·README가 유지). (f) LogLocator minor(2~9) + 이중 그리드. 중간 패널이 커져 DT의 구겨진 비정형 보행 vs GD의 규칙 파형 대비가 더 선명해짐.

## 2026-08-12 — dt_bsmsym 12런 완료: U자 우회 완전 차단, 전 시드 뱀형 정면 보행

**커밋:** (미커밋)
**요청:** (승인된 캠페인 완주 보고) 링크 정렬 항(가중치 30) 적용 DT 재학습 판정.
**파일:** `runs/corl2026_scaling/dt_bsmsym_n*/` (12런), `analysis_bsmsym/rollout_check.csv`
**변경:** **12/12 시드 전부 정면 정렬 보행 성공** — 이동각 ≤7°, 몸통 yaw ≤2°, 3000스텝 완주, 속도 0.17~0.62 m/s(n과 함께 증가), |ω| 2.9~3.5(엔벨로프 내). **링크 정렬 비용 실측 0.014~0.129 = 정상 파동 수준(U자 기준 1.06의 1~12%)** — U자 우회 완전 소멸, 뱀다운 신장 자세 유지. 특기: DT n=6도 3/3 보행 성공(전 캠페인 최초 — GD bsmotor n=6은 실패했던 구간). 사용자의 "링크별 오리엔테이션 반영" 설계가 chordal 평균의 상쇄 허점을 정확히 봉인함을 실증. 보존 GD(bsmotor) 대비: DT가 속도 우위(예: n=20 0.62 vs 0.59, n=14 0.39 vs 0.32) + n=6 커버, GD는 관절 속도 보수성(1.1~1.9 vs 2.9~3.5) 유지. 표본 효율 곡선 비교는 보상 정의가 달라(DT에 링크 항 추가) 직접 비교에 주의 필요 — 요청 시 별도 분석.

---

## 2026-08-31 — delta=23 전진 계보를 old/로 격리

**커밋:** (미커밋)
**요청:** 잘못된 gait(delta=23)로 학습된 기존 전진 정책을 정책 폴더에서 "old" 표기 폴더로 옮겨 착오를 방지해달라는 요청.
**파일:** `policies/path_tracking/old/forward_delta23/` (forward/에서 전체 이동), `policies/path_tracking/forward/TRAINING_HISTORY.txt` (안내 스텁 신규), `training/configs/ppo_plane_{finetune,finetune_continue,curriculum_x_long,curriculum_x_finetune,curriculum_left_finetune,dt_forward_stage1~5}.yaml`, `scripts/run_dt_forward_pipeline.sh`
**변경:** forward 계보(01~05, gait_params 미지정으로 환경 기본값 delta=23 적용 학습분)를 `old/forward_delta23/`로 이동하고 원장 맨 위에 폐기 사유 헤더 추가. 비워진 forward/에는 상태 안내 스텁 원장 생성(올바른 전진 gait=[30,30,40,40,0], delta=0 재학습 미수행, dt_forward 파이프라인은 별개임을 명시). 해당 경로를 참조하던 resume YAML 5종과 주석 참조(dt_forward stage1~5, 파이프라인 스크립트)를 새 경로로 일괄 갱신 — 잔여 참조 0건 확인. 이동 후 대표 모델 파일 존재 확인.

---

## 2026-08-31 — delta=0 전진 Stage 1 학습 시작

**커밋:** (미커밋)
**요청:** 올바른 전진 gait(delta=0)로 전진 정책을 재학습하되 보상 계수를 다른 계보와 동일하게 설정하고, 총 80M 스텝 규모(3-stage)로 진행. 다음 캠페인은 전진-좌 45도 대각(delta=23)임을 기억해달라는 지시 포함.
**파일:** `training/configs/ppo_plane_forward_delta0_from_scratch_long.yaml` (신규), `policies/path_tracking/forward/TRAINING_HISTORY.txt`
**변경:** gait_params=[30,30,40,40,0], joy_input=[1,0,0], 보상 계수는 좌/우/후진과 완전 동일(rotation_norm_cost_weight=10.0 포함 — 사전 비교에서 유일한 실질 차이였음), 검증된 Stage 1 레시피(lr 1e-4/n_epochs 2/target_kl 0.04, 28.4M 스텝)로 from-scratch YAML 작성. delta=0 kwargs로 200스텝 headless 구동 검증 후 launch_training.sh(태그 stage1, 뷰어 창)로 시작 — run 20260831-215034-678652, 단독 실행이라 stage당 약 4.5~5시간, 3-stage 총 ~15시간 예상. 전진 원장에 진행 기록 추가. 대각 계획은 메모리(direction-policy-campaign)에 저장.

---

## 2026-09-01 — 전진 delta=0 Stage 1 완주, Stage 2 시작 (n_epochs 2→3)

**커밋:** (미커밋)
**요청:** (delta=0 전진 3-stage 캠페인의 자동 진행) stage 경계에서 결과 분석 후 optimizer만 튜닝해 다음 stage 시작.
**파일:** `training/configs/ppo_plane_forward_delta0_continue_stage2.yaml` (신규), `policies/path_tracking/forward/TRAINING_HISTORY.txt`
**변경:** Stage 1 완주 — 최고 평가 리턴 173,777 @ 27.9M(좌측 Stage 1과 동급), x_velocity +0.488, y_velocity 0.017, dir_sim 0.782, yaw 7.4도로 delta=0 전진 gait 정상 확인. 말기 approx_kl 0.0123(target의 1/3)·clip 0.101·조기중단 14회로 여유 확인 → 좌/우 검증 레시피대로 n_epochs 2→3(lr/target_kl 유지)의 Stage 2 YAML 작성, Stage 1 final에서 resume(누적 28,413,952 재개, 오버라이드 적용 확인), launch_training.sh 태그 stage2로 시작.

---

## 2026-09-01 — 전진 delta=0 Stage 2 완주(+28%), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (delta=0 전진 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_forward_delta0_continue_stage3.yaml` (신규), `policies/path_tracking/forward/TRAINING_HISTORY.txt`
**변경:** Stage 2 완주 — 최고/마지막 평가 리턴 222,727 @ 56.7M(Stage 1 대비 +28%, 구 delta=23 계보 최고 208,913 추월, 말미까지 상승 중), x_velocity +0.593, dir_sim 0.827, yaw 5.7도. 말기 approx_kl 0.038~0.055 포화·clip 0.402·조기중단 233회 → 좌/우 Stage 3 검증 처방(lr 1e-4→5e-5, n_epochs 3→2)의 Stage 3 YAML 작성, Stage 2 final에서 resume(누적 56,827,904 재개, 오버라이드 적용 확인) 후 태그 stage3로 시작.

---

## 2026-09-01 — 전진 delta=0 Stage 3 완주, 캠페인 종료

**커밋:** (미커밋)
**요청:** (delta=0 전진 3-stage 캠페인의 완결)
**파일:** `policies/path_tracking/forward/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** Stage 3(lr 5e-5/n_epochs 2) 완주 — 최고 232,266 @ 81.3M(+4.3%), x_velocity +0.606, dir_sim 0.832, yaw 5.1도, 조기중단 233→3회로 보수화 처방 유효 확인. 계보 요약(173,777→222,727→232,266, 총 13.5h)을 원장에 기록, 메모리의 캠페인 상태를 완료로 갱신. 정책 폴더 번호 디렉터리 정리는 사용자 승인 대기, 다음 캠페인(전진-좌 45도 대각, delta=23) 착수 가능 상태.

---

## 2026-09-01 — 전진 delta=0 계보를 policies/path_tracking/forward로 정리

**커밋:** (미커밋)
**요청:** 대각 캠페인에 앞서 정책 폴더를 먼저 정리해달라는 요청.
**파일:** `policies/path_tracking/forward/{01_forward_delta0_from_scratch_long,02_forward_delta0_continue_stage2,03_forward_delta0_continue_stage3}/` (runs/에서 이동), `policies/path_tracking/forward/TRAINING_HISTORY.txt`, `training/configs/ppo_plane_forward_delta0_continue_stage{2,3}.yaml`
**변경:** 기존 규약대로 timestamped run 전체를 번호 디렉터리로 이동(각 stage 콘솔 로그/pid 포함), 빈 runs/ 디렉터리 제거. 원장 경로와 stage 2/3 YAML resume 경로를 policies/ 위치로 갱신(YAML의 output_dir는 재실행용 정의라 유지). 무결성 검증: 새 위치 best_model 1-episode 평가 리턴 229,699/6,000스텝으로 학습 시 평가(228,388~232,266)와 일치, vecnormalize 자동 매칭 확인.

---

## 2026-09-01 — 전진-좌 45도 대각 캠페인 Stage 1 시작

**커밋:** (미커밋)
**요청:** 기억해 둔 계획대로 대각(전진-좌 45도) 학습을 시작해달라는 요청.
**파일:** `training/configs/ppo_plane_diag_fl_from_scratch_long.yaml` (신규), `policies/path_tracking/diag_forward_left/TRAINING_HISTORY.txt` (신규)
**변경:** delta=23(plane_v3.py 방향 테이블의 ↗ 항목 — 구 전진 계보가 착오로 쓰던 gait를 본래 용도로 사용), joy_input=[0.7071,0.7071,0](45도 단위 벡터), 보상 계수는 5개 계보 공통, 검증된 Stage 1 레시피(lr 1e-4/n_epochs 2/target_kl 0.04, 28.4M)로 from-scratch YAML 작성. 200스텝 headless 검증 후 launch_training.sh(태그 stage1, 뷰어 창)로 시작 — run 20260901-134112-909353. 대각 원장 신규 생성(검증 지표: x·y 속도 동반 상승 및 ~1:1 비율, yaw 억제). 3-stage 자동 진행 예정.

---

## 2026-09-01 — 대각(FL) Stage 1 완주(전 계보 Stage 1 최고), Stage 2 시작

**커밋:** (미커밋)
**요청:** (대각 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_fl_continue_stage2.yaml` (신규), `policies/path_tracking/diag_forward_left/TRAINING_HISTORY.txt`
**변경:** Stage 1 완주 — 최고 184,934 @ 28.2M로 전 계보 Stage 1 최고 기록, x/y 속도 0.370/0.328(heading 41.6도 ≈ 목표 45도), dir_sim 0.803, yaw 5.4도. 초기 탐색 저점 없이 4.8M에 양전환한 점이 특이(대각 gait와 명령 정렬). 말기 KL 0.0196(target의 1/2)·조기중단 3회 → n_epochs 2→3의 Stage 2 YAML 작성, Stage 1 final에서 resume(누적 28,413,952, 오버라이드 확인) 후 태그 stage2로 시작.

---

## 2026-09-01 — 대각(FL) Stage 2 완주(+10.4%), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (대각 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_fl_continue_stage3.yaml` (신규), `policies/path_tracking/diag_forward_left/TRAINING_HISTORY.txt`
**변경:** Stage 2 완주 — 최고 204,106 @ 56.4M(+10.4%), heading 42.7도, dir_sim 0.820. 말기 KL 0.049~0.060 포화·clip 0.395·조기중단 2,166회(역대 최다) → 검증 보수화 처방(lr 1e-4→5e-5, n_epochs 3→2)의 Stage 3 YAML 작성, Stage 2 final에서 resume(누적 56,827,904, 오버라이드 확인) 후 태그 stage3로 시작. 목표 누적 85.2M.

---

## 2026-09-02 — 대각(FL) Stage 3 완주, 캠페인 종료

**커밋:** (미커밋)
**요청:** (대각 3-stage 캠페인의 완결)
**파일:** `policies/path_tracking/diag_forward_left/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** Stage 3(lr 5e-5/n_epochs 2) 완주 — 최고 211,721 @ 82.6M(+3.7%), heading 41.9도, yaw 5.3도, 조기중단 2,166→80회로 보수화 처방 5개 계보째 재현 확인. 말미 리턴 209K~210K 수렴으로 대각 단독 개선은 마무리 권장으로 기록. 계보 요약(184,934→204,106→211,721, 13.5h)과 5방향 최고 리턴 현황을 원장·메모리에 갱신. 정책 폴더 정리는 사용자 승인 대기.

---

## 2026-09-02 — 대각(FL) 계보를 policies/path_tracking/diag_forward_left로 정리

**커밋:** (미커밋)
**요청:** 학습된 대각 정책을 정리해달라는 요청.
**파일:** `policies/path_tracking/diag_forward_left/{01_diag_fl_from_scratch_long,02_diag_fl_continue_stage2,03_diag_fl_continue_stage3}/` (runs/에서 이동), `policies/path_tracking/diag_forward_left/TRAINING_HISTORY.txt`, `training/configs/ppo_plane_diag_fl_continue_stage{2,3}.yaml`
**변경:** 기존 규약대로 timestamped run 전체를 번호 디렉터리로 이동(각 stage 콘솔 로그/pid 포함), 빈 runs/ 디렉터리 제거. 원장 경로와 stage 2/3 YAML resume 경로를 policies/ 위치로 갱신. 무결성 검증: 새 위치 best_model 1-episode 평가 리턴 210,355/6,000스텝으로 학습 시 평가(209,107~211,721)와 일치, vecnormalize 자동 매칭 확인.

---

## 2026-09-02 — 작업 착수 전 계획 리스트업 루틴 추가

**커밋:** (미커밋)
**요청:** 작업 수행 전에 어떤 방법으로 수행할지 리스트업해서 먼저 알려주는 루틴을 추가해달라는 요청.
**파일:** `CLAUDE.md`, 메모리(feedback: plan-checklist-routine)
**변경:** 기존 "작업 착수 전 계획 제시" 규칙을 명시적 체크리스트 루틴으로 격상 — ① 목표 ② 수행 단계 번호 목록 ③ 방법 근거·대안 ④ 예상 산출물/영향(장기 작업은 소요 시간)을 제시하고 승인 후 착수. 예외 2건 명시: 상태 불변경 조회 작업, 사전 승인된 자동 진행 루프의 내부 단계(단, 단계 보고에 다음 단계 계획 포함). 세션 간 유지를 위해 영구 메모리에도 feedback 항목으로 저장.

---

## 2026-09-02 — 전진-우 45도 대각 캠페인 Stage 1 시작 (delta=203)

**커밋:** (미커밋)
**요청:** 우측 대각 전진 학습 요청. 신규 계획 리스트업 루틴에 따라 계획 제시 후 승인받고 착수.
**파일:** `training/configs/ppo_plane_diag_fr_from_scratch_long.yaml` (신규), `policies/path_tracking/diag_forward_right/TRAINING_HISTORY.txt` (신규)
**변경:** 거울상 원리로 delta=203(=23+180) 도출 및 수치 검증 — 전진-좌 대각(delta=23) 대비 dorsal 100% 일치/lateral 100% 부호 반전. 주석 테이블의 ↘=-23은 거울상 아님(lateral 25.6%)을 확인해 기각. joy_input=[0.7071,-0.7071,0], 보상 계수 공통, 검증 Stage 1 레시피로 YAML 작성, 200스텝 검증 후 태그 stage1으로 시작 — run 20260902-102706-813605. 3-stage 자동 진행 예정.

---

## 2026-09-02 — 대각(FR) Stage 1 완주, Stage 2 시작 (n_epochs 2→3)

**커밋:** (미커밋)
**요청:** (대각 FR 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_fr_continue_stage2.yaml` (신규), `policies/path_tracking/diag_forward_right/TRAINING_HISTORY.txt`
**변경:** Stage 1 완주 — 최고 150,257 @ 28.4M, heading -44.0도(목표 -45도), dir_sim 0.802. FL 대비 -19%는 방향 정렬이 아닌 합속도 크기 차이로, 좌우 물리 비대칭 패턴(좌 273.7K vs 우 244.0K)과 일치. 말기 KL 0.0219·조기중단 4회로 여유 → n_epochs 2→3의 Stage 2 YAML 작성, Stage 1 final에서 resume(누적 28,413,952, 오버라이드 확인) 후 시작.

---

## 2026-09-02 — 대각(FR) Stage 2 완주(+14.5%), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (대각 FR 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_fr_continue_stage3.yaml` (신규), `policies/path_tracking/diag_forward_right/TRAINING_HISTORY.txt`
**변경:** Stage 2 완주 — 최고 171,998 @ 56.7M(+14.5%), heading -46.0도, dir_sim 0.830, yaw 4.4도. 말기 KL 0.060 포화·조기중단 3,349회 → 검증 보수화(lr 1e-4→5e-5, n_epochs 3→2)의 Stage 3 YAML 작성, Stage 2 final에서 resume(누적 56,827,904, 오버라이드 확인) 후 시작. 목표 누적 85.2M.

---

## 2026-09-02 — 대각(FR) Stage 3 완주, 캠페인 종료

**커밋:** (미커밋)
**요청:** (대각 FR 3-stage 캠페인의 완결)
**파일:** `policies/path_tracking/diag_forward_right/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** Stage 3(lr 5e-5/n_epochs 2) 완주 — 최고 181,215 @ 82.3M(+5.4%), heading -46.6도, yaw 3.8도, 조기중단 3,349→101회로 보수화 처방 7번째 재현. 계보 요약(150,257→171,998→181,215, 13.2h)과 6방향 현황을 원장·메모리에 기록. FL 대비 -14%는 전 계보 일관된 좌우 물리 비대칭 범위로 판단. 정책 폴더 정리는 사용자 승인 대기.

---

## 2026-09-03 — 대각(FR) 계보를 policies/path_tracking/diag_forward_right로 정리

**커밋:** (미커밋)
**요청:** 정책 폴더 정리 요청 (동일 절차 4번째 반복).
**파일:** `policies/path_tracking/diag_forward_right/{01_diag_fr_from_scratch_long,02_diag_fr_continue_stage2,03_diag_fr_continue_stage3}/` (runs/에서 이동), `policies/path_tracking/diag_forward_right/TRAINING_HISTORY.txt`, `training/configs/ppo_plane_diag_fr_continue_stage{2,3}.yaml`
**변경:** 규약대로 run 전체 이동(콘솔 로그/pid 포함), 빈 runs/ 제거, 원장·YAML resume 경로 갱신. 무결성 검증: 새 위치 best_model 1-episode 평가 리턴 177,772/6,000스텝 — 학습 시 평가(180,179~181,215)와 부합(단일 episode 편차 범위), vecnormalize 자동 매칭 확인.

---

## 2026-09-03 — 후진-좌 45도 대각 캠페인 Stage 1 시작 (gait [30,30,40,40,203,-1])

**커밋:** (미커밋)
**요청:** 후진-좌 대각 gait 후보 리스트업 후, 1순위 파라미터로 학습 진행 승인.
**파일:** `training/configs/ppo_plane_diag_bl_from_scratch_long.yaml` (신규), `policies/path_tracking/diag_backward_left/TRAINING_HISTORY.txt` (신규)
**변경:** 세 독립 유도(FR대각 δ=203의 시간 역재생 = 변위 반전, 후진-우 후보 (23,-1)의 y-거울상, 검증된 후진 레시피 "반대 방향 전진 gait의 역재생" 패턴)가 수렴한 (203,-1) 채택. 개루프 실측으로 중립 prior 시그니처 확인, 주석 테이블 ↖=(-23,-1)은 부호반전 계열 2전 2패 + 개루프 +4.4m 전진 표류로 기각. joy_input=[-0.7071,0.7071,0], 보상 계수 공통, Stage 1 레시피로 YAML 작성, 200스텝 검증 후 태그 stage1으로 시작 — run 20260903-123502-155422. 3-stage 자동 진행 예정.

---

## 2026-09-03 — 대각(BL) Stage 1 완주(방향 성립 확인), Stage 2 시작

**커밋:** (미커밋)
**요청:** (후진-좌 대각 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_bl_continue_stage2.yaml` (신규), `policies/path_tracking/diag_backward_left/TRAINING_HISTORY.txt`
**변경:** Stage 1 완주 — 최고 131,291 @ 28.3M, heading 132.8도(목표 135도), dir_sim 0.755. 역재생 prior의 깊은 초기 저점(-385K) 후 단조 상승, (203,-1) 도출 원리가 실학습으로 검증됨. 말기 KL 0.0173 여유 → n_epochs 2→3의 Stage 2 YAML 작성, Stage 1 final에서 resume(누적 28,413,952, 오버라이드 확인) 후 시작.

---

## 2026-09-03 — 대각(BL) Stage 2 완주(+32.5%), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (후진-좌 대각 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_bl_continue_stage3.yaml` (신규), `policies/path_tracking/diag_backward_left/TRAINING_HISTORY.txt`
**변경:** Stage 2 완주 — 최고 173,962 @ 53.4M(+32.5%, 대각 계열 최대 Stage 2 상승폭), heading 132.9도, yaw 4.8도, EV 0.931. 말기 KL 0.069 포화·조기중단 3,294회 → 검증 보수화(lr 1e-4→5e-5, n_epochs 3→2)의 Stage 3 YAML 작성, Stage 2 final에서 resume(누적 56,827,904, 오버라이드 확인) 후 시작. 목표 누적 85.2M.

---

## 2026-09-04 — 대각(BL) Stage 3 완주, 캠페인 종료

**커밋:** (미커밋)
**요청:** (후진-좌 대각 3-stage 캠페인의 완결)
**파일:** `policies/path_tracking/diag_backward_left/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** Stage 3(lr 5e-5/n_epochs 2) 완주 — 최고 187,883 @ 82.8M(+8.0%), heading 133.4도, yaw 4.2도, EV 0.951, 조기중단 3,294→1,042회. FR(181,215) 추월로 좌측 우위 패턴 일관 확인. 계보 요약(131,291→173,962→187,883, 13.3h)과 7방향 현황을 원장·메모리에 기록. 남은 방향은 후진-우 대각 1개(후보 (23,-1) 도출 완료). 정책 폴더 정리는 사용자 승인 대기.

---

## 2026-09-04 — BL 계보 정리 및 후진-우 대각(마지막 방향) Stage 1 시작

**커밋:** (미커밋)
**요청:** 정책 폴더 정리 후 후진-우 대각 학습 시작 요청.
**파일:** `policies/path_tracking/diag_backward_left/{01,02,03}_diag_bl_*/` (runs/에서 이동), `policies/path_tracking/diag_backward_left/TRAINING_HISTORY.txt`, `training/configs/ppo_plane_diag_bl_continue_stage{2,3}.yaml` (resume 경로 갱신), `training/configs/ppo_plane_diag_br_from_scratch_long.yaml` (신규), `policies/path_tracking/diag_backward_right/TRAINING_HISTORY.txt` (신규)
**변경:** ① BL 계보를 규약대로 번호 디렉터리로 이동(콘솔 로그/pid 포함, 빈 runs/ 제거), 원장·YAML 경로 갱신, 무결성 검증 통과(1-episode 리턴 188,030 — 학습 시 평가와 일치). ② 후진-우 대각(8방위 마지막): gait [30,30,40,40,23,-1] (FL 역재생 = BL의 y-거울상 = 주석 테이블 ↙과 일치, 세 근거 수렴), joy=[-0.7071,-0.7071,0], 공통 보상·Stage 1 레시피로 YAML 작성, 200스텝 검증 후 태그 stage1으로 시작 — run 20260904-102334-622556. 3-stage 자동 진행 예정.

---

## 2026-09-04 — 대각(BR) Stage 1 완주, Stage 2 시작 (n_epochs 2→3)

**커밋:** (미커밋)
**요청:** (후진-우 대각 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_br_continue_stage2.yaml` (신규), `policies/path_tracking/diag_backward_right/TRAINING_HISTORY.txt`
**변경:** Stage 1 완주 — 최고 150,747 @ 27.5M(BL Stage 1 131K보다 높은 출발), heading -133.5도(목표 -135도), dir_sim 0.783. 역재생 prior 특유의 깊은 저점(-575K)과 중반 재하락 후 강한 회복. 말기 KL 0.021 여유 → n_epochs 2→3의 Stage 2 YAML 작성, Stage 1 final에서 resume(누적 28,413,952, 오버라이드 확인) 후 시작.

---

## 2026-09-04 — 대각(BR) Stage 2 완주(+12.4%), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (후진-우 대각 3-stage 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_diag_br_continue_stage3.yaml` (신규), `policies/path_tracking/diag_backward_right/TRAINING_HISTORY.txt`
**변경:** Stage 2 완주 — 최고 169,491 @ 55.7M(+12.4%), heading -133.5도, dir_sim 0.800. 말기 KL 0.054 포화·조기중단 3,350회 → 검증 보수화(lr 1e-4→5e-5, n_epochs 3→2)의 Stage 3 YAML 작성, Stage 2 final에서 resume(누적 56,827,904, 오버라이드 확인) 후 시작. 8방위 로스터의 마지막 stage, 목표 누적 85.2M.

---

## 2026-09-04 — 대각(BR) Stage 3 완주, 8방위 방향 정책 로스터 완성

**커밋:** (미커밋)
**요청:** (후진-우 대각 3-stage 캠페인의 완결 = 8방위 로스터의 마지막 학습)
**파일:** `policies/path_tracking/diag_backward_right/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** Stage 3(lr 5e-5/n_epochs 2) 완주 — 최고 178,719 @ 84.6M(+5.4%), heading -133.9도, yaw 4.1도, 조기중단 3,350→759회. BL 대비 -4.9%로 좌측 우위 4쌍 일관 확인. 계보 요약(150,747→169,491→178,719, 13.4h)과 **8방위 로스터 완성표**(방향별 joy/gait/최고 리턴 및 gait 도출 규칙성)를 원장·메모리에 기록. 정책 폴더 정리는 사용자 승인 대기.

---

## 2026-09-05 — 대각(BR) 계보 정리, 8방위 로스터 전체 보존 완료

**커밋:** (미커밋)
**요청:** 학습된 정책(BR) 정리 요청 (동일 절차 5번째 반복).
**파일:** `policies/path_tracking/diag_backward_right/{01,02,03}_diag_br_*/` (runs/에서 이동), `policies/path_tracking/diag_backward_right/TRAINING_HISTORY.txt`, `training/configs/ppo_plane_diag_br_continue_stage{2,3}.yaml`
**변경:** 규약대로 run 전체 이동(콘솔 로그/pid 포함), 빈 runs/ 제거, 원장·YAML resume 경로 갱신. 무결성 검증: 새 위치 best_model 1-episode 리턴 177,323/6,000스텝 — 학습 시 평가(176,989~178,719)와 일치, vecnormalize 자동 매칭 확인. 이로써 8방위 전 계보(24 run)가 policies/path_tracking/에 동일 규약으로 보존 완료.

---

## 2026-09-05 — 회전 gait 도출 + 제자리 회전 환경(plane-rotation-v0) 신규 생성

**커밋:** (미커밋)
**요청:** 제자리 CW/CCW 회전 정책 준비의 1~2단계 — 회전용 gait 추천 리스트 도출과 신규 환경 생성(학습은 미시작).
**파일:** `horcrux_env/envs/plane_rotation_v1.py` (신규), `horcrux_env/envs/__init__.py`, `horcrux_env/__init__.py` (plane-rotation-v0 등록)
**변경:**
① gait 개루프 스캔(48조합×2000스텝 + 정밀 검증): 1:2 주파수 패밀리 (30,30,20,40,0/180)은 ±6,400도/4,000스텝의 압도적 회전이지만 텀블링 결합(|roll|>45도가 83~94%, 종료조건下 생존 32~87스텝, dorsal=0이면 roll 0%지만 yaw 소멸 — 구르기가 곧 회전 메커니즘). 건강한 1:1 패밀리에서 lateral 테이퍼(머리 2.2→꼬리 0.4, dorsal 0.5) 진폭 패턴으로 **(30,30,40,40,135)=CW -1,933도, (30,30,40,40,315)=CCW +1,901도**/3,000스텝, 표류 ~1.3m, roll 위반 ~1%의 건강 회전 모드 발견 — δ 거울쌍(135+180=315)이고 진폭 패턴이 RL 행동 공간 내부라 학습 도달성 증명.
② PlaneJoyDirWorld 상속 PlaneRotationWorld: 보상 = 회전정렬(45·sign(joy_r)·yaw_vel) + 회전효율 + healthy − **앵커 거리 비용(50·‖com−initial_com‖, 신규 핵심)** − 병진속도 비용(기본 0) − ctrl/unhealthy. orientation_cost(|yaw|)와 proj_dist(0-나눗셈 NaN, joy=[0,0,±1]에서 기존 plane-v0 보상이 실제 NaN이 됨을 실측 확인) 제거. 가중치는 생성자 인수로 노출(설계 원칙 3-4), 부모 info 키 유지 + cost_anchor/anchor_distance/aligned_yaw_vel 추가.
검증: 랜덤 행동 300스텝×2방향 비유한 보상 0건, ltaper 구동 4조합(gait 방향×명령 부호)에서 회전 보상 부호 전부 정합.

---

## 2026-09-05 — dorsal/lateral 시간 주파수 비 파라미터 스터디 (밤샘 자동 실행)

**커밋:** (미커밋)
**요청:** e_d2(dorsal temporal) > e_l2(lateral)가 지면 굴곡 극복에 유리하다는 가설의 심층 파라미터 스터디를 야간 자율 실행으로 요청.
**파일:** `training/configs/ppo_plane_tempstudy_{d80l40,d100l40,d60l30,d40l40ctrl}.yaml` (신규), `runs/ppo_plane_tempstudy/chain_driver.sh` (신규)
**변경:** ① 개루프 스캔(21비율×δ12, 평지 1500스텝 → 비율별 최적 δ를 obstacle XML에서 2500스텝 재측정): 건강 굴곡 1위 (100,40,60) 비율2.5 obst dX+4.15/roll 11.9%, 건강 평지 최강 (80,40,180) 비율2.0 dX+14.4/roll 4.5%. 부수 발견 — d2≥80 고비율에서 roll 위반 2~18%로 급감(빠른 dorsal 파의 roll 안정화). 기준선 (40,40)은 굴곡 +5.4지만 roll 89.5%(텀블링). ② 상위 3개 비율+대조군의 10M 스텝 동일예산 학습 4런을 setsid 분리 순차 체인으로 시작(PID 144723, d80l40→d100l40→d60l30→d40l40ctrl, 각 ~1.8h, 뷰어 창 오픈). 보상/PPO는 전진 Stage 1과 동일, gait만 변수. 완료 시 굴곡 zero-shot 평가 포함 종합 보고 예정.

---

## 2026-09-05 — temporal-ratio 스터디 완료: 개루프/10M RL/굴곡 zero-shot 결과

**커밋:** (미커밋)
**요청:** (밤샘 파라미터 스터디의 완결 보고)
**파일:** `runs/ppo_plane_tempstudy/scan_results.txt` (스캔 결과 보존), 스터디 run 4개
**변경/결과:** 체인 4런 전부 정상 완주(01:34~09:16, 각 ~1.8~2.1h). ① 10M 동일예산 평지 RL: 대조군(40,40) 64.6K·ep_len 6000으로 최고, d80l40은 피크 58.2K(대조군의 90%)이나 말기 건강 불안정(ep_len 904), d100l40/d60l30은 미성숙(-18/-1,072) — 비율 계열은 KL~3e-5·std~0.98로 아직 탐색 저점 구간, 확정 비교에는 풀 28.4M 필요. ② 굴곡 zero-shot(4정책 best 각 2ep): 전 정책 생존 21~984스텝으로 조기 종료 — 10M 미성숙 정책의 미지 지형 전이는 판정 불가, 지형 포함 학습이 필요하다는 결론. ③ 종합: 가설(d2>l2 유리)은 개루프에서 강하게 지지(건강 굴곡 통과는 전부 d2>l2 영역, d2>=80에서 roll 안정화), RL에서는 d80l40이 유망하나 10M 예산 내 검증 한계. 후속 후보로 d80l40 vs 대조군 풀 캠페인 또는 obstacle 지형 학습을 기록.

---

## 2026-09-05 — 제자리 회전 CCW 캠페인 Stage 1 시작 + 회전 지표 로깅 추가

**커밋:** (미커밋)
**요청:** 확정 파라미터(δ=315, joy=[0,0,+1], anchor 50)로 CCW 회전 학습 우선 진행 승인.
**파일:** `training/configs/ppo_plane_rot_ccw_from_scratch_long.yaml` (신규), `training/callbacks/info_metrics.py`, `policies/rotation/ccw/TRAINING_HISTORY.txt` (신규)
**변경:** info_metrics의 SCALAR_METRICS에 회전 전용 키 4종(anchor_distance, aligned_yaw_vel, cost_anchor, cost_trans_vel) 추가 — 타 환경은 키 부재 시 자동 생략이라 무해. plane-rotation-v0 + 검증 Stage 1 레시피의 CCW YAML 작성, 200스텝 검증 후 태그 stage1으로 시작(run 20260905-114411, PID 158581, 뷰어 창). 감시 2중: 3M 도달 시 앵커 질식 점검 알림 + 종료 감시. 회전 정책 원장은 새 태스크 계열이므로 policies/rotation/ccw/에 생성(path_tracking과 분리).

---

## 2026-09-05 — 앵커 비용 포화형으로 수정, CCW Stage 1 재시작

**커밋:** (미커밋)
**요청:** (CCW 캠페인의 사전 공지된 앵커 캘리브레이션 점검에 따른 조치)
**파일:** `horcrux_env/envs/plane_rotation_v1.py`, `training/configs/ppo_plane_rot_ccw_from_scratch_long.yaml`, `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** 1차 학습(무한 선형 앵커 비용) 3M 진단 — 정책이 앵커에서 10m 표류하며 앵커 비용 -500/step이 보상을 지배, critic EV -0.007/KL 8e-7/value_loss 3e7로 학습 정지(AGENTS.md의 '실행되나 학습 안 됨' 시그니처). 원인은 무계 비용의 스케일 지배로 진단하고 SIGINT/TERM으로 중단(3.2M 시점, 로그는 console_stage1_aborted_unbounded_anchor.log로 보존). 앵커 비용을 포화형 w·min(max(dist−dead_zone,0), cap)으로 변경(dead_zone 0.15m, cap 2.0m → 최대 -100/step 유계, 8방위 계보 보상 스케일과 정합). 생성자 kwargs로 노출, 800스텝 검증(cap 동작 + NaN 0건) 후 재시작 — run 20260905-122402, PID 164086. 3M 재점검 + 종료 감시 재무장.

---

## 2026-09-05 — CCW Stage 1 완주(best 247K @ 6.3M), Stage 2는 best 재개 + 보수화

**커밋:** (미커밋)
**요청:** (CCW 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_rot_ccw_continue_stage2.yaml` (신규), `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** Stage 1 완주 — 최고 246,967 @ 6.3M(ep_len 4,403, 장수-회전 레짐) 후 근시안 기울기로 과속-전도 레짐(1.44 rad/s, 짧은 에피소드)으로 이탈, 말미 42.8K. 원인 분석: γ=0.95 유효지평(~20스텝)에 ~900스텝 뒤 종료가 비가시 + 종료 페널티(2) 미미 → 회전속도 증가 기울기가 지배. Stage 2는 계보 관례(final 재개)에서 이탈해 evaluation/best(6.3M)에서 재개(근거 문서화) + 보수화 lr 5e-5/ep 2로 좋은 basin 정련. resume 확인(Starting timestep 6,300,000, 오버라이드 적용). 누적 12M 도달 시 basin 유지 점검 + 종료 감시 무장. γ 인상/종료 페널티 재설계는 보상 의미론 변경이라 사용자 논의 사항으로 원장에 기록.

---

## 2026-09-05 — CCW Stage 2 중단: 보수화로도 basin 불안정, 보상 재설계 필요 판정

**커밋:** (미커밋)
**요청:** (CCW 캠페인 자동 진행 중 12M basin 점검 결과에 따른 조치)
**파일:** `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** best(6.3M) 재개 + lr 5e-5 보수화에도 첫 평가부터 재붕괴(37K/641 → 4~9K/len~100 진동, 회복 없음) 확인, 누적 ~12.5M에서 SIGINT 중단. 진단 확정: γ=0.95 유효지평 내에서 회전 보상(+65/step)의 '더 빨리' 기울기가 원거리 종료 비용을 구조적으로 지배 — 장수-회전 레짐이 불안정 평형. optimizer로 해결 불가, 보상 재설계 3안(회전 보상 rate-cap 포화 / unhealthy_cost 대폭 인상 / γ 0.99 재학습)을 사용자 결정 사항으로 원장 기록. 현 최선 정책은 Stage 1 evaluation/best(246,967 @ 6.3M) 보존.

---

## 2026-09-05 — 회전 환경 v2 '안정 우선' 재설계 및 CCW 재학습 시작

**커밋:** (미커밋)
**요청:** 사용자 승인 — A+B 병행에 더해 "속도보다 속도의 안정이 중요한 팩터"로 만들고, 앵커 20cm 이탈을 불건강 조건(기존과 같은 지속 시간 기준의 실패)으로 설정.
**파일:** `horcrux_env/envs/plane_rotation_v1.py`, `training/callbacks/info_metrics.py`, `training/configs/ppo_plane_rot_ccw_v2_from_scratch_long.yaml` (신규), `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** ① 회전 보상을 목표 속도(rotation_target_rate 0.5) 포화형 clip으로 변경 + 과속 페널티(target+0.15 초과분 × 45) 신설 — '더 빨리'의 유인 제거. ② 앵커 반경(anchor_healthy_radius 0.2m) 이탈을 roll 이탈과 동일한 연속 불건강 카운터에 편입(30스텝 지속 시 terminated), is_healthy에도 반영. ③ unhealthy_cost 1000 + γ 0.99 (YAML). ④ 구현 중 부모 is_terminated의 스텝당 2회 호출로 인한 카운터 이중 증가·종료 페널티 보상 누락 결함 발견, 스텝 멱등 캐시로 수정(T1 재검증: 종료 보상 -1006). 검증 3종(앵커 종료/포화·과속 의미론/NaN) 통과 후 v2 from-scratch 시작 — run 20260905-195059, PID 180122. cost_overspeed 로깅 키 추가. 3M 점검 + 종료 감시 무장.

---

## 2026-09-05 — CCW v2 Stage 1 완주(설계 검증 성공), Stage 2 시작

**커밋:** (미커밋)
**요청:** (안정 우선 v2 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_rot_ccw_v2_continue_stage2.yaml` (신규), `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** v2 Stage 1 완주 — aligned_yaw_vel 0.507(목표 0.5 정확 수렴), anchor 0.123m, 평가 -2,196→+28,063 단조 상승(ep_len 44→1,542, best 2,895), v1의 붕괴 미재현으로 안정 우선 설계 검증. 말기 KL 1.9e-3 유휴 → 표준 레시피 n_epochs 2→3의 Stage 2를 final에서 재개(누적 28,413,952, γ 0.99 유지, 오버라이드 확인). 과제는 생존 길이 연장(1,542/6,000).

---

## 2026-09-06 — CCW v2 Stage 2 완주(best +35%, 정체 진입), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (안정 우선 v2 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_rot_ccw_v2_continue_stage3.yaml` (신규), `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** Stage 2 완주 — best 66,713 @ 45.5M(len 3,354, Stage 1 대비 +35%), 회전 품질 유지(aligned 0.574, anchor 0.113m)이나 평가 12~19K 정체·생존 길이 병목(ep_len ~800)·critic EV 0.026 저조. 계보 정착 처방(lr 1e-4→5e-5, ep 3→2)의 Stage 3를 final에서 재개(누적 56,827,904, 오버라이드 확인). EV 저조는 캠페인 후 검토 항목으로 기록. Stage 3 완료 시 CCW 캠페인 종료 → 동일 v2 설계로 CW 착수 예정(승인된 순차 계획).

---

## 2026-09-06 — CCW v2 캠페인 종료(best 97.8K), CW v2 Stage 1 시작

**커밋:** (미커밋)
**요청:** (승인된 순차 계획: CCW 완료 후 CW)
**파일:** `training/configs/ppo_plane_rot_cw_v2_from_scratch_long.yaml` (신규), `policies/rotation/cw/TRAINING_HISTORY.txt` (신규), `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** CCW Stage 3 완주 — best 97,757 @ 69.8M(len 4,408, +47%), aligned 0.570/anchor 0.099m. 계보 요약(49.4K→66.7K→97.8K)과 판정(안정 우선 목표 달성, 생존 일관성 미달·critic EV~0 상한, 개선 후보 3안) 기록. CW 캠페인을 거울 gait δ=135, joy=[0,0,-1], 동일 v2 설계로 시작 — run 20260906-071917, PID 216002. CCW 정책 폴더 정리는 승인 대기.

---

## 2026-09-06 — CCW Stage 4 연장 정착 시작 (CW Stage 1과 병렬)

**커밋:** (미커밋)
**요청:** CCW 추가 학습으로 안정성 개선 가능성 문의 → 분석(정체 증거 없음 + std 미소멸 = 개선 여지, 단 critic EV 병목은 별개) 제시 후 두 학습 동시 진행 승인.
**파일:** `training/configs/ppo_plane_rot_ccw_v2_continue_stage4.yaml` (신규), `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** Stage 3 final(누적 85.2M)에서 lr 5e-5→2.5e-5(후진 계보 검증 재반감), ep 2로 +28.4M 연장 — run 20260906-105101, PID 224694. CW Stage 1(PID 216002)과 병렬 실행 확인. 종료 감시 무장.

---

## 2026-09-06 — CW Stage 1 완주(거울 재현), Stage 2 시작

**커밋:** (미커밋)
**요청:** (CW 캠페인의 자동 진행, CCW Stage 4와 병렬)
**파일:** `training/configs/ppo_plane_rot_cw_v2_continue_stage2.yaml` (신규), `policies/rotation/cw/TRAINING_HISTORY.txt`
**변경:** CW Stage 1 완주 — yaw -0.532(목표 CW 속도)·anchor 0.126m로 거울 재현 성공, best 14,450 @ 23.3M은 CCW(49,413) 대비 약함(전 계보 일관 좌우 비대칭 부합). KL 7.4e-4 유휴 → n_epochs 2→3의 Stage 2를 final에서 재개(누적 28,413,952, 오버라이드 확인) — run 20260906-110000, PID 226200. CCW Stage 4 병렬 지속.

---

## 2026-09-06 — CW Stage 2 완주(5배 급등, CCW 추월), Stage 3 보수화 시작

**커밋:** (미커밋)
**요청:** (CW 캠페인의 자동 진행)
**파일:** `training/configs/ppo_plane_rot_cw_v2_continue_stage3.yaml` (신규), `policies/rotation/cw/TRAINING_HISTORY.txt`
**변경:** CW Stage 2 완주 — best 72,250 @ 55.0M(len 3,445, Stage 1 대비 5배, CCW Stage 2 66,713 추월로 좌우 격차 해소). 말기 KL 0.0071·평가 진동 → 보수화(lr 5e-5, ep 2)의 Stage 3를 final에서 재개(누적 56,827,904, 오버라이드 확인) — run 20260906-162555, PID 239619. CCW Stage 4 병렬 지속.

---

## 2026-09-06 — CCW Stage 4 완주: 추가 학습의 안정성 개선 실증 (+43%)

**커밋:** (미커밋)
**요청:** (CCW 연장 정착의 완결 — 사용자 질문 "추가 학습으로 안정성 개선 가능?"의 실증)
**파일:** `policies/rotation/ccw/TRAINING_HISTORY.txt`
**변경:** Stage 4(lr 2.5e-5) 완주 — best 139,915 @ 99.8M(len 5,705, 풀 에피소드 근접, +43%), 말기 평가 대역 46~67K 상향. std 어닐링 가설은 미실현(0.843), critic EV 0.111 지속 — Stage 5는 한계 이득 예상, 도약은 critic 개선 필요로 판정. CCW 대표 정책을 Stage 4 evaluation/best로 갱신. CW Stage 3 병렬 진행 중.

---

## 2026-09-06 — CW Stage 3 완주, 회전 캠페인(CCW+CW) 전체 종료

**커밋:** (미커밋)
**요청:** (CW 캠페인의 완결)
**파일:** `policies/rotation/cw/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** CW Stage 3(lr 5e-5/ep 2) 완주 — best 88,284 @ 71.0M(len 3,956, +22%), 마지막 평가 69,354/len 3,020 강한 마무리. CW 계보 14.5K→72.3K→88.3K, CCW(97.8K@Stage3) 대비 -10% 소폭 비대칭. 대표 정책 갱신, CW Stage 4 연장 선택지(~110-130K 기대) 기록. 이로써 회전 CCW(4-stage, 113.7M)+CW(3-stage, 85.2M) 캠페인 완료, 머신 유휴. 정책 폴더 정리는 승인 대기.

---

## 2026-09-06 — 회전 양방향 추가 연장: CW Stage 4 + CCW Stage 5 병렬 시작

**커밋:** (미커밋)
**요청:** 둘 다 학습을 더 진행하자는 승인.
**파일:** `training/configs/ppo_plane_rot_cw_v2_continue_stage4.yaml`, `training/configs/ppo_plane_rot_ccw_v2_continue_stage5.yaml` (신규 2종), 회전 원장 2종
**변경:** CW Stage 4 — CCW에서 +43% 검증된 lr 2.5e-5 처방으로 Stage 3 final 재개(누적 85.2M→113.7M, PID 249245). CCW Stage 5 — Stage 4 말기 KL 9.2e-4 비포화 진단에 따라 lr 2.5e-5 유지로 Stage 4 final 재개(누적 113.7M→142.1M, PID 249253; 추가 반감은 정체 위험이라 기각). 병렬 실행, 각 종료 감시 무장.

---

## 2026-09-07 — CW Stage 4 완주(105.6K, +20%), CCW Stage 5 병렬 지속

**커밋:** (미커밋)
**요청:** (양방향 연장의 자동 진행)
**파일:** `policies/rotation/cw/TRAINING_HISTORY.txt`
**변경:** CW Stage 4(lr 2.5e-5) 완주 — best 105,554 @ 97.8M(len 4,757, +20%, 100K 돌파). CW 계보 14.5K→72.3K→88.3K→105.6K 확정, 대표 정책을 Stage 4 best로 갱신. CCW Stage 5 완주 대기.

---

## 2026-09-07 — CCW Stage 5 완주(148.3K, 풀 에피소드 최초 달성), 회전 캠페인 전체 종료

**커밋:** (미커밋)
**요청:** (양방향 연장의 완결)
**파일:** `policies/rotation/ccw/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** CCW Stage 5 완주 — best 148,323 @ 126.8M에서 ep_len 6,000 풀 에피소드 생존 최초 달성, 마지막 10회 평균 59.3K(+50%). 최종 계보 CCW 5-stage(142.1M) 49.4K→148.3K / CW 4-stage(113.7M) 14.5K→105.6K. 대표 정책 갱신, 머신 유휴. 정책 폴더 정리 및 후속(critic 개선/통합 커리큘럼)은 사용자 결정 대기.

---

## 2026-09-07 — CW Stage 5 시작: 방위 학습의 마지막 run

**커밋:** (미커밋)
**요청:** 실패 원인 진단(앵커 표류 100%)과 norm_reward 미적용 확인 후, v3 재설계 대신 CW를 한 stage 더 학습해 CCW와 맞추고 방위 학습을 마무리하기로 결정.
**파일:** `training/configs/ppo_plane_rot_cw_v2_continue_stage5.yaml` (신규), `policies/rotation/cw/TRAINING_HISTORY.txt`
**변경:** CW Stage 4 final(누적 113.7M)에서 lr 2.5e-5 유지로 +28.4M — run PID 268157. v3 개선안 3종(norm_reward/복구시간/데드존)은 원장에 후보로 기록만. 완주 시 방위(8방위+회전 2종) 학습 전체 종결 보고 예정.

---

## 2026-09-07 — CW Stage 5 완주(138.3K), 방위 학습 전체 종결

**커밋:** (미커밋)
**요청:** (방위 학습 마무리 결정의 완결)
**파일:** `policies/rotation/cw/TRAINING_HISTORY.txt`, 메모리(direction-policy-campaign)
**변경:** CW Stage 5 완주 — best 138,349 @ 121.5M(len 5,582, +31%), CCW와 격차 -7%로 축소, 앵커 정밀도 0.099m. 최종 계보 CW 5-stage 14.5K→138.3K / CCW 5-stage 49.4K→148.3K (각 142.1M). 이로써 방위 정책 로스터 10종(8방위 이동 + 회전 2종) 완성, 방위 학습 종결. 대표 정책 갱신. 정책 폴더 정리는 승인 대기.

---

## 2026-09-07 — 회전 정책(CW·CCW) 폴더 정리 완료, 전체 로스터 보존 종결

**커밋:** (미커밋)
**요청:** CW·CCW 정책을 동일한 방법으로 정리해달라는 요청.
**파일:** `policies/rotation/ccw/{00_v1_experiments,01_ccw_v2_from_scratch,02~05_ccw_v2_stage*}/`, `policies/rotation/cw/{01_cw_v2_from_scratch,02~05_cw_v2_stage*}/` (runs/에서 이동), 원장 2종, 회전 YAML resume 경로 9건
**변경:** CCW 8개 run(v1 실험 3건은 00_v1_experiments/ 하위에 v1a 무계앵커중단·v1b 과속붕괴·v1c best재개중단으로 명명 보존, v2 계보 5건은 01~05) + CW 5개 run(01~05)을 규약대로 이동(콘솔 로그/pid 포함), 빈 runs/ 12개 디렉터리 제거. YAML resume 경로를 policies/ 위치로 갱신(잔여 runs/ 참조는 output_dir·주석뿐임을 확인). 무결성 검증: 양 대표 정책 1-episode 평가 정상 — CCW는 이동 전 실측과 비트 동일 리턴(23,596.120) 재현. 이로써 방위 로스터 전체(이동 8계보 + 회전 2계보, 총 37 run)가 policies/에 보존 완료.

---

## 2026-09-08 — Phase A: 통합 환경 plane-unified-v0 구축 (능동 gait 인터페이스 포함)

**커밋:** (미커밋)
**요청:** 멀티태스크 로드맵 Phase A 승인 + "사전 정의 gait를 넘어 패턴이 능동적으로 변경될 수 있는 것을 상정"한 신규 코드 요구.
**파일:** `horcrux_env/envs/gait_provider.py` (신규), `horcrux_env/envs/plane_unified_v1.py` (신규), `horcrux_env/{__init__,envs/__init__}.py` (plane-unified-v0 등록), `training/train.py` (norm_reward YAML 플래그, 기본 False), `training/callbacks/info_metrics.py` (명령별 에피소드 리턴/길이 로깅), `training/configs/smoke_unified.yaml` (신규)
**변경:** ① GaitProvider 추상화 — 명령→gait 결정을 환경 밖으로 분리, 기본 구현은 검증 10-명령 테이블. ② PlaneUnifiedWorld — reset마다 10개 명령 추첨(command_weights), 명령 조건부 보상(선형=방위 계보 보상 그대로/회전=v2 안정 우선 보상+NaN 함정 회피), 명령 조건부 건강(회전만 앵커 0.2m 조건, 복구 60스텝, 스텝당 1회 멱등 카운터 — 앵커 표류 진단 처방 반영). ③ 능동 gait API — set_gait(위상 진행률 보존 사상, 오차 0.0000 검증)·set_command, 계층적 RL 확장 지점. 검증 4종 전체 통과(10명령 매핑/NaN/분기 정합, 위상 보존 교체, 조건부 종료 의미론 — 회전 -1,091 종료·선형 3.7m 무종료, 추첨 분포 10/10) + 통합 환경 스모크 학습 완주. 학습 실행은 별도 승인 대기.

---

## 2026-09-08 — 통합 환경: 에피소드 중 회전 명령 전환 시 앵커 재설정 수정

**커밋:** (미커밋)
**요청:** "에피소드마다 1개 gait만 진행하나?"라는 질문에 답하는 과정에서 발견된 능동 전환 사용 사례의 잠재 결함 수정.
**파일:** `horcrux_env/envs/plane_unified_v1.py`
**변경:** set_command()가 회전 명령으로 진입할 때 앵커를 에피소드 시작 COM이 아닌 **현재 COM으로 재설정**하고 불건강 카운터를 초기화하도록 수정 — 기존에는 중간 전환 시 낡은 기준점으로 즉시 이탈 판정될 수 있었음. 검증: 전진으로 2.29m 표류 후 CCW 전환 → anchor_distance 0.007m 재설정, 즉시 종료 없음, 이후 종료는 새 앵커 기준 정상 판정. (기본 동작은 여전히 에피소드당 1명령 — 에피소드 중 재추첨 커리큘럼은 Phase C 확장 항목.)

---

## 2026-09-08 — 경로 추종 데모: 전문가 스위칭으로 사각형·별 완주 (Figure+영상)

**커밋:** (미커밋)
**요청:** 학습된 전문가 10명 + 고전 추종기로 웨이포인트 주행 실험, Figure 플롯과 비디오 녹화 기능 포함.
**파일:** `training/path_following.py` (신규)
**변경:** 경로 생성기(직선/사각형/별) + 웨이포인트 추종 커맨더(COM→목표 벡터를 body frame 변환 후 8-명령 양자화, 제어 주기 25스텝) + 전문가 뱅크(명령별 대표 정책 + 각자 VecNormalize 통계로 관측 정규화, NormalizeAction 역변환) + 통합 환경 set_command() gait 동기 전환 + rgb_array 녹화(MP4)·궤적 Figure(명령 구간 색상)·CTE 통계. 결과: 직선 2m(CTE 0.06m) → **사각형 2m 완주**(4/4, 41.2초, 순수 게걸음 — 회전 명령 미사용, CTE 평균 0.31/최대 0.97m, 전환 16회) → **별 1.5m 완주**(5/5, 143.8초, CTE 평균 0.38/최대 1.34m, 전환 70회 계단형). 뱀 로봇의 고전 난제(네모·별 경로)를 GD 레퍼토리 + 상위 추종기로 재현 성공. 개선 여지: backward 계열 전환 구간의 표류(사각형 최대 오차 지점), δ-보간 연속 조향, Phase C 통합 정책. 산출물 runs/path_follow_demo/.

---

## 2026-09-08 — 경로 추종 데모 시각화 개선 4종 반영 및 재실험

**커밋:** (미커밋)
**요청:** 렌더링 영상에서 실험 결과가 잘 안 보임 — ① 카메라 FOV 확대 ② 카메라를 CoM 동적 추적으로 ③ 계획 웨이포인트를 반투명 형광 초록 구로(도달 시 어둡게) ④ 로봇 경로를 세그먼트별 투명도 차등의 빨간선으로 실시간 표시.
**파일:** `training/path_following.py`
**변경:** ceiling 카메라 fovy 48→80(--cam-fovy 노출) + 매 스텝 model.cam_pos를 CoM으로 갱신(동적 추적). gymnasium OffScreenViewer add_marker로 렌더마다 씬 주입: 웨이포인트 구(현재 목표 최고 밝기 0.75α / 대기 형광 0.50α / 도달 어두운 초록 0.35α), CoM 궤적 점열(현재 세그먼트 0.80α 진한 빨강 / 지난 세그먼트 0.22α 흐림). 씬 geom 한도(1,000) 보호를 위해 궤적 마커 550개 균등 데시메이션. 재실험: 사각형 4/4·별 5/5 완주 재현(경로 성능 동일), 프레임 검수로 4개 요구사항 반영 확인. 720p 영상 2종 전달.

---

## 2026-09-08 — 경로 추종 결함 진단·수정: 전환 위상 보존 버그 + 위험 전환 라우팅

**커밋:** (미커밋)
**요청:** 사각형 경로에서 backward·right 정책이 오동작하는 것 같다는 관찰의 원인 확인 요청.
**파일:** `horcrux_env/envs/plane_unified_v1.py`, `training/path_following.py`
**변경/진단:**
① 단독 구동 진단: backward(오차 -1.1도)·right(+1.3도) 전문가 자체는 정상 — 혐의 해소.
② 8x8 전환 행렬 전수 진단으로 진범 특정: **set_gait의 위상 분율 보존이 이종 gait 전환에서 붕괴 유발**(거울 δ±180 쌍 등 12건, 최대 오차 157도·yaw 165도). 위상 분율은 실제 관절 형상과 무관하고, 전문가들은 모두 k=0 시작으로 학습됨. preserve_phase=False(k=0 재시작)로 위험 7쌍 전부 0.3~3.0도 정상화 → **set_gait 기본값을 False로 변경**(근거 docstring 기록), 위상 보존은 동일 gait 미세 조정 용도로만 권장.
③ 잔여 3쌍(역재생 후진대각 → 순재생 계열: bl→right 152도, bl→fr 61도, br→fl 156도)은 커맨더에 **전환 라우팅 테이블** 추가 — backward/forward를 1 제어주기(25스텝) 경유. 라우팅 실측: 3쌍 모두 0.1~2.9도.
④ 재실험: 사각형 CTE 평균 0.314→**0.193m**(최대 0.97→0.41m, 전환 16→5회), 별 0.381→**0.166m**(최대 1.34→0.66m, 전환 70→34회). Figure에서 사각형 4변·별 5획이 계획 경로에 밀착.

---

## 2026-09-08 — 소프트 핸드오프 실험 및 하이브리드 전환 채택

**커밋:** (미커밋)
**요청:** 통신의 소프트 핸드오프처럼 전환 시 두 정책의 행동을 함께 계산해 가중치를 점진 변경하는 방식 제안 — 검토 요청.
**파일:** `training/path_following.py`
**변경/실험:** 3방식 비교(위험 3쌍+거울쌍+일반쌍 7개 전환) —
① **행동 가중평균 블렌딩(제안 원형)은 GD 구조와 충돌**: 구 정책이 새 gait의 부호 패턴 위에서 동작해 리듬을 방해, 위험 쌍 미해결(113~125도)에 안전 쌍 악화(forward→right 3→83도).
② **에너지 페이드(감쇠→정지+gait 전환→상승)가 소프트 핸드오프의 올바른 GD 버전**: 정지유지 포함(20/15/20)로 전 위험 쌍 0.3~4.3도 정상화, 우회 라우팅 불필요.
③ 전 쌍 페이드 적용은 정지-재출발 비용으로 CTE 악화(0.19→0.39~1.24m) — 중간에 디바운스/체류 시도는 오버슈트 캐스케이드 오진으로 판명(원인은 페이드 제동 거리), 폐기.
**최종 채택: 하이브리드** — 기본 즉시 k=0 전환 + 위험 3쌍(역재생 후진대각→순재생 계열)만 소프트 페이드. 라우팅 테이블 제거, 제어 틱을 실스텝 기준으로 재구성(do_step 헬퍼, 페이드 중에도 기록/카메라 유지). 재실험: 사각형 0.193m/5전환, 별 0.166m/34전환 — 최고 기록 유지하면서 메커니즘 일반화.

---

## 2026-09-08 — Fade Gauntlet 경로 + 페이드 계측 + 각도 히스테리시스

**커밋:** (미커밋)
**요청:** 페이드가 실제 적용된 웨이포인트 추종 결과를 보여달라는 요청.
**파일:** `training/path_following.py`
**변경:** ① 위험 전환 3쌍(bl→right, br→fl, bl→fr)을 순차 강제하는 'gauntlet' 지그재그 경로(6 웨이포인트) 추가. ② 전환 통계에 소프트 페이드 발동 횟수 계측(제목/result.txt). ③ 대각 세그먼트의 양자화 경계 채터링(전환 65회) 해결을 위해 커맨더에 각도 히스테리시스 추가 — 55도는 교정 억제로 사각형/별 CTE 악화(0.19→0.57/0.17→0.71) 확인 후 34도(반섹터 22.5도+여유)로 확정. 결과: gauntlet 6/6 완주·페이드 3회 전부 발동(CTE 0.303m), 사각형 최고 기록 유지(0.193m/5전환), 별 0.271m/13전환(전환 수 절반, CTE 소폭 상승 트레이드오프).

---

## 2026-09-08 — 페이드 시간 분포 재조정: (20,15,20)→(10,5,10), 2.75초→1.25초

**커밋:** (미커밋)
**요청:** 페이드 각 단계의 시간 구분 확인 및 시간 분포 조정 요청.
**파일:** `training/path_following.py`
**변경:** 9개 분포 스윕 + 강건성 검증(위험 3쌍 × 진입 위상/시드 5변형 = 15조건). 발견: 기존 (20,15,20)은 단일 조건에서만 안전했고 위상이 바뀌면 3/15 실패(최악 99.4도) — 실패 패턴이 비단조적(전환 시점 gait 위상 민감). **(10,5,10) = 감쇠 0.5s/정지 0.25s/상승 0.5s, 총 1.25초가 15/15 전 조건 통과(최악 3.8도)로 유일한 완전 강건 + 55% 단축**. 적용 후: 사각형 0.193m 유지, 별 최대 오차 0.97→0.71m 개선, gauntlet 인스턴스는 0.30→0.49(제동 거리 변화로 핸드오프 후 명령 시퀀스가 달라진 경로 수준 변동 — (12,8,12)도 0.43으로 유사, 전환 품질 문제 아님을 확인). 통제 실험 우선 원칙으로 (10,5,10) 확정.

---

## 2026-09-08 — 위상 정렬 전환 채택(페이드 대체), 결정적 A/B 비교

**커밋:** (미커밋)
**요청:** 페이드 대신, 새 gait를 다음 motion vector와 유사도가 높은 위상부터 시작하는 알고리즘 적용 제안.
**파일:** `horcrux_env/envs/plane_unified_v1.py` (set_gait align_phase 옵션), `training/path_following.py` (ALIGN_PAIRS 선택 적용, 페이드/settle/close_freeze 실험 정리)
**변경:** set_gait에 align_phase 구현 — 새 gait 한 주기 중 현재 motion vector와 부호 유사도(내적) 최대인 위상 k에서 시작. 핵심 발견 두 가지: (1) 격리 위험쌍 테스트는 152/61/156도→1.0/0.5/3.1도로 극적, 그러나 (2) **전체 사각형 A/B에서 전면 위상정렬은 오히려 악화(k=0 0.193 vs align 0.448)** — 전문가가 모두 k=0 학습이라 안전 전환엔 익숙한 k=0가 최적, 위상정렬 이득은 부호 충돌 위험쌍에서만 발생(페이드와 동일한 선택 구조). 따라서 **위험 3쌍만 위상정렬**, 나머지 k=0. 결정적 3방식 A/B(다른 조건 고정): square 3방식 동일(위험쌍 없음), star align 0.433 > fade 0.497 > hard 0.742, gauntlet fade 0.301 > align 0.472 > hard 0.485. 위상정렬·페이드 모두 hard를 이기며, **위상정렬 채택 — 시간 지연(0.75s)·감속 표류 0의 근본책**. 쇼케이스: bl→right에서 hard 172.8도 vs align 0.9도. 페이드 관련 상수/로직 및 실패한 settle/전면적용 실험 제거.

---

## 2026-09-08 — (음성 결과) 위상 매칭의 다중 벡터 윈도우 확장 검증·기각

**커밋:** (미커밋, 코드 변경 없음)
**요청:** 단일 motion vector 대신 이전 W개 벡터(궤적 윈도우)를 비교해 위상을 정렬하면 어떨지 검토.
**변경:** 위험 3쌍 + 안전 4쌍에서 W=1 vs W=5 vs W=10 슬라이딩 윈도우 매칭 실측. 결과: W=1이 전 쌍 ≤3.1도로 안전한 반면, 윈도우 확장은 W=1이 잘 처리하던 쌍을 오히려 붕괴시킴(right→left 0.6→10.2도@W5, diag_fl→diag_fr 1.0→113.6도@W10). 원인: (1) 전환 토크 연속성은 현재 부호 패턴 하나에만 의존하고 과거는 이미 물리 상태(qpos/qvel)에 반영됨, (2) 두 gait의 주기(Mvecs) 불일치로 구 리듬이 새 gait의 W-구간과 정합 불가 → argmax가 엉뚱한 고득점 위상에 착지, (3) 역재생 gait는 위상 인덱스가 열 번호와 비선형 대응이라 정방향 윈도우 가정 붕괴. 결론: **단일 벡터 매칭(W=1) 유지** — 순간 매칭으로 충분하고 더 강건. 재논의 방지용 기록.

---

## 2026-09-08 — (음성 결과) 위상정렬 + 페이드 결합 검증·기각

**커밋:** (미커밋, 코드 변경 없음)
**요청:** W=1 위상 정렬을 유지하면서 페이드도 함께 주는 경우 검토.
**변경:** 위험 3쌍 + 안전 3쌍에서 hard/align/fade/align+fade 4방식 비교. 결과: align 단독이 전 쌍 1~3도·최소 yaw 과도로 최선. 결합(align+fade)은 이득 없이 diag_bl→diag_fr를 1도→76도로 붕괴시킴(align이 완벽히 처리하던 쌍). fade 단독도 안전 쌍 diag_fl→diag_fr를 19도로 악화. 원인: 페이드의 임무(에너지 0으로 부호충돌 회피)를 위상정렬이 이미 근본 제거 → 결합은 상보가 아닌 중복이며, 페이드의 감속-재가속이 교체 시점 현재벡터를 바꿔 정렬을 흩뜨림. 결론: **align 단독(W=1) 유지, 페이드 미사용**. 재논의 방지 기록.

---

## 2026-09-08 — (진단 정정) 페이드의 정지(HOLD) 제거 실험

**커밋:** (미커밋, 코드 변경 없음)
**요청:** 페이드에서 정지 구간을 없애면 align+fade 결합 결과가 달라지는지 검토.
**변경:** fade(10,5,10) vs fade-nohold(10,0,10)를 align과 결합 비교. 발견: 앞 항목에서 align+fade가 붕괴시킨 diag_bl→diag_fr(76도)가 **정지를 없애니 2도로 정상화** — 결합 실패의 범인은 페이드가 아니라 정지 구간이었음. 정정된 원인: HOLD 동안 토크 0이어도 로봇이 잔여 관성으로 형상이 변하는데 위상정렬 k는 정지 진입 시점 벡터로 고정돼 있어, 상승 시 형상-위상 괴리 발생(정지 길수록 악화). 단 fade-nohold+align도 align 단독을 넘지 못함(right→left 1→7도, diag_fl→diag_fr yaw 28→43도). 결론 불변: **align 단독(W=1) 유지** — 부호 연속성이 이미 확보돼 페이드는 정지 유무와 무관하게 추가 이득 없음. (참고: 순수 페이드 k=0에서는 정지가 필수였음 — 부호충돌 에너지 소거용. align이 충돌을 없앤 뒤로는 정지가 해로움.)

---

## 2026-09-08 — 매끄러운 전환 해결책: 위상정렬 + 선택적 행동 크로스페이드

**커밋:** (미커밋)
**요청:** gait 전환을 안정적이고 매끄럽게 하는 해결책을 스스로 찾아달라는 요청.
**파일:** `training/path_following.py`
**변경:** '매끄러움'을 정량 지표로 신규 정의(전환창 스텝당 COM 속도변화 jerk_vel, 헤딩변화 jerk_head, IMU 선가속 스파이크 acc_spike)하고 후보 5종 계측(hard/align/align+토크저역통과/align+크로스페이드/align+정책블렌딩). 발견: (1) align은 안정성은 해결하나 위험쌍 acc_spike 142로 잔여 저크 존재. (2) align_xfade(위상정렬 후 구·신 정책 행동 12스텝 선형 크로스페이드)가 위험쌍에서 acc_spike 142→89·jerk_head 120→98로 최고 매끄러움 + 안정성 동일(0.9도). (3) 모든 진폭 변조(xfade/lowpass/softstart)는 안전쌍을 악화(정상 전환 약화)시키므로 위험쌍에만 선택 적용해야 함. (4) 크로스페이드는 위상정렬 위에서만 유효 — 정렬로 gait 부호 문맥이 일치해야 두 행동의 선형결합이 의미를 가짐(정렬 없는 블렌딩은 과거 실험서 붕괴). **채택: 안전쌍=즉시k0, 위험 3쌍=위상정렬+크로스페이드(12스텝).** 데모 검증: 매끄러움뿐 아니라 경로 CTE도 개선(star 0.433→0.334, gauntlet 0.472→0.345, square 0.193 유지). 쇼케이스: bl→right acc_spike 155→57(63%↓). XFADE_STEPS 파라미터 노출.

---

## 2026-09-09 — 경로 추종 렌더: 웨이포인트 방위 화살표 + 로봇 방위 화살표 (1단계)

**커밋:** (미커밋)
**요청:** 경로 추종 실험이 회전을 감안하지 않는다는 지적. 초록 구를 화살표로 바꿔 웨이포인트 방위까지 표현하도록 렌더 환경 수정 요청. (합의: 1단계 렌더만 먼저, 방위 기본값 = 접선.)
**파일:** `training/path_following.py`
**변경:** (1) `make_path`가 (N,3) `[x, y, yaw_deg]` 반환 — `with_tangent_headings`로 접선 방위 부여(각 점에서 다음 점 방향, 마지막 점은 도착 방향). (2) `WaypointCommander`가 `waypoints[:, :2]`와 `headings`를 분리 보관(추종 로직 변경 없음 — 1단계에서는 표시용). (3) `add_scene_markers`: 구 → `mjGEOM_ARROW`(밑동=위치, 방향=목표 방위) + 작은 밑동 구, 색 규칙 유지; 로봇 CoM 위 파란 화살표로 몸통 yaw 표시. `heading_matrix`가 yaw→마커 회전행렬(z축=방위, y축=세계+Z) 생성 — 0/90/180도 렌더 실증으로 규약 확인(화살표는 pos에서 시작해 로컬 +z로 뻗음). (4) trajectory.png에 목표 방위 quiver 추가. 결과 수치 불변(square 0.193, star 0.334)으로 렌더 전용 변경 확인. 영상에서 크랩워크 추종의 몸통 yaw(≈0)와 접선 목표 방위의 차이가 바로 읽혀 2단계(회전 전문가 추종)의 필요성이 시각화됨.

---

## 2026-09-09 — gait 전환 학습 파이프라인 구축 (전환 커리큘럼 env + 전문가 증류 + Stage 1 설정)

**커밋:** (미커밋)
**요청:** 이전 학습 정책에서 이어서 gait 전환을 훈련. 모든 전환 쌍을 랜덤으로, 전환 시점·위치(상태)도 다양하게. 합의: 출발점은 10명 전문가 증류(B), 전환 메커니즘은 위상 정렬(align), Stage 1 40M. 아울러 사용 알고리즘 학술자료 정리 요청.
**파일:** `horcrux_env/envs/plane_unified_v1.py`, `training/distill_experts.py`(신규), `training/callbacks/info_metrics.py`, `training/configs/ppo_unified_transition_stage1.yaml`(신규), `docs/references_transition_learning.md`(신규)
**변경:**
- **통합 env 전환 커리큘럼** (`switch_enabled` 기본 꺼짐 → 기존 동작 보존): reset마다 전환 횟수 `switch_count_range`(1~4)·시점(최소 체류 `switch_min_dwell` 100스텝 간격, 에피소드 내 균등)을 예약하고, 다음 명령은 현재 명령을 제외한 나머지에서 추첨(`switch_pair_weights` (n,n)로 가중 가능, 기본 균등 → 90 순서쌍). 전환은 **물리 스텝 뒤·관측 반환 전**에 적용해 정책이 그 스텝 관측에서 새 motion vector/joy를 즉시 본다(1스텝 불일치 없음; 해당 스텝 보상은 옛 명령 기준). `switch_mode` align/k0/random. `random_init_phase`로 초기 위상 k 무작위. `episode_horizon`으로 부모의 6000스텝 truncation을 짧게 덮어씀. info에 `switched/switch_from/switch_to/switch_aligned/switch_count/steps_since_switch`.
- **부모 reset의 `_motion_vector` 미갱신 보정**: 부모는 reset에서 `_motion_vector`를 갱신하지 않아 이전 에피소드의 벡터가 첫 스텝에 잔존한다(첫 에피소드는 0 벡터). 통합 env는 gait가 에피소드마다 바뀌므로 reset에서 현재 gait의 k 벡터로 명시 초기화.
- **`set_gait` 역재생 gait 정렬 버그 수정**: `getMvec(k)`는 역재생 gait면 열 `-k`를 돌려주므로, 유사도 최대 열 `col`에서 시작하려면 `k=-col`이어야 한다. 이전에는 순재생 목표 gait(위험 3쌍)만 검증돼 드러나지 않았다. 스모크에서 역재생 목표 12회 포함 50회 전환 모두 "시작 벡터 유사도 = 새 gait 최대 유사도" 확인.
- **스모크에서 발견한 함정**: env kwarg를 `max_episode_steps`로 지으면 `gym.make`가 자기 인자로 가로채 env에 전달되지 않는다(TimeLimit 래퍼만 걸림) → `episode_horizon`으로 개명.
- **콜백** `env_switch/*`: 전환 후 50스텝 평균 보상(`post50_reward`), 100스텝 내 종료 비율(`fail_within100`), 도착 명령별 분해(`*_to_XX`), 에피소드당 전환 횟수(`per_episode`). TB 기록 확인.
- **증류 스크립트** `distill_experts.py`: (1) 전문가 10명을 통합 env(명령 고정, RL YAML과 동일 보상)에서 병렬 롤아웃 → 원본 관측·전문가 행동·보상 기록, (2) 통합 obs_rms, (3) PPO MlpPolicy 동일 구조 학생: actor MSE 모방 + critic을 γ=0.99 MC return에 회귀(절단 꼬리 300스텝 마스크, 출력 편향 = return 평균 초기화, 별도 옵티마이저), log_std −1.2, (4) DAgger 옵션, (5) 명령별 학생 vs 전문가 평가(리턴·낙상·진행속도·yaw·앵커), (6) `model.zip`+`vecnormalize.pkl`+`metadata.json`+`DISTILL_REPORT.md`. train.py resume(n_steps/batch/gamma 불변 검사)와 호환 확인.
- **v1 증류 결과(결정론 롤아웃만, `policies/unified/00_distilled_v1_det_only`)**: 검증 MSE 0.0025로 데이터 안 모방은 정확하나 닫힌 루프에서 left/right/cw 100% 낙상, diag_fr 역방향 — 전형적 공변량 이동(결정론 전문가+동일 초기 자세 → 얇은 상태 분포, 통합 정규화 std가 좁아 이탈 상태가 ±10 클리핑으로 증폭). 처방으로 **전문가 자체 가우시안 노이즈 실행(DART식, 라벨은 평균 행동) 수집 옵션** `--stochastic-steps-per-command` 추가 + DAgger 적용 → v2 진행.
- **Stage 1 YAML**: `plane-unified-v0` + 전환 커리큘럼(align, 1~4회, dwell 100, 초기 위상 무작위, horizon 1000), 방위 계보 보상 계수 frozen, γ 0.99, 검증된 Stage 1 값(lr 1e-4, ep 2, target_kl 0.04), 40M, resume=`policies/unified/00_distilled`. 학습 착수는 사용자 승인 후.
- **학술자료** `docs/references_transition_learning.md`: 8개 주제 48편(PPO 기초, BC/DAgger, 정책 증류, BC→RL 워밍업, 다중작업 RL, 지속 RL, 다중 보행 다리 로봇, 뱀 로봇/CPG), 서지정보 웹 검증, 파이프라인 대응표 포함.

---

## 2026-09-09 — 전문가 증류 완료 (v2 + DAgger 4회), 통합 정책 원장 신설

**커밋:** (미커밋)
**요청:** (위 항목의 연속) 증류 v1의 닫힌 루프 실패 처방 실행.
**파일:** `training/distill_experts.py`(`--stochastic-steps-per-command`, `--init-model` 이어가기 옵션), `policies/unified/00_distilled/`, `policies/unified/TRAINING_HISTORY.txt`(신규)
**변경:** v2 = 결정론 40만 + 전문가 노이즈 실행 40만 + DAgger 2회 → 9/10 명령 0.96~1.14, 낙상 0, cw 0.78. cw 보강으로 DAgger 라운드 3·4(이어가기) → 최종 forward/diag_fr/diag_bl/diag_br 1.00, ccw 1.01, right 0.99, left/diag_fl 0.98, backward 0.95, **cw 0.60**(앵커 드리프트로 729스텝 종료; 노이즈 0.05에서 5/8 생존 — 칼날 상태, BC 라벨에 앵커 복귀가 없어 DAgger로 미개선). 판단: RL 단계(앵커 비용+종료 페널티)가 교정할 알려진 출발 조건으로 기록하고 Stage 1 착수는 사용자 승인 대기. v1/v2 산출물은 `00_distilled_v1_det_only`, `00_distilled_v2_dagger2_backup`으로 보존. 콘솔 로그는 `00_distilled/console_*.log`.

---

## 2026-09-09 — Stage 1 gait 전환 학습 착수 (설정 검토 반영)

**커밋:** (미커밋)
**요청:** 설정 검토 후 착수. 검토 결과 반영: 평가 에피소드 5→10 (전환 무작위성으로 인한 best_model 선택 요동 완화). 나머지(균등 90쌍, num_envs 8, lr 1e-4)는 유지.
**파일:** `training/configs/ppo_unified_transition_stage1.yaml`
**변경:** `scripts/launch_training.sh ... stage1`로 분리 실행. run `runs/ppo_unified_transition_stage1/20260909-145708-553412_…`, PID 24994, resume `policies/unified/00_distilled/model.zip` 확인, 초기 fps ≈ 2,200 (40M ≈ 5시간). 감시 포인트: 첫 2M 스텝의 eval 리턴 추이(BC 초기값 붕괴 여부), `env_switch/fail_within100`, approx_kl, explained_variance.

---

## 2026-09-09 — 회전 앵커: 종료 규칙 → 근접 보상 (전환 학습용 설계 변경), Stage 1 재시작

**커밋:** (미커밋)
**요청:** 2M 스텝 점검에서 회전 진입 전환 실패(cw 0.63/ccw 0.60)의 원인이 관성 미끄러짐(전환 직전 0.44 m/s → 앵커 최대 0.37 m)이 전환 순간 고정된 앵커 0.2m/60스텝 종료 규칙에 걸리는 것으로 진단됨(증류 정책 진단: 회전 진입 54% 종료, 선형 진입 9%). 유예 재앵커를 제안했으나 사용자가 **"종료 대신 앵커에 가까우면 더 높은 보상"**을 제안 → 그 설계로 합의.
**파일:** `horcrux_env/envs/plane_unified_v1.py`, `training/callbacks/info_metrics.py`, `training/configs/ppo_unified_transition_stage1.yaml`
**변경:** 통합 env에 `anchor_terminate`(기본 True=기존 동작), `anchor_proximity_reward_weight`(기본 0), `anchor_proximity_radius`(0.2) 추가. `_rotation_rew`에 근접 보상 `w·max(0, 1−d/r)` 가산(info `reward_anchor_proximity`), `is_healthy`/`is_terminated`의 앵커 조건은 `anchor_terminate`일 때만. 기존 포화 앵커 비용 유지. YAML: `anchor_terminate: false`, weight 10, radius 0.2 — 스텝당 수지(목표 속도 회전≈25): d=0 +35, 0.2m +15, 0.4m +5, ≥0.55m 음수. 근접 보상 10 < 회전 보상 22.5로 "정지가 회전보다 유리" 국소해 차단. 검증: 보상 프로파일 설계대로(d<0.1 +30.7, 0.1–0.2 +22.4, 0.2–0.3 +17.8), 회전 진입 100스텝 내 종료 54%→19%(잔여는 낙상), 기본값 env는 옛 동작 그대로(cw 729스텝 앵커 종료 재현, 근접 보상 0). 이전 run(20260909-145708, 4.25M 스텝, 옛 앵커 의미)은 중단·보존(`console_stage1_aborted.log`). 2M 점검 요약: 붕괴 없음(ep_rew −9k 저점 후 +4.2k, ep_len 255→717, EV 0.51 회복, KL 0.003~0.008).

---

## 2026-09-09 — Stage 1 전환 학습 완료 보고 (40M), Stage 2 계획

**커밋:** (미커밋)
**요청:** (승인된 3-stage 루프의 stage 전환 — CLAUDE.md 예외 2: 단계 완료 보고에 다음 단계 계획 명시)
**결과:** run 20260909-153324, 40.0M 스텝, 21:05 종료. 최고 평가 22,624 @ 27.5M, 마지막 19,244, 최근 10회 평균 15,115. 말기 ep_rew 13.0K(초반 −16K), ep_len 873, 전환 후 100스텝 실패율 0.123→0.099, 전환 후 50스텝 보상 −31.9→−8.5, EV 0.921, KL 0.0010(유휴), clip 0.0015, std 0.301(변화 없음). 도착 명령별 실패율: diag_fr 0.33, diag_bl 0.33(둘 다 δ=203 gait), 나머지 ≤0.10 — 회전 진입 실패는 근접 보상 설계로 해소(ccw 0.10, cw 0.03).
**Stage 2 계획:** 검증 레시피대로 KL 유휴 → `n_epochs 2→3`, lr 1e-4·target_kl 0.04 유지, Stage 1 final(model+vecnormalize) 재개, 40M. 평가 에피소드 10→20(선택 잡음 완화, 정책 무관). 환경·보상·커리큘럼 불변.

---

## 2026-09-09 — Stage 2 전환 학습 착수 (n_epochs 3)

**커밋:** (미커밋)
**요청:** 승인된 3-stage 루프의 stage 전환 (예외 2). Stage 1 완료 보고의 계획대로 실행.
**파일:** `training/configs/ppo_unified_transition_stage2.yaml`(신규)
**변경:** Stage 1 final(model+vecnormalize, runs/ 경로) 재개, n_epochs 2→3, lr 1e-4·target_kl 0.04·gamma 0.99 유지, 평가 에피소드 10→20, 40M 추가. `scripts/launch_training.sh … stage2`, run 20260909-210657, PID 35021, 로그에서 `n_epochs=3` 확인, fps ≈ 2,140.

---

## 2026-09-09 — 경로 추종 데모에 통합 정책 모드 추가, Stage 1 정책 렌더링

**커밋:** (미커밋)
**요청:** 지금 학습된 정책의 경로 추종 성능을 이전처럼 렌더링해 채팅에 표시. (체크포인트: Stage 1 final 40M 선택.)
**파일:** `training/path_following.py`, `horcrux_env/envs/plane_unified_v1.py`
**변경:** `--policy unified --model --vecnorm` 모드(`UnifiedPolicy`): 단일 정책+통합 정규화, 명령 전환 시 학습(전환 커리큘럼)과 동일하게 `set_command(align_phase=True)` 후 `current_observation()`(신규 공개 메서드, 동작 변경 없음)으로 관측을 즉시 재생성 — 크로스페이드 없음, 전환 처리는 정책 몫. 기존 전문가 모드 기본값 불변. 산출 폴더 접미사 `_unified`, result.txt 설정 줄 모드 반영.
**결과 (통합 정책 vs 전문가 스위칭+크로스페이드):** square 0.180 m/8전환/37.5 s (vs 0.193/5/20 s), star 0.343/15/58.8 s (vs 0.334/10/42.5 s), **gauntlet 0.253/13/58.8 s (vs 0.345/34/128.8 s)** — 위험 전환이 몰린 gauntlet에서 CTE −27%, 전환 횟수 1/3, 시간 절반. 사각형·별은 CTE 동급이나 주행 시간이 길고 전환이 잦음(순항 속도·전환 직후 감속) → Stage 2·3 추이 관찰 포인트.

---

## 2026-09-09 — 연구 흐름 정리 PPT 생성

**커밋:** (미커밋)
**요청:** 지금까지의 실험 결과와 증류 등을 꼼꼼히 정리한 PPT. 생성한 영상·피규어를 넣고, 그림/영상 슬라이드마다 의도와 결과 요약을 달아 연구 흐름을 따라갈 수 있게.
**파일:** `docs/Horcrux_transition_research_2026-09.pptx`(신규, 24장, 약 10.5 MB), 생성 스크립트는 세션 스크래치(`build_deck.py`, python-pptx)
**변경:** 구성 — 표지/흐름 타임라인/배경(GD·로스터·레시피·회전 v2) → Part 1(데모 설계, 문제 발견, 메커니즘 ①페이드 ②위상 정렬, 3방식 A/B+기각 3건, 매끄러움 하이브리드, 방위 렌더) → Part 2(설계 결정, 증류 파이프라인·결과, 전환 커리큘럼 env, 앵커 근접 보상 설계, Stage 1 결과, Stage 2 상황, 통합 정책 경로 추종) → 통찰 7·다음 단계·참고문헌/산출물·부록. 영상 12개 임베드(포스터 프레임 포함), 학습 곡선은 TensorBoard 직접 추출한 네이티브 차트, 비교 수치도 네이티브 차트. 모든 수치는 CLAUDE_CHANGES/원장/result.txt 기록값. 도구: node/pptxgenjs 부재로 python-pptx(+lxml, defusedxml) 설치 후 사용; validate.py 통과, LibreOffice 렌더 24장 시각 QA(제목 줄바꿈·캡션 겹침·배지 번호·상자 넘침 10곳 수정).

---

## 2026-09-10 — Stage 2 완료 보고, Stage 3 설정 (lr 2e-4)

**커밋:** (미커밋)
**요청:** 승인된 3-stage 루프의 stage 전환 (예외 2).
**파일:** `training/configs/ppo_unified_transition_stage3.yaml`(신규), `policies/unified/TRAINING_HISTORY.txt`
**결과 (Stage 2, 누적 80M):** 최고 평가 24,102 @62.8M, 최근 10회 평균 16,965(+12%), 롤아웃 리턴 14.8K→15.0K 횡보, 전환 후 실패 0.097 정체, KL 0.0028(유휴)·clip 0.011·EV 0.93·std 0.302 고정. 도착 명령별 실패 diag_bl 0.35 / diag_fr 0.33(δ=203) 그대로, ccw/cw 0.
**Stage 3 계획:** Stage 2 final 재개, **lr 1e-4→2e-4**(신뢰 영역 여유 1/14 활용, target_kl 0.04 안전장치), n_epochs 3·γ 0.99·환경·커리큘럼 불변, 40M(누적 120M), 평가 20. 병행: δ=203 도착 실패의 구조적 원인(정렬 품질) 진단.

---

## 2026-09-10 — Stage 3 착수 (lr 2e-4) + δ=203 도착 전환 실패 진단

**커밋:** (미커밋)
**요청:** 승인된 3-stage 루프의 마지막 stage 전환 (예외 2) + 정체 원인 진단.
**변경:** `scripts/launch_training.sh … stage3`, run 20260910-031109, PID 71496, `learning_rate=0.0002, n_epochs=3` 확인, fps ≈ 2,190 (완료 08:20경).
**진단 (코드 변경 없음):** (1) 정렬 품질 행렬 — gait가 두 부호 가족({forward, backward, diag_fl, diag_br, left} / {right, diag_fr, diag_bl})으로 갈리며 가족 간 전환은 어느 위상에서도 유사도 5~6/14. (2) Stage 2 정책의 δ=203 진입 실험(출발 6 × 변형 3 × 6회): diag_fr 진입은 20스텝 정지 후 시작 시 낙상 ≈0(정책 0~0.83) → 진폭 조절로 회피 가능하나 정책이 발견 못 함; diag_bl 진입은 정지해도 낙상 0.17~0.83(악화) → 정렬 위상 자체가 부적절한 시작점(가족 간 유사도가 고르게 낮아 argmax가 임의). 후속 후보: 가족 간 전환용 상태 인식 정렬(관절 속도 부호 기준), δ=203 도착 쌍 가중 커리큘럼, 탐색 폭 확대 — 모두 사용자 결정 필요.

---

## 2026-09-10 — Stage 3 완료 (누적 120M), 3-stage 전환 학습 루프 종료

**커밋:** (미커밋)
**결과:** run 20260910-031109, 09:10 종료. 최고 평가 23,101 @111.3M, 마지막 10회 평균 16,179(Stage 2 16,965과 잡음 범위). 말기 ep_rew 14.6K, 전환 후 실패 0.074, KL 0.010~0.012(lr 2e-4로 유휴 탈출, 정상 범위), clip 0.059, EV 0.92. 도착 명령별: diag_bl 0.35→0.12(개선), diag_fr 0.33→0.26, ccw 0→0.12. 후속: 5개 체크포인트 고정 시드 벤치마크와 통합 정책 경로 추종(Stage 3 final)으로 대표 체크포인트 선정 → 정책 폴더 정리는 사용자 요청 시.

---

## 2026-09-10 — 연구 정리 PPT를 사용자 템플릿(ETRI 4:3)에 맞춰 재구성

**커밋:** (미커밋)
**요청:** 전달한 PPT가 사용 중인 템플릿과 달라, 업로드한 샘플 템플릿(docs/PPT샘플.pptx)에 맞게 수정 요청.
**파일:** `docs/Horcrux_transition_research_2026-09_template.pptx`(신규, 29장, 11.8 MB); 생성 스크립트 세션 스크래치 `build_deck_template.py`
**변경:** 템플릿을 base로 열어 샘플 슬라이드를 제거하고 레이아웃('제목 슬라이드'/'간지'/'속지-제목만')·마스터(ETRI 로고·아이콘)·테마를 유지한 채 재구성. 샘플에서 추출한 규약 적용 — 제목 "gait 전환 학습 (20260910) ― 소제목"(맑은 고딕 bold 203864, 길이별 16/14/12.5pt), 카드 EEF3FA/C7D3E3 + ▪ 불릿(2E75B6), 캡션 8.5pt 8A8A8A, 표 헤더 203864. 4:3(10×7.5 in)에 맞춰 24장 → 29장으로 분할(배경 2장, 매끄러움 2장, 앵커 문제 2장, 통합 정책 2장), Stage 2·3 완료 결과(리턴/KL 곡선, 도착 명령별 실패율 S2 vs S3), 정체 원인 진단(부호 가족 유사도 행렬, δ=203 진입 실험), 체크포인트별 경로 데모 비교표 추가. validate.py(--original 템플릿) 통과, 29장 렌더 QA(긴 제목 아이콘 겹침·간지 글자색 수정).

---

## 2026-09-10 — 체크포인트 고정 시드 벤치마크, 대표 체크포인트 권고, 템플릿 덱 부록 추가

**커밋:** (미커밋)
**결과:** 40개 동일 시드 전환 에피소드로 S1 final / S2 best / S2 final / S3 best / S3 final 비교 — 리턴 16.3~17.0K(sd 1.3~1.7만, 동급), 전환 후 100스텝 실패 0.164→0.137→0.090→0.083→**0.066**, δ=203 도착 실패 0.25→**0.06**(S3 final), 완주율 0.65~0.80. 권고: **S3 final**(전환 강건성), 차선 S2 final(생존율 0.80). 단일 결정론 경로 데모의 편차(S3 final 사각형 0.447)는 잡음으로 해석. 벤치마크는 처음 spawn Pool로 두 번 멈춤/중단(코드 144) → 순차 실행 파일 스크립트로 완료. 템플릿 덱에 부록 ②(벤치마크 표 + 권고) 추가해 30장으로 재생성·재검증.

---

## 2026-09-10 — 통합 정책 성능 시각화 영상 (policy_showcase.py)

**커밋:** (미커밋)
**요청:** 지금 학습된 정책의 성능을 동영상으로 시각화. (합의: S3 final, 명령 투어 + 전환 클로즈업 + 경로 3종, 오버레이 포함)
**파일:** `training/policy_showcase.py`(신규)
**변경:** 명령 투어(10개 명령 순차 전환, 세그먼트 6 s, 학습 규약과 동일한 위상 정렬 전환 + 관측 즉시 재생성), 위험 전환 클로즈업(전환 후 150스텝 1/2 배속, 5쌍), 경로 추종 3종(path_following의 커맨더·경로·마커 재사용). 오버레이는 PIL 후처리(현재 명령·세계 좌표 목표 방향 나침반·전환 경과·전환 횟수·14관절 행동 진폭 바·불건강 경고·전환 플래시), 마커는 궤적 점열·전환 지점(노란 박스)·로봇 yaw 화살표. 산출 `runs/policy_showcase/20260910-111945_S3final/` + summary.txt. 결과: 투어 중 불건강 스텝 diag_fr 12 / diag_bl 24 / diag_fl 63(연쇄), 나머지 0; 클로즈업 backward→diag_bl 61스텝 불건강(낙상), 나머지 4쌍 0; 경로 square 0.341 m/24회/91 s, star 0.306/13/61 s, gauntlet 0.223/7/32.5 s.

---

## 2026-09-10 — 템플릿 덱에 정책 시각화 슬라이드 3장 추가 (33장)

**커밋:** (미커밋)
**요청:** 시각화 내용을 정리해 슬라이드에 추가.
**파일:** `docs/Horcrux_transition_research_2026-09_template.pptx` (30 → 33장, 19.8 MB)
**변경:** '통합 정책 경로 추종 ②' 뒤에 ① 명령 투어(영상 + 세그먼트별 불건강 표 + 오버레이 읽는 법), ② 전환 클로즈업(성공 forward→diag_fr / 실패 backward→diag_bl 영상 + 진폭 관찰·해석), ③ 경로 추종 오버레이(영상 3 + 전문가/S1 final/S3 final 비교표) 추가. 흐름 요약(슬라이드 2)의 8단계 문구를 S3 final 결과로 갱신. validate(--original) 통과, 렌더 QA(제목 길이 축약).

---

## 2026-09-10 — 통합(단일) 정책 계보 정책 폴더 정리

**커밋:** (미커밋)
**요청:** 이번에 학습한 단일 정책을 정책 폴더에 정리하되, 기존 분리(전문가) 정책과 섞이지 않게.
**파일/이동:** `runs/ppo_unified_transition_stage{1,2,3}/…` → `policies/unified/01_transition_stage1/`, `02_transition_stage2/`, `03_transition_stage3/` (run 폴더 전체 + 콘솔 로그·pid 포함, 전문가 정리 규약과 동일). 옛 앵커 종료 규칙의 중단 run → `policies/unified/old/01a_transition_stage1_aborted_anchor_terminate/`, 증류 중간본 2개 → `old/`. 빈 `runs/ppo_unified_*` 제거. 삭제된 데이터 없음.
**변경:** Stage 2·3 YAML resume 경로를 새 위치로 갱신. 원장 `policies/unified/TRAINING_HISTORY.txt`에 전문가 계보와의 분리 경고(정규화 통계·환경 상이, 혼용 금지) 헤더, "현재 권고 = 03_transition_stage3 final(벤치마크 근거), 차선 = 02 final, best는 대표로 쓰지 않음" 확정, 폴더 구성 절 추가. 로드 검증: 00/01/02/03의 final(+02·03 best) 모델·정규화 쌍 모두 정상(누적 스텝 40.0M/80.0M/120.0M, obs_rms count 일치).

---

## 2026-09-10 — 전문가 이어 학습 파이프라인: 인계 시작(moving-state init) 환경·상태 은행·평가

**커밋:** (미커밋)
**요청:** 전문가 정책을 더 학습시키되, 시작을 정지 상태가 아니라 "다른 정책이 움직이던 상태에서 전환된 시점"으로 하고(사용자 제안), 주행 성능 퇴화를 막기 위해 전환/비전환 에피소드를 섞고, 은행 규모를 키우며(3천→2만/출발), 반복(iteration)으로 점진 개선. 파일럿 3개(diag_fr·diag_bl·forward) 먼저.
**파일:** `horcrux_env/envs/plane_moving_init_v1.py`(신규, `plane-moving-init-v0` 등록), `training/build_moving_state_bank.py`(신규), `training/eval_expert_transitions.py`(신규), `training/callbacks/info_metrics.py`(`env_init/*`), `training/configs/ppo_plane_{diag_fr,diag_bl,forward}_moving_init_iter1.yaml`(신규)
**변경:** (1) `PlaneMovingInitWorld(PlaneJoyDirWorld)`: plane-v0 보상·종료·관측 불변, reset만 두 분포 혼합 — 정지 시작(1−p) / 인계 시작(p): 은행 상태(qpos·qvel) 복원 후 이 전문가 gait로 전환, 위상은 align_prob로 위상 정렬(역재생 k=−col) 또는 무작위; 인계 에피소드는 moving_episode_horizon(1000)에서 절단. info `moving_init/source_cmd/init_aligned`. (2) 은행 생성: 전문가 10명 결정론+노이즈 롤아웃(사전 주행 100~800, 매 스텝 저장) + 2차 상태(다른 출발에서 인계 후 굴린 상태) + 통합 정책(S3 final) 무작위 전환 롤아웃 10% + 이전 은행 30% 재사용 옵션; 건강 상태만, xy 원점 이동, 메타데이터 json. (3) 평가: 정지 시작 정상 주행(속도·리턴·낙상) + 출발 10 × 목표 진입 100스텝 내 실패율 행렬(은행 상태·align 전환, 학습 규약 동일) + `--override`로 새 체크포인트 비교. (4) 파일럿 YAML: stage3 final 재개, 인계 50% / align 80% / 절단 1000, lr 1e-4·ep 2·target_kl 0.04, γ 0.95(불변), 28.4M. 스모크: env(인계 비율 0.53, 절단 정상, NaN 없음), train.py 4k 스텝 + `env_init/*` TB 기록, 평가 스크립트 정상. 기존 diag_fr 전문가는 스모크 은행 인계 시작 31% 낙상(정지 0%) — 학습 신호 확인. 참고: 은행 생성 시 회전 출발(cw/ccw)을 plane-moving-init-v0에서 굴리면 부모 보상의 0-나눗셈 RuntimeWarning이 뜨나 상태 수집에는 무관(보상 미사용).

---

## 2026-09-10 — 학습 녹화 콜백 카메라: CoM 추적 + 광각 (프레임 이탈 수정)

**커밋:** (미커밋)
**요청:** 학습 렌더링에서 로봇이 빠르게 움직여 잠깐 보이다 프레임 밖으로 벗어남 → 렌더 카메라 수정.
**파일:** `training/callbacks/video_recorder.py`, `training/train.py`
**변경:** `VideoRecorderCallback`에 `track_com=True`, `cam_fovy=80.0` 옵션 — 녹화 env의 'ceiling' 카메라 fovy를 넓히고 매 스텝 전 `cam_pos[:2]`를 로봇 CoM으로 이동(데모 파이프라인과 동일 방식). 카메라/CoM API가 없는 env는 자동으로 고정 카메라 유지. train.py `video:` 섹션에 `track_com`, `cam_fovy` 키 연결(기본 켜짐). 스모크(300스텝 전진 주행 녹화)에서 로봇이 첫/마지막 프레임 모두 화면 중앙에 유지됨을 확인. 진행 중인 파일럿 3개는 모듈을 이미 로드한 상태라 영향 없음(남은 클립은 고정 카메라), 다음 학습부터 적용.

---

## 2026-09-10 — 인계 시작 파일럿(iteration 1) 결과: 주행 유지, 진입 실패는 미개선 → 원인 진단

**커밋:** (미커밋)
**요청:** 파일럿 후 보충·수정할 것 확인.
**파일:** `training/path_following.py`(`--expert-override name=model:vecnorm`, `--tag-suffix` 추가 — 전문가 교체 데모용), 원장 3개·캠페인 원장 갱신
**결과:** 3개 병렬 28.4M(13:39~21:10). 학습 중 정지 시작 리턴 유지(174K/180K/221K), 인계 시작 리턴 상승(15.7→19.1K / 9.4→17.3K / 18.0→27.6K), KL 셋 다 포화(0.035~0.045). 결정론 평가(기준선과 같은 은행·시드): 정지 주행 유지(diag_bl 0.492→0.497 m/s, forward 0.617→0.620), 그러나 진입 후 실패율 final 0.311→0.361 / 0.328→0.328 / 0.167→0.144, best 0.256 / 0.344 / 0.133 — 잡음 범위, 목표(절반 이하) 미달.
**진단:** (1) 낙상이 사실상 무료 — 선형 명령 unhealthy_cost_weight=2, γ=0.95(유효 지평 20스텝)라 "전환 직후 20스텝 저진폭 버티기"(diag_fr는 left 출발 낙상 .60→.00으로 회피 가능)와 "바로 달리다 넘어지기"의 기대 이득이 비슷해 학습 기울기가 없음. 인계 리턴 상승은 살아남은 뒤 주행 개선분. (2) diag_bl(역재생 δ=203) 진입은 저진폭으로도 안 됨(hold20 무효/악화) — 가족 간 전환의 정렬 시작 위상 자체 문제. 처방 후보: iteration 2 = 인계 env 전용 `unhealthy_cost_weight` 상향(200) + lr 5e-5, diag_bl류는 정렬 규칙 개선(상태 인식) 별도 과제.

---

## 2026-09-10 — 발견: plane_v3 종료 스텝 낙상 페널티 미적용 결함 → 인계 env에서 보정, iteration 2 착수

**커밋:** (미커밋)
**요청:** iteration 2(낙상 페널티 200 + lr 5e-5) 착수 승인 → 스모크에서 결함 발견.
**파일:** `horcrux_env/envs/plane_moving_init_v1.py`(step 보정), `training/configs/ppo_plane_{diag_fr,diag_bl,forward}_moving_init_iter2.yaml`(신규)
**발견:** plane_v3는 `is_terminated`를 스텝당 두 번 호출(`_get_rew`, `step`)해 보상 계산 시점엔 카운터가 한 스텝 뒤라 종료 스텝의 `cost_unhealthy`가 항상 0 — **방위 전문가 계보는 낙상 페널티(2)를 한 번도 받은 적이 없음**(종료 타이밍도 unhealthy_max_steps의 절반인 ~15스텝). plane_v3는 frozen이므로 `PlaneMovingInitWorld.step`에서 종료 스텝에 `unhealthy_cost_weight`를 1회 보정해 싣는다(타이밍 불변). 스모크: 무작위 행동 낙상 시 cost_unhealthy −200(기본 2 설정은 −2) 확인.
**iteration 2:** iteration 1 final 재개, `unhealthy_cost_weight 200`, lr 5e-5, 나머지 동일(같은 은행, 인계 50%·align 80%·절단 1000, 28.4M). 3개 병렬 착수, CoM 추적 카메라 녹화 적용.

---

## 2026-09-11 — 인계 시작 iteration 2 결과 기록 / 연구 덱 전체를 쉬운 문장으로 재작성 (40장)

**커밋:** (미커밋)
**요청:** iteration 2 완료 보고. 그동안 수정한 내용을 잊지 않도록 슬라이드로 정리하고, 슬라이드 문장을 소리 내어 읽기 쉬운 쉬운 문장으로 덱 전체를 다시 쓰기(이후 답변도 같은 방식).
**파일:** `policies/path_tracking/{diag_forward_right,diag_backward_left,forward}/TRAINING_HISTORY.txt`(iteration 2 `[완료]` 결과), `policies/path_tracking/MOVING_INIT_CAMPAIGN.txt`(결과·판정·iteration 3 후보), `docs/Horcrux_transition_research_2026-09_template.pptx`(40장 쉬운 문장판; 빌드 스크립트는 세션 scratchpad `deck/build_deck_plain.py`), 평가 `runs/moving_state_bank/eval_iter2_{final,best}.json`
**결과:** 3개 병렬 28.4M(09-10 21:42 ~ 09-11 05:13). 벌점 200 실제 적용 확인(cost_unhealthy 평균 −0.006~−0.010/스텝). 정지 주행 유지(diag_fr 0.470, diag_bl 0.497, forward 0.626 m/s). 학습 중 인계 실패율은 diag_bl 0.38→0.22, forward 0.23→0.14로 줄었으나 고정 상태 결정론 평가는 diag_fr 0.311→0.361(iter1)→0.361 / best 0.333, diag_bl 0.328→0.328→0.289 / 0.289, forward 0.167→0.144→0.178 / 0.183 — 목표(절반) 미달, 잡음 범위. 결정론 vs 확률적 진단(9출발×10상태): 차이 ≤0.05로 "평균 행동 경계선" 가설 기각. KL 셋 다 포화(0.045~0.049), std 감소.
**변경(덱):** 33장 → 40장. Part 3 "전문가를 움직이는 상태에서 다시 학습하기"(왜 시작했나 / 새로 만든 것 / 첫 파일럿 / 찾아낸 결함과 수정 / 두 번째 파일럿 / 바뀐 파일 목록) 추가. 모든 문장을 한 문장 한 내용의 구어체로 바꾸고 기호(→ · /)를 말로 풀었으며, 제목을 줄여 아이콘 겹침을 없앴다. validate 통과, LibreOffice 렌더로 40장 육안 검토.
**다음(사용자 결정 대기):** iteration 3 후보 — (a) 탐색 폭 확대(log_std/ent_coef), (b) 인계 직후 20스텝 저진폭·생존 보상(인계 env 한정, 전문가 보상 의미 불변), (c) 가족 간 진입의 상태 인식 시작 위상 규칙. 8개 전문가 확장은 파일럿에서 실제 감소를 확인한 뒤.

---

## 2026-09-11 — 전환 위상 선택의 수학적 근거 덱 + 규칙 비교 실험(학습 없음) + 참고문헌 9절

**커밋:** (미커밋)
**요청:** iteration 3 후보 (c) "가족 간 진입의 상태 인식 시작 위상"의 수학적 근거를 논문에 쓸 수 있게 슬라이드로 정리하고, 필요하면 그림 자료도 찾아 넣기. 그림은 저장소에 없어 실제 데이터로 직접 만들고, 원리를 확인하는 작은 실험(학습 없이 평가만)을 승인받아 함께 수행.
**파일:** `training/eval_phase_rules.py`(신규: 규칙 k0/sign/near/kin/signmom/all 비교, 궤도 표, 거리·낙상 기록), `docs/figures/phase_selection/F1~F9*.png`(신규), `docs/Horcrux_phase_selection_math_2026-09.pptx`(신규 19장), `docs/deck_src/`(신규: 덱 빌드 스크립트 보관 `build_deck*.py`, `make_phase_figures.py`, `README.md`, `curves.json`, `bench_ckpts.json`), `docs/references_transition_learning.md`(9절 6편 추가 + 대응표 행 + 검증 메모), 결과 `runs/moving_state_bank/eval_phase_rules{,_signmom,_all}.json`
**코드로 확인한 사실:** 모션 벡터 = 기준 관절각의 2차 시간 미분 부호(`gait_v2.py` 135행) = 사인파이므로 −sign(기준각); 관절은 토크 모터(`horcrux_p.xml`)라 토크 = 정책 크기 × 부호. 8방위 gait는 시간 파라미터(40,40)가 같아 δ+180은 가로 관절 기준 신호를 정확히 반전 → 세로·가로를 동시에 맞추는 위상이 없음(가족 간 부호 일치 상한 14 중 4.8~7.7, F3).
**실험(8 목표 × 9 출발 × 20 상태, 대표 전문가, post 150):** 평균 진입 실패 — 부호 정렬(현행) 0.231, 위상 0 재시작 0.281, 관절 공간 최근접점(분산 정규화) 0.290, 운동 에너지 계량 0.267, 부호 정렬+운동량 동점 처리 0.242. 거리 J(선택 위상→목표 궤도)와 실패의 상관 0.02(최근접 10%만 0.13, 나머지 평평). 후보 위상 전부 시도(10 상태/출발, 8 목표): 어떤 위상도 안 되는 상태 0~2%, 살아남는 칸 60~77%, 실패 칸이 이웃 위상끼리 뭉침(행당 덩어리 1.3~1.6개 vs 무작위 1.8~2.3개) → 상태별 안전 위상 창이 존재하나 위치가 상태마다 달라 고정 위상(최선 0.17~0.24)이나 단순 계량으로는 못 찾음.
**판정:** "목표 궤도 최근접점" 원리는 계량 선택에 달렸고, 관절 공간 유클리드 거리는 그 계량이 아님(토크 방향 연속성 = 해밍 계량이 더 잘 가름). 부정적 결과를 덱에 그대로 기록. 다음 후보: 전부 시도 기록(7,290개)으로 상태·위상 → 생존 분류기 학습(교차 검증으로 부호 정렬과 비교), 규칙을 path_following/unified set_gait에 옵션으로 꽂기, 인계 시작 학습과 결합.

---

## 2026-09-11 — 인계 시작 iteration 3: 기울기 조건 보상 항 2개(인계 env 한정) + 원본에서 재학습 착수

**커밋:** (미커밋)
**요청:** 인계 시작 학습을 더 시켜 보되, 원본 정책에서 시작하고 보상 가중치 변경 또는 추가 항을 고려. 계획(항 2개, 인계 에피소드 한정, 원본 재개, 3개 병렬 28.4M) 승인 후 착수.
**파일:** `horcrux_env/envs/plane_moving_init_v1.py`(kwargs `tilt_cost_weight`, `push_tilt_cost_weight`, `tilt_deadzone_deg`, `tilt_ref_deg`; 기본 0 → 기존 동작 불변; info `cost_tilt`, `cost_push_tilt`), `training/callbacks/info_metrics.py`(두 키 로깅), `training/configs/ppo_plane_{diag_fr,diag_bl,forward}_moving_init_iter3.yaml`(신규), `training/eval_phase_rules.py`(규칙 `lat` 추가: 가로 부호 일치 우선·세로 동점 처리), 원장 3개·캠페인 원장
**변경:** 인계 시작 에피소드에서만 매 스텝 cost_tilt = −w·clip((|roll|−15°)/30°, 0, 2), cost_push_tilt = −w·clip(·, 0, 1)·(평균 진폭/최대 진폭), w = 20/20. roll은 `_cur_euler_ypr[2]`(도). 정지 시작 에피소드, plane-v0, 원본 정책은 불변. 스모크: 무작위 행동에서 roll>15° ↔ cost_tilt<0 일치, 정지 시작에서 항상 0, 기본 가중치에서 키 존재·값 0 확인.
**착수:** 17:05, 3개 병렬(fps ≈ 1,255), 원본 stage 3 final 재개, lr 1e-4, 벌점 200, 28.4M(≈6.3h, 완료 ≈ 23:20).
**병행 사전 평가(학습 없음, 17:15 완료):** 시작 위상 규칙 `lat`(가로 부호 일치 우선, 세로 동점 처리)를 대표 전문가 8개 × 같은 1,440 상태로 평가 — 진입 실패 평균 0.231 → 0.158, 8 목표 모두 감소, 집안 간 0.340 → 0.223, 같은 집안 0.037 → 0.042(불변). 코드 변경 없이 규칙만 바꾼 결과. 환경(`set_gait`/인계 env/path_following) 옵션화는 미실시(승인 대기).

---

## 2026-09-12 — 인계 시작 iteration 3 결과: 촘촘한 기울기 벌점도 진입 실패 미개선(forward만 소폭), 시작 위상 규칙이 더 큰 지렛대

**커밋:** (미커밋)
**요청:** iteration 3 완료 보고(자동 진행 루프의 단계 보고).
**파일:** 원장 3개(`[완료]` 결과), `policies/path_tracking/MOVING_INIT_CAMPAIGN.txt`(결과·판정·iteration 4 후보), 평가 `runs/moving_state_bank/eval_iter3_{final,best}.json`, `eval_phase_rules_iter3_final.json`
**결과:** 3개 병렬 28.4M(09-11 17:05 ~ 09-12 00:45). 결정론 진입 실패(기준 → final / best): diag_fr 0.311 → 0.322 / 0.328, diag_bl 0.328 → 0.350 / 0.417, forward 0.167 → 0.117 / 0.172. 정지 주행 속도 유지(97% 기준 충족), 리턴 2~4% 하락. 학습 중 cost_tilt·cost_push_tilt 크기가 끝까지 불변 → 정책이 벌점 회피 행동을 찾지 못함. 성공 기준 미달.
**규칙 비교:** iter3 final을 같은 20상태에서 시작 위상 규칙만 바꿔 평가 — 부호 정렬 0.428/0.272/0.172 → 가로 먼저 0.233/0.211/0.089(원본 전문가 0.378/0.317/0.200 → 0.261/0.161/0.144). 학습보다 규칙의 효과가 큼.
**다음(승인 대기):** iteration 4 = 원본 stage 3 재개 + 인계 env 시작 위상 규칙 '가로 먼저'(align_rule 옵션 신설, 기본값은 현행 유지) + 벌점 200, 새 항 제거. 규칙 옵션은 통합 env `set_gait`·`path_following`에도 동일 추가.

---

## 2026-09-12 — 전환 시작 위상 규칙 공유 모듈(phase_align.py) + align_rule 옵션 3곳 + 인계 시작 iteration 4 착수

**커밋:** (미커밋)
**요청:** 네 번째 파일럿 진행 — 시작 위상 규칙 '가로 먼저'를 환경 옵션으로 넣고(기본값은 현행), 원본 전문가에서 인계 시작 학습(벌점 항 2개 제거, 낙상 벌점 200 유지).
**파일:** `horcrux_env/envs/phase_align.py`(신규: `align_column(M, mvec, rule)`, `start_k(gait, mvec, rule)`; rule `sign`=현행 argmax 첫 열, `lat`=가로(짝수) 부호 일치 우선·세로(홀수) 동점 처리·동점 중 행렬 중앙 열), `horcrux_env/envs/plane_moving_init_v1.py`(kwarg `align_rule`, 기본 `sign`), `horcrux_env/envs/plane_unified_v1.py`(kwarg `align_rule`, `set_gait`가 공유 함수 사용), `training/path_following.py`(`--align-rule`, env kwarg 전달, result.txt에 규칙 표기), `training/eval_phase_rules.py`(sign/lat를 공유 함수로), `training/configs/ppo_plane_{diag_fr,diag_bl,forward}_moving_init_iter4.yaml`(신규), 원장 3개·캠페인 원장
**변경 근거:** `lat`의 동점 열을 행렬 한가운데(≈1,570)에서 고르는 이유 — 첫 열/끝 열을 고르면 역재생/순재생에서 몇 스텝 안에 열 번호가 감겨(3139 → 0) 표본 위상이 약 0.3 rad 튀는 불연속이 생김. `sign`은 재현성을 위해 현행(첫 열) 그대로 둠(역재생 목표에서는 기존에도 이 불연속이 있었음 — 기록만 남김).
**검증:** sign 열 번호가 옛 코드와 1,000개 무작위 벡터에서 일치; lat가 09-11 평가 기록과 같은 부호 패턴(111/111 표본); 인계 env 기본값이 옛 동작과 같은 k; lat env의 모션 벡터가 getMvec(k)와 일치; 통합 env `set_command(align_phase=True)`가 두 규칙 모두 start_k와 일치; 잘못된 규칙 이름 거부; diag_bl(역재생) lat env 1000스텝 동안 열 감김 0회.
**착수:** 11:20, 3개 병렬(fps ≈ 1,310), 원본 stage 3 final 재개, 인계 50% / align 80%(lat) / 무작위 20%, 벌점 200, lr 1e-4, 28.4M(≈8h, 완료 ≈ 19:15). 성공 기준은 lat 규칙 평가로 diag_fr ≤0.15, diag_bl ≤0.10, forward ≤0.08(출발선 0.261/0.161/0.144), 주행 ≥97%.

---

## 2026-09-12 — 인계 시작 iteration 4 결과: 주행 완전 유지, lat 규칙 아래 진입 실패는 diag_bl·forward만 소폭 개선

**커밋:** (미커밋)
**요청:** iteration 4 완료 보고(자동 진행 루프의 단계 보고).
**파일:** 원장 3개(`[완료]` 결과), `policies/path_tracking/MOVING_INIT_CAMPAIGN.txt`(결과·판정·권고), 평가 `runs/moving_state_bank/eval_iter4_final.json`, `eval_phase_rules_iter4_{final,best}.json`
**결과:** 3개 병렬 28.4M(11:20 ~ 18:55). 정지 주행 속도·리턴 모두 기준 이상(0.472/0.492/0.623 m/s). lat 규칙 진입 실패(출발선 원본 0.261/0.161/0.144): final 0.272/0.122/0.133, best 0.317/0.172/0.094 — diag_bl −24%, forward −8%(best −35%), diag_fr 불변. sign 규칙 표준 평가 0.306/0.361/0.200(기준 0.311/0.328/0.167). 성공 기준 미달.
**판정:** 네 번의 인계 시작 파일럿(벌점·학습률·촘촘한 벌점·시작 위상 규칙)에서 학습 자체의 이득은 작고, 시작 위상 규칙(`lat`, 학습 없음)이 가장 큰 이득. 남은 실패는 회전 출발(ccw/cw)과 diag_fr의 forward/left 출발. 전문가 인계 학습은 여기서 멈추고 규칙을 경로 추종·통합 정책에 적용하는 것을 권고(사용자 결정 대기). runs 정리(04_~07_)도 승인 대기.

---

## 2026-09-12 — 경로 추종 시연 옵션(--align-all, --seed, --no-video) + 규칙·정책 조합 렌더링 108회 + 연구 덱 45장으로 확장

**커밋:** (미커밋)
**요청:** 지금까지의 학습을 정리하던 덱에 세 번째·네 번째 파일럿과 시작 위상 규칙을 이어서 정리하고, 학습한 정책으로 경로 추종 렌더링을 진행. 계획(조합 A~D + 합친 정책 2종, 경로 3개) 승인 후 착수.
**파일:** `training/path_following.py`(`--align-all`: 모든 전환에 정렬 규칙 적용·크로스페이드는 위험 쌍만, `--seed`, `--no-video`; result.txt에 규칙 표기), `docs/Horcrux_transition_research_2026-09_template.pptx`(40장 → 45장: 이어 학습 ⑦~⑩, 경로 추종에서 확인하기; 연구 흐름·다음 단계·결과물 위치·부록 갱신), `docs/deck_src/build_deck_plain.py`(갱신본), `runs/path_follow_demo/20260912-22*`(시드 42 영상판 18개 + 시드 1~5 무영상 90개)
**결과(6회 평균 오차 m, 경로 네모/별/장애물):** 원본+지금 규칙 0.35/0.35/0.64(완주 17/18) · 원본+새 규칙 위험쌍만 0.37/0.46/0.58(17/18) · 원본+새 규칙 전부 0.36/0.57/0.31(18/18) · iter4 전문가+새 규칙 전부 0.42/0.39/0.48(18/18) · 합친 정책 S3+지금 규칙 0.38/0.34/0.25 · 합친 정책+새 규칙 0.36/0.33/0.42.
**정정(2026-09-13, 비판적 검토 에이전트 확인):** 위 "6회 평균"은 반복 실험이 아니었다. (1) plane_v3 reset 잡음이 0(721~725행, `reset_noise_scale`은 저장만 되는 죽은 인자)이라 시드는 몸 상태를 바꾸지 않고 reset이 추첨하는 명령만 바꾼다. (2) path_following.py는 `set_command(forward)` 뒤 지역변수 `raw_obs`에 낡은 reset 관측을 남겨(333행) 첫 행동을 그 관측으로 계산하며, 같은 낡은 관측이 안전 쌍 즉시 전환(390행)과 크로스페이드 첫 스텝(385행)에도 있다. 전문가는 joy 정규화 표준편차가 1e-4라 다른 joy가 들어오면 ±10으로 포화되므로 이 한 스텝의 영향이 크다. (3) 별·장애물에서 C/D/합친 정책은 첫 전환 때 관측을 재생성해 낡은 관측을 버리므로 6회가 동일한 1회 실행이고, A/B와 네모의 편차는 첫 스텝 포화 입력 하나에 대한 민감도다. 따라서 위 판정("새 규칙 전부 완주·장애물 절반", "별 악화", "합친 정책 최선", "iter4 이득 없음", "새 규칙 4단계 학습 필요")은 모두 철회한다. 유지되는 것: 이 시연은 첫 행동 하나에 결과가 크게 갈릴 만큼 민감하다; 장애물에서 합친 정책 1회(0.25 m)와 새 규칙 전부 1회(0.31 m)가 지금 규칙 6회(0.35~1.17) 전부보다 좋았다(유망 수준). 재실행 조건: 낡은 관측 3곳 수정 + 시작 상태를 실제로 바꾸는 반복(잡음 복원 또는 은행 상태 시작) + 짝지은 비교, 표에 완주·완주 실행 오차·시간·전환·편차 병기.

---

## 2026-09-13 — 비판적 검토 결과 기록: 학습·평가는 시연 결함과 무관, 정지 주행 값은 1회 측정, best 체크포인트 선택은 평가 추첨의 산물

**커밋:** (미커밋)
**요청:** 사용자 지시("비판적 검토 에이전트의 피드백을 받은 뒤 답할 것") 이후 "학습을 다시 해야 하는가"를 검토. 코드 변경 없음, 기록만.
**검토로 확인된 사실:** (1) `train.py`·`plane_moving_init_v1.reset_model`(set_state→start_k→`_get_obs`)·`plane_unified_v1`(전환 뒤 `_get_obs` 재생성, `step`이 새 관측 반환)·`eval_expert_transitions.py`·`eval_phase_rules.py`(reset→set_state→`_k`→`_get_obs`)에는 낡은 관측 문제가 없다(진입 행렬 reset 180회 실측: 관측 끝 17개가 목표 gait mvec·joy와 일치). (2) 진입 행렬은 출발당 서로 다른 은행 상태 20개(backward만 19/20)로 잰 실제 반복이며, 규칙 효과(sign 0.2306 → lat 0.1576, 같은 1,440 시도에서 고침 191 / 망침 86, McNemar χ² 39.8)는 유효하고 파일럿 효과(원본→iter4 final: lat 0.189→0.176 고침 43/망침 36 χ² 0.62; sign 0.298→0.280 χ² 1.19)는 유의하지 않다. 목표당 180회 표본의 95% 반폭은 ±0.05~0.07. 평가 은행이 학습 은행과 같은 파일(bank_iter1.npz)이라 파일럿에 불리한 조건도 아니었다. (3) reset 잡음 0이라 별도 평가의 정지 주행 5 에피소드와 학습 중 EvalCallback의 정지 에피소드는 동일 실행(시드 0/1로 1000스텝 궤적이 자릿수까지 일치) → `rest.speed/ret/fall_rate`는 1회 값. 학습 중 `eval/mean_reward`는 10 에피소드 중 정지 에피소드 개수(2~8, 추첨)와 상관 0.99이며, iter4 세 run 모두 best_model이 정지 8개가 뽑힌 57번째 평가(99.7M)에서 저장됨 → **best 체크포인트 우열은 근거 없음, final + 짝지은 비교로만 판단**. (4) 파일럿 설계의 신호 비중: 인계 시작 에피소드는 1000스텝 절단이라 스텝 기준 전체 표본의 10.4~11.9%뿐(iter4 monitor 집계). (5) 부수: 부모 plane_v3 `reset_model`은 `_motion_vector`를 갱신하지 않아 원본 전문가 env의 첫 스텝 제어에 이전 에피소드 mvec가 곱해짐(6000스텝 중 1스텝, 영향 미미; 인계·통합 env는 이미 보정). 설정의 `reset_noise_scale: 0.1`은 쓰이지 않는 죽은 인자.
**판정:** 시연 결함을 이유로 학습을 다시 할 필요는 없다. 다만 "학습이 필요 없다"고 말할 근거도 없다 — 네 파일럿은 인계 표본 비중 10~12%의 설계였고 best 선택이 무의미했으므로 학습 효과를 제대로 시험한 것이 아니다. 순서: 시연 재실행(낡은 관측 3곳 수정 + 실제 반복 조건) → 그 결과를 본 뒤 인계 비중을 높인 재학습이나 합친 정책 새 규칙 학습 여부 결정.

---

## 2026-09-13 — 경로 추종 시연 결함 3곳 수정 + 반복 조건 옵션 + 재실험 v2(6조합 × 3경로 × 10반복, 짝지은 비교) + 비판적 검토 반영

**커밋:** (미커밋)
**요청:** "계획한 대로 시행" — 어제 무효로 판정된 경로 추종 비교를 결함을 고친 뒤 실제 반복 조건으로 다시 하고, 검토 에이전트의 피드백을 받아 보고.
**파일:** `training/path_following.py`(① 시작 `set_command` 뒤 `current_observation()`으로 관측 재생성, ② 안전 쌍 즉시 전환 뒤 관측 재생성, ③ 크로스페이드 첫 스텝 전 관측 재생성; `--start-noise`(관절 각도 잡음, rad), `--path-rotate-deg`(경로 회전, 도) — 시드로 정한 난수라 같은 시드면 모든 조합이 같은 조건; result.txt에 `[반복 조건]` 줄), `runs/path_follow_demo/2026091*_v2_*`(180 + 영상 3), `runs/path_follow_demo/v2_summary.json`, 분석 `scratchpad/v2_analysis.py`, 덱 슬라이드 갱신
**조건:** 잡음 ±0.03 rad, 회전 ±8°(실제 표본 −3.1~+7.7°, 10개 중 8개 양수), 시드 1~10, 최대 6000스텝, 영상 없음. 조합 A(원본·sign) B(원본·lat 위험3쌍만) C(원본·lat 전부) D(iter4 final 3개 교체·lat 전부) U_sign(합친 S3·sign) U_lat(합친 S3·lat).
**결과(완주/오차 평균±sd m/시간):** A 10/10 .40±.18 61s | 10/10 .52±.21 116s | 9/10 .56±.18 144s · B .39/.54/.52 · C .59±.29 66s | .44±.13 77s | .37±.11 86s · D .55/.41/.44 · U_sign .42±.11 47s | .38±.06 101s | .34±.11 78s · U_lat .29±.09 31s | .32±.11 71s | .30±.10 65s.
**짝지은 비교(오차 이김/비김/짐, 부호검정 p):** C vs A 네모 3/0/7, 별 5/0/5, 장애물 9/0/1 p=.02 (합산 17/13, 이득 없음) · B vs A 전부 차이 없음(위험 3쌍이 모두 같은 집안이라 설계상 예상) · D vs C 7/3, 5/5, 5/5 (차이 못 찾음) · U_lat vs U_sign 10/0 p=.002, 8/2, 6/4 · U_lat vs C 합산 23/7 p=.005 · U_lat vs A 합산 24/6 p=.001 · U_lat는 다른 다섯 조합과 30쌍 비교에서 모두 이김(22/8~24/6), 시드·경로별 1등 16/30.
**검토 반영(수정된 표현):** "합친 정책 + lat"가 오차·시간 최선. 규칙만의 이득은 U_sign 대비 0.08 m, 전문가 대비 우위 0.19 m에는 합친 정책 학습이 포함. 다중 비교 보정을 넘는 결과는 U_lat 네모 10/0 하나. 오차·시간·전환 횟수는 상관 0.6~0.97의 한 현상. U_sign vs A는 전환 처리(합친: 전부 정렬·크로스페이드 없음 / 전문가: 안전 쌍 k=0)가 달라 정책만의 비교가 아님 → 정책 비교는 U_lat vs C. 회전각 표본 치우침, 별 경로는 회전 +4.5° 이상 6시드에서 마지막 명령이 달라짐, 명령 로그 미저장, lat 규칙은 '가로 우선'과 '가운데 열(감김 회피)' 두 변화가 동시. 사후 규칙("장애물 같은 경로에만 lat 전부")과 "4단계 학습하면 좋아질 가능성"은 근거 없음으로 제외.
**부수:** 결함 수정 뒤 네모 기준선이 0.193 m/20 s → 0.181 m/17.5 s(시드 1)로, 낡은 관측이 기준선을 깎고 있었음. `runs/path_follow_demo/20260913-0925*_square_smoke_s{1,2}`는 스모크 테스트 산출물.

---

## 2026-09-13 — 경로 추종 커맨더 실험: 갱신 주기(25/10/5) × 도착 판정(원/수직면), 놓침·되돌아감 지표, 궤적 npz 저장

**커밋:** (미커밋)
**요청:** 사용자 지적 "갱신 주기가 너무 길어 오버슛이 난다" → 검토 에이전트 확인(한 주기 이동 0.57~0.86 m > 판정 원 지름 0.7 m; 교정·도착 사각 구간 0.35~0.475 m; 근접 동결이 앞뒤 미구분) 후 계획 승인.
**파일:** `training/path_following.py` — `WaypointCommander(plane_capture, start)`(웨이포인트 수직면 통과 시 도착, 기본 꺼짐), `run()` 인자·CLI `--control-period`(기본 25), `--capture-radius`(0.35), `--plane-capture`; 도착 사건 기록; 결과에 `[커맨더]`·`[놓침]` 줄(웨이포인트별 궤적 최근접 거리, 판정 원 밖 통과 수, 되돌아간 전환 수 = 명령 방향 내적 < 0인 전환); `trajectory.npz`(traj, cmd, waypoints, start, capture_*, wp_min_dist) 저장. 기본값은 예전 동작과 동일(스모크: v2 U_lat square r1과 0.281 m/425스텝 일치). 분석 `scratchpad/v3_analysis.py`, 요약 `runs/path_follow_demo/v3_summary.json`, 결과 `runs/path_follow_demo/2026091*_v3_*`(180 + 영상 2).
**조건:** 합친 정책 S3 + lat 고정, 경로 3 × 시드 10(잡음 0.03 rad, 회전 ±8°), 변형 6(P25/P10/P5 × 원/수직면).
**결과(평균 오차 m / 최대 오차 m / 시간, 네모·별·장애물):** P25 원(기준) .29/1.00/31s · .32/1.29/71s · .30/1.12/65s | P25 수직면 .23/.64/24s · .25/.93/56s · .24/.67/51s | P10 원 .20/.59/33s · .26/1.04/61s · .25/.96/62s | P10 수직면 .18/.50/27s · .19/.77/56s · .18/.48/44s | P5 원 .20/.65/25s · .25/1.02/60s · .16/.58/42s | P5 수직면 .17/.50/23s · .21/.79/51s · .16/.54/42s. 완주 전부 30/30. 기준 대비 짝지은 평균 오차(합산 30쌍): P25 수직면 19/8/3 p=.001, P10 원 20/1/9 p=.06, P10 수직면 25/0/5 p<.001, P5 원 26/0/4 p<.001, P5 수직면 27/0/3 p<.001. 되돌아간 전환(네모 합): 19 → 3(수직면). 전환 횟수는 주기를 줄여도 크게 늘지 않음(네모 7→7~10).
**판정(비판적 검토 확인, 재계산 일치):** 기준 커맨더의 큰 오차·긴 시간은 대부분 "틱 사이에 판정 원을 지나쳐 놓친 뒤(궤적은 원 안을 지났으나 틱에서 못 잡음: P25 24/150, P10 4/150, P5 1/150; 평균 속도 0.43 m/s × 1.25 s = 0.54 m > 원 지름 0.7 m의 상당 부분), 근접 동결 0.85 m를 벗어나서야 되돌아오는" 한 기제에서 나옴(기준 최대 오차 30개 중 23개). 주기 단축은 표본 놓침을 줄이고, 수직면 판정은 놓쳤을 때 되돌아가지 않게 하는 안전망(원을 놓쳤을 때만 발동: P25 50/150, P10 27/150, P5 22/150). 구간 중간 되돌아감(경로 꺾임의 구조적 몫 제외): 네모 18→2, 별 41→4, 장애물 36→1(P25 원→P25 수직면). P5 수직면 vs P10 수직면은 모든 지표에서 차이 없음(16/2/12, 14/3/13, 14/2/14, 10/5/15) → 계산이 덜한 **P10 + 수직면**을 기본값 후보로 제안(채터링 근거는 없음 — P10에서 전환 +20~35%, 1초 내 재전환 신설되나 오차 무해; 히스테리시스 효과는 이 실험으로 판별 불가). 유보: 수직면 완주는 웨이포인트 옆 통과도 인정(발동 시 옆 오차 최대 1.4 m(P25)/0.96 m(P10), 끝점 오차 ≥0.35 m가 10회 중 2~4회); 한 정책·한 규칙에서만 검증; 합산 30쌍은 시드 공유로 비독립(경로별 p .02~.11), 본페로니 뒤 P10 원(p .061)은 탈락; 회전 표본 평균 +3.7°. 미시험: 매 스텝 도착 검사(주기와 분리), 동결 반지름 축소, 수직면 발동에 옆 오차 상한. 기본값 변경은 사용자 결정 대기.

---

## 2026-09-14 — 커맨더 갱신 주기 0.1초(2스텝)·0.05초(1스텝) 추가 실험 (코드 변경 없음, 결과 기록)

**커밋:** (미커밋)
**요청:** "갱신 주기를 0.1초와 같이 짧게 줘봐" — 어제 실험(v3) 조건 그대로 P2 원, P2 수직면, P1 수직면 각 30회 추가. 결과 `runs/path_follow_demo/2026091*_v3_P{2,1}_*`, 요약 `v3_summary.json` 갱신, 비판적 검토 에이전트 재계산 일치.
**결과(평균 오차 / 최대 오차 / 시간 / 전환, 네모·별·장애물):** P2 원 .22/.69/32s/12 · .20/.87/57s/19 · .24/.87/50s/12 | P2 수직면 .21/.61/31s/12 · .18/.72/53s/18 · .20/.54/43s/10 | P1 수직면 .17/.43/26s/11 · .16/.53/50s/19 · .19/.50/42s/11. 완주 전부 30/30.
**짝지은 비교(30쌍):** P1p vs P5p 평균 오차 17/0/13 p=.59, 최대 18/0/12 p=.36, 시간 15/0/15, 전환 +3.0회 | P2p vs P5p 오차 10/0/20 p=.10, 최대 11/0/19, 시간 13/0/17, 전환 +2.9 p=.011 | P1p vs P2p 최대 오차 23/2/5 p=.001 | P2p vs P2c(수직면 효과, 같은 주기) 오차 16/11/3 p=.004, 최대 15/12/3 p=.008, 시간 17/11/2 p=.001.
**판정:** 0.25초 아래로 줄여도 평균 오차·시간은 P5/P10 수직면과 같다(유의 차 없음). 구간 중간 전환만 약 30% 늘어 채터링(1초 내 재전환 65→116, 이웃 명령 왕복 90→150)이 되고, 전환마다 1초간 속도 0.44→0.29 m/s(약 0.2 m 손실)지만 완주 시간 차이는 유의하지 않음. P1 수직면은 큰 실패 꼬리가 가장 얇음(최대 오차 0.8 m 초과 1/30 vs P5 4, P10 6, P2 5). 주기 기제의 오차(지나친 뒤 되돌아옴, 틱 사이 놓침)는 P2·P1 수직면에서 0. 남은 최대 오차(P1 0.25~0.89 m, 중앙 0.47)는 3분의 2가 구간 옆 흐름(이웃 두 명령 왕복 중 증가, 12/19 — 8방향 양자화와 부합하나 yaw 미기록이라 보행 편향과 구분 불가), 3분의 1이 코너 직후 흔들림; 코너 외 20개 중 7개는 근접 동결 구간(0.85 m 안, 설계상 교정 없음)에서 발생. 기본값 선택은 "P10/P5 수직면(전환 적음)" 대 "P1 수직면(큰 실패 최소, 전환 +3회)"의 트레이드오프이며 사용자 결정 대기. 수직면 판정 필요성은 주기와 무관하게 확실. 연속 조향·코너 앞 감속·동결 반지름/히스테리시스 조정은 미실험 후보.

---

## 2026-09-14 — 경로 추종 커맨더 기본값 변경: 갱신 주기 25 → 5스텝(0.25초), 수직면 도착 판정 기본 켬

**커밋:** (미커밋)
**요청:** "0.25초 전환으로 진행하자" (사용자 결정). 후보 두 개(주기 5 또는 10 + 수직면 = 전환 적음 / 매 스텝 + 수직면 = 큰 실패 최소) 가운데 0.25초 선택.
**파일:** `training/path_following.py` — `WaypointCommander(control_period=5, plane_capture=True)`, `run()` 기본값 동일, CLI `--control-period` 기본 5, `--plane-capture` → `BooleanOptionalAction` 기본 True(`--no-plane-capture`로 예전 동작). 예전 동작은 `--control-period 25 --no-plane-capture`.
**근거:** 주기 25/10/5/2/1 × 원/수직면, 합친 정책+lat, 경로 3 × 시드 10 짝지은 비교. 5스텝+수직면: 평균 오차 .29~.32 → .16~.21 m, 최대 오차 1.0~1.3 → .5~.8 m, 30쌍 중 27쌍 개선(p<.001), 완주 30/30; 더 짧은 주기(2, 1)는 평균 오차·시간 이득 없이 구간 중간 전환 +30%.
**검증:** 기본 인자만으로 돌린 square 시드 1(잡음 0.03, 회전 8) 결과가 v3 P5_plane r1과 일치해야 함(아래 실행 로그 확인). `--no-plane-capture` 파싱 확인.
**영향:** 앞으로의 경로 시연·덱 수치는 새 기본값 기준. 기존 결과 폴더(v2: 주기 25·원 판정)와 비교할 때는 `[커맨더]` 줄을 확인할 것. 통합 env·전문가 정책·학습 코드는 무관.

---

## 2026-09-14 — 자율 캠페인 착수 (사용자 약 10시간 부재): 다양한 웨이포인트 검증 + 통합 정책 Stage 4(lat 규칙) + 커맨더 최적화

**커밋:** (미커밋)
**요청:** "다양한 웨이포인트로 성능 검증 → 추가 학습 → 이전 검증 결과와 비교, 부재 중 개선점 도출 및 최적화" (사전 승인된 자율 루프; 단계마다 보고를 기록으로 남김).
**계획:** ① 경로 5종 추가(zigzag, scurve, octagon, lawnmower, random) + 검증 드라이버 `training/validate_paths.py`(run/compare, 시드 짝지음) ② 기준 검증: 합친 정책 S3 final + lat + 새 커맨더 기본값, 경로 8 × 시드 10 ③ 통합 정책 Stage 4: `training/configs/ppo_unified_transition_stage4.yaml`(Stage 3 동일 + `align_rule: lat`, 03 final 재개, 40M) ④ 학습 중 커맨더 파라미터 탐색(동결 반지름·히스테리시스, 경로 8 × 시드 5) — 기본값 변경은 8경로 중 6개 이상 개선·전체 p<0.05·악화 경로 없음일 때만 ⑤ Stage 4 final을 고정 시드 40판 벤치마크(sign/lat)와 경로 검증(②와 짝지음)으로 Stage 3과 비교 ⑥ 비판적 검토 → 덱·원장·변경 이력 기록. 원본 정책·환경·runs 데이터는 삭제·이동하지 않음.
**파일(착수 시점):** `training/path_following.py`(`PATH_KINDS`, `make_path(kind, scale, start, rng)` 5종 추가, CLI `--path` 선택지 확장), `training/validate_paths.py`(신규), `training/configs/ppo_unified_transition_stage4.yaml`(신규).
**진행 기록:**
- 18:10 Stage 4 착수 (`runs/ppo_unified_transition_stage4/20260914-181034-263440_ppo_unified_transition_stage4`, fps 단독 1,985 / 검증 병행 시 1,565). 경로 5종(zigzag, scurve, octagon, serpentine=직각 굽이, uturn=168° 되돌기, random) 시드 1 스모크 전부 완주.
- 18:17~18:23 기준 검증 `runs/path_validation/s3_lat_base.json` (S3 final + lat + 주기 5·수직면, 경로 9 × 시드 10, 잡음 0.03·회전 8): 완주 90/90. 평균 오차 네모 .174 별 .206 장애물 .165 지그재그 .240 S자 .247 팔각형 .190 굽이길 .135 유턴 .140 무작위 .214 (최대 오차 .42~.79, 시간 23~51초).
- 커맨더 탐색 준비: `path_following.py`에 `--freeze-radius`(기본 0.85), `--hysteresis-deg`(기본 34) 추가(기본 동작 불변), result.txt `[커맨더]` 줄에 병기. `training/bench_unified_ckpts.py`(신규, scratchpad 고정 시드 벤치마크의 CLI판: `--cand 이름=model:vecnorm`, `--align-rule`, `--episodes`).
- 18:35 S3 final 고정 시드 40판 벤치마크(`runs/unified_bench/s3_{sign,lat}.json`): sign 규칙 리턴 16,414 완주 .75 전환실패 .066 δ203 .06 (09-10 값과 일치) / **lat 규칙 리턴 14,635 완주 .72 전환실패 .096 δ203 .22** — 무작위 전환 커리큘럼(전환 뒤 낙상 지표)에서는 sign으로 학습된 S3에 lat 규칙이 더 나쁨. 경로 추종(오차 지표)에서 U_lat가 나았던 것과 다른 결과 → Stage 4(lat로 학습)가 이 격차를 메우는지가 핵심 판정 항목.
- 18:40 커맨더 탐색 배치 1차는 zsh 인자 분리 오류(`set -- $cfg` 미분리)로 전부 실패 → 산출 JSON 2개 삭제 후 재실행(freeze {0.60, 0.45} × hyst 34, freeze 0.85 × hyst {25, 45}, freeze 0.60 × hyst 25; 경로 9 × 시드 10).
- 19:15 커맨더 탐색 결과(`runs/path_validation/tune_*.json`, `cmp_*_vs_base.json`; 기준 freeze 0.85·hyst 34와 90쌍 짝지음, 평균 오차 이김/비김/짐): freeze 0.60 37/38/15 Δ−.015 p=.003(최대 34/11, 시간 22/29) | **freeze 0.45 50/20/20 Δ−.024 p<.001(최대 47/11, 시간 30/38; 9경로 중 7개 개선, 나머지 2개 ±.001 동률, 악화 없음)** | hyst 25 48/3/39 Δ−.013 p=.39(시간 29/57 악화) | freeze 0.60+hyst 25 57/2/31 Δ−.033 p=.007(최대 60/29, 시간 26/62 크게 악화, 팔각형 +.023) | hyst 45 23/5/62 Δ+.039 악화. 히스테리시스를 줄이면 전환이 늘어 시간이 나빠지고, 동결 반지름을 줄이면 시간 손실 없이 오차가 준다. 2차 탐색: freeze 0.35(=판정 반지름), freeze 0.45+hyst 30.
- 19:40 2차 탐색: freeze 0.35 54/13/23 Δ−.026 p=.001 (0.45와 짝지음 22/50/18, 차이 없음) | freeze 0.45+hyst 30 60/6/24 Δ−.030 p<.001이나 0.45+hyst 34 대비 47/10/33 p=.15(유의 없음), 시간 35/51·팔각형 +.026 악화. **채택: 근접 동결 반지름 기본값 0.85 → 0.45 m (히스테리시스 34도 유지)** — 사전 규칙(9경로 중 6개 이상 개선, 전체 p<.05, 악화 경로 없음) 충족. `path_following.py` 세 곳 기본값 변경. 이후 S3/S4 비교의 S3 기준은 `tune_f045_h34.json`(S3+lat+새 기본값)을 쓴다.
- 19:15~19:25 잔여 오차 원인 분석(새 기본값 검증 90번의 trajectory.npz): 최대 오차 0.6 m 초과 22개 중 21개가 코너 뒤 3초가 지난 구간 중간(진행률 0.1~0.8)에서 발생, 코너 직후는 1개. 기제: 웨이포인트 자체를 겨냥하면 34도 히스테리시스가 허용하는 옆 오차가 남은 거리에 비례(≈0.21×거리 → 2 m 구간 0.4 m, 3 m 구간 0.6 m)하고, 관측 최대 오차(0.5~0.8 m, 구간 중간)와 맞는다. → 개선안: 선분 위 앞보기 점(lookahead) 겨냥.
- 19:25 `training/path_following.py`에 `--lookahead`(기본 0 = 예전 동작) 추가: `WaypointCommander(lookahead)`, `run(lookahead)`, `[커맨더]` 줄에 병기. 앞보기 점 = 이전 노드→웨이포인트 선분 위 수선 발에서 lookahead m 앞(선분 끝 초과 없음); 근접 동결은 웨이포인트 거리 기준 그대로. 기본값 재현 확인(square 시드 1: .103/.255/400스텝/8회 동일). 최악 사례 스모크: 지그재그 시드 7 최대 1.48 → 0.48(0.8 m)/0.27(0.5 m) m, 56 → 35/29초; 팔각형 시드 5 최대 1.14 → 0.50 m. 전체 검증(경로 9 × 시드 10, 0.5·0.8 m) 진행 중.
- 19:35 앞보기 검증(`runs/path_validation/la050.json`, `la080.json`, `cmp_la0*_vs_f045.json`; 기준 `tune_f045_h34`와 90쌍): **앞보기 0.5 m — 평균 오차 66/1/23 Δ−.036 m(−22%) p<.001, 최대 오차 56/32 p=.014, 0.8 m 초과 큰 실패 6→1, 되돌아간 전환 −20%; 그러나 시간 30/58 Δ+7.2초(+20%) p=.004, 전환 수 +50%(14.2→21.2).** 앞보기 0.8 m — 오차 48/7/35 Δ−.018 p=.19(유의 없음), 시간 +8% p=.32. 정확도와 시간의 맞바꿈이라 채택 기준(시간 악화 없음)을 채우지 못함 → 불감대 변형과 중간값(0.35, 0.65) 추가 검증.
- 19:40 `path_following.py`에 `--lookahead-deadband`(기본 0) 추가: 양수면 선분에서 옆으로 벗어난 거리가 이 값 이상일 때만 앞보기 점을 겨냥(되돌림 모드)하고 절반 아래로 줄면 웨이포인트 겨냥으로 복귀(모드 히스테리시스, 웨이포인트 도착 시 초기화). 기본 동작 불변(lookahead 0이면 무시). 스모크(지그재그 시드 7, 0.5 m + 불감대 0.25): 평균 .168 최대 .451 전환 42회 54초 — 순수 앞보기 0.5(.082/.267/18회/29초)보다 나쁨. 전체 검증(la035, la065, la050_db025) 진행 중.
- 19:40 기준 비교(`s3_sign_f045.json`, `experts_latall_f045.json`, `cmp_s3lat_vs_*.json`; 새 기본값, 경로 9 × 시드 10): **S3+lat vs S3+sign 평균 오차 44/1/45 Δ−.004 p=1.0 — 새 커맨더·아홉 경로에서는 새 규칙이 합친 정책의 오차를 줄이지 않음(시간은 63/26으로 lat가 빠름).** 09-13 v2(옛 커맨더, 경로 3)에서 U_lat가 U_sign을 오차로 이겼던 결과가 새 조건에서 재현되지 않음 → 덱 판정 문장 수정 필요. S3+lat vs 원본 전문가+lat 전부: 오차 56/0/34 Δ−.069 p=.026, 시간 54/35, 완주 90/90 대 90/90.
- 19:50 앞보기 2차 검증(`la035`, `la065`, `la050_db025`; 기준 `tune_f045_h34`, 90쌍): 0.35 m 오차 72/17 Δ−.051(−31%) p<.0001·시간 22/68 +29% p<.0001·전환 +77%·큰 실패 0 vs 6 | 0.65 m 오차 56/31 Δ−.024(−15%) p=.010·최대 62/23 p<.0001·시간 35/51 +12% p=.11·전환 +27% | **0.5 m + 불감대 0.25 m 오차 62/24 Δ−.029(−17%) p=.0001·최대 61/24 Δ−.092 p=.0001·큰 실패 2 vs 6·시간 38/46 +10% p=.45·전환 32/47 +26% p=.11, 아홉 경로 모두 오차 개선.** 완주 모두 90/90. 앞보기 거리가 짧을수록 오차↓ 시간↑의 맞바꿈 곡선(0.35/0.5/0.65/0.8: 오차 −31/−22/−15/−11%, 시간 +29/+20/+12/+8%). 기본값(앞보기 0 = 웨이포인트 겨냥)은 바꾸지 않음 — 시간이 늘어나는 변형은 사전 규칙상 채택 대상이 아니고 오차·시간 우선순위는 사용자 결정 사항. 검토 에이전트 검토 진행 중.
- 09-15 01:11 Stage 4 학습 완료(160.0M, 약 7시간, fps 1,520~1,610). 학습 곡선(처음 10% → 마지막 10% 평균): ep_rew 16,144 → 16,867, 전환 뒤 100스텝 실패 .061 → .049, post50 보상 −8.1 → −7.5, KL .012 → .014, EV .92 유지. 목표별 실패: diag_fr .098 → .043, diag_bl .109 → .072, diag_fl .155 → .118, diag_br .091 → .055 개선 / forward .047 → .076, right .045 → .072 악화(학습 중 확률 정책 값이라 벤치마크로 확인 필요). 20:00~05:00 검토 에이전트가 사용량 한도로 중단돼 캠페인이 멈췄고, 05:10 사용자 지시로 재개: Stage 4 평가(`scratchpad/s4_eval.sh`: 벤치 sign/lat 40판 + 경로 검증 s4_lat ↔ tune_f045_h34)와 검토 에이전트(Opus) 병행.
- 05:40 Stage 4 final 평가 결과(`runs/unified_bench/s3s4_{sign,lat}.json`, `runs/path_validation/s4_lat.json`, `cmp_s4_vs_s3_lat.json`): 고정 시드 40판 — **lat 규칙: S4 리턴 17,610 완주 .80 전환실패 .082(6/73) δ203 .18(3/17) vs S3 14,635 / .72 / .096(7/73) / .22(4/18)** (작은 개선, 실패 1건 차이) / **sign 규칙: S4 전환실패 .105(8/76) δ203 .22(4/18) vs S3 .066(5/76) / .06(1/17)** (악화, S4는 lat에 특화). 경로 검증(S4+lat vs S3+lat, 새 기본값, 90쌍): 평균 오차 41/2/47 Δ+.007 p=.59, 최대 46/44, 시간 44/46, 완주 90/90 대 90/90 — 차이 없음(장애물·팔각형·무작위는 S3가, 유턴은 S4가 나은 쪽). 잠정 판정(검토 전): 넷째 단계의 이득은 확인되지 않음, 대표 모델은 S3 final 유지. `bench_unified_ckpts.py`에 에피소드별 기록(`episodes`) 추가 후 재실행(결정론이라 집계값 동일) — 시드 짝지은 검정용.
- 06:20 검토 에이전트(Opus) 1차 검토 반영 — **정정:** (1) 19:15 항목의 기하 설명("옆 오차 ≈0.2×남은 거리와 관측이 맞는다")은 틀림: 최대 오차 지점의 옆 오차/남은 거리 중앙값 0.46으로 허용치의 2~3배, 90번 중 20번은 34도 한계 초과; 로봇의 실제 이동 방향이 목표에서 34도 넘게 벗어난 시간 15.5%(2초 평균) → 남은 오차는 겨냥 방식 + 보행 방향 오차의 합작. 위치 통계도 21/22가 아니라 20/22(시간 기준), 17/22(시간+구간 중간). (2) 19:40 항목의 "lat 이득 = 전환 뒤 흐트러짐 감소" 가설은 기각: 초당 전환 빈도 차이 없음(p=.20), 왕복형 전환 비율 33.5 vs 32.8% 동일, 속도 이득은 전환에서 먼 구간(80스텝 이후 1.26배)에서 최대; 전환 수 감소의 4/5는 주행 시간 감소의 결과. 확인된 사실: lat에서 무게중심 속도 +7.9%(p=.0004), 이동 거리 대비 경로 진행 비율 .78→.87(p=.0002), 원인 미상. (3) S3 vs 전문가: 짝 차이 중앙값 .023 m(평균 .069는 전문가 큰 실패 꼬리), 유턴은 18% 악화, p=.026은 홀름 보정(14개 비교) 후 .21; 큰 실패 6 vs 28(한쪽만 실패 5 대 27, p=.0001)이 가장 튼튼. (4) 앞보기 권고 수정: 정확도 우선이면 0.35 m(불감대 변형 대비 오차 61/28 p=.0006, 큰 실패 0), 중간이면 0.65 m ≈ 불감대 변형(모든 지표 차이 없음, 0.65가 매개변수 적고 경로별 시간 손실 고름); 스모크 사례(1.48→0.27 m)는 0.5 m 단독의 결과(불감대 변형은 0.45 m·54초). (5) 불감대 변형은 사전 채택 규칙(6경로 이상 개선·p<.05·악화 없음) 세 조건을 모두 채움 — 시간 조건은 사전 규칙에 없던 기준이므로 기본값 미변경은 규칙 이탈이며 사용자 결정 사항으로 명시. (6) 홀름 보정 후 남는 것: 앞보기 0.35·0.5·불감대(및 악화 쪽 동결 0.85·히스테리시스 45); 0.65(p=.0097)는 탈락. 가장 큰 한계: 앞보기 아이디어를 만든 데이터(기준 90번)와 변형을 채점한 데이터가 같음(남겨 둔 경로·시드 없음). 검토 통과: 앞보기 실행이 동결 0.45·히스테리시스 34로 돌았음(폴더 기록 확인), 시간 이득은 이상치 탓 아님, 비김 tol 0~0.01 m에서 주요 p 불변, 저장된 err/err_max가 trajectory.npz 재계산과 일치(90/90).
- 06:45 검토 에이전트 2차(Stage 4) 검토 반영 — **정정:** (1) 01:11 항목의 목표별 실패율 이름이 틀림(잘못된 순서로 읽음). gait_provider 순서(forward, left, right, diag_fl, diag_fr, backward, diag_bl, diag_br, ccw, cw)로 다시 읽으면: backward .098→.043, right .037→.016, diag_fr .155→.118, diag_bl .109→.072, diag_br .091→.055 개선 / forward .047→.076, diag_fl .045→.072 악화. "right 악화"는 사실이 아님. (2) 18:35 항목과 Stage 4 착수 근거였던 "S3에 lat를 쓰면 벤치마크가 더 나쁨(.096 vs .066)"은 짝지으면 lat만 낙상 6판/sign만 4판(p=.75), 완주 5 대 6, 리턴 17/23(p=.43)으로 40판 잡음 안 — 확인된 격차가 아님. 40판의 검출력 ≈10%(.03 차이), 잡으려면 ≈700판. (3) 05:40 항목의 "S4는 lat에 특화" 해석 철회: sign 규칙에서 총 낙상 10 대 10, 완주율 동일, 전환 직후 낙상 증가분(8 대 5)은 diag_fr·diag_bl 전환(4/18 대 1/17, p=.34)에만 있고 판단 불가. "δ203 도착 실패"는 "대각 두 방향으로 바꾼 직후 낙상(fail100의 부분집합)"으로 표기 통일. (4) S4 lat 리턴 편차 감소와 평균 차이 절반 이상은 시드 5019 한 판(S3 −68,689) 때문 → 개선 신호 아님. (5) 경로 추종 경로별 차이(유턴 8/2 등)는 열 쌍씩이라 Holm 후 ≥.88, 언급 안 함. (6) S3+lat 경로 검증(18:30)과 S4 검증(05:12) 사이에 path_following.py가 바뀌었으므로 S3+lat를 현재 스크립트로 재실행(`s3_lat_cur`)해 대조. 최종 판정: 넷째 단계 이득·손해 미확인, 대표 03 final 유지, 함께 쓸 규칙은 사용자 결정(경로 추종 목적이면 lat, 벤치마크 재현이면 sign). 원장 `policies/unified/TRAINING_HISTORY.txt` 4절 [완료]로 갱신.
- 06:55 S3+lat 경로 검증을 현재 `path_following.py`(앞보기 기능 포함, `--lookahead 0`)로 재실행(`runs/path_validation/s3_lat_cur.json`): 옛 결과 `tune_f045_h34`와 90쌍 전부 동일(0/90/0) → 스크립트 변경은 기본 경로에 영향 없음, S4 vs S3 비교(41/2/47, p=.59) 유효. 덱 51장 재빌드(슬라이드 44~49 신규: 경로 검증 ①②, 커맨더 최적화 ①②, 합친 정책 넷째 단계; 다음 단계·결과물 위치 갱신).

**캠페인 종합(09-14 18:10 ~ 09-15 07:00):**
- 코드: `training/path_following.py`(경로 6종, `--freeze-radius`·`--hysteresis-deg`·`--lookahead`·`--lookahead-deadband`, 기본값 동결 0.45), `training/validate_paths.py`(신규), `training/bench_unified_ckpts.py`(신규, 에피소드별 기록), `training/configs/ppo_unified_transition_stage4.yaml`(신규), `docs/deck_src/build_deck_plain.py`(슬라이드 6장 추가), `docs/figures/path_validation/paths_grid.png`.
- 채택: 커맨더 근접 동결 반지름 0.85 → 0.45 m(사전 규칙 충족). 미채택(사용자 결정): 앞보기(0.35 정확도 우선 / 0.65 중간; 불감대 변형은 사전 규칙 3조건 충족하나 시간 +10%), Stage 4 대표 교체(근거 없음), 함께 쓸 규칙(lat=경로 추종 시간 −16% / sign=벤치 재현).
- 검토가 고친 것: 기제 가설 2개 기각(lat 이득 = 흐트러짐 감소, 앞보기 기하 설명), 출발 전제 1개 격하(S3+lat 벤치 악화는 잡음), 목표 이름 오독 정정, "S4 lat 특화"·"경로별 차이" 삭제, 검출력(≈700판)·보정(Holm) 반영, 완주 정의(수직면 판정, 2번 옆 통과) 명시, 같은 데이터로 설계·채점한 한계 명시.
- 다음 후보: 남겨 둔 경로·시드로 앞보기 재채점, 경로 크기 1/3 m, 궤적에 yaw 기록, 벤치 전환 단위 기록·판 수 확대, lat 두 변화 분리, 회전→선형 전환 규칙.

---

## 2026-10-19 — 학습 기록에 코드 버전(수정 여부·변경분 패치) 남기기

**커밋:** (아래 주제별 커밋에 포함)
**요청:** 하네스 설정 대화형 정비 1번 항목 "코드 버전 기록과 커밋" — 선택: "해시 + 수정 여부 + 변경분 파일".
**배경:** `train.py`의 `git_revision()`은 `git rev-parse HEAD`만 기록해, 마지막 커밋(2026-08-06 `cb36eae`) 이후의 모든 run이 같은 해시를 가리켰다. 실제 코드는 크게 달라 기록이 사실과 어긋났다.
**파일:** `training/train.py`
**변경:** `git_state(run_dir)` 추가, `save_run_metadata`가 이를 사용. metadata.json에 `git_revision`(그대로), `git_dirty`, `git_untracked_source_files`, `git_diff_sha256`, `git_diff_file` 기록. 수정 상태면 `<run_dir>/git_diff.patch` 저장 — 코드 경로(`horcrux_env/`, `training/`, `scripts/`, `pyproject.toml`)의 HEAD 대비 변경 + 같은 폴더의 미추적 소스 파일(.py .yaml .yml .xml .sh .json .txt .md) 전체. `policies/`·`docs/`·`runs/`는 넣지 않음(첫 시도에서 policies 옛 기록 삭제분이 적용 실패해 패치 전체가 막혔음). 되살리기: `git checkout <git_revision> && git apply <run_dir>/git_diff.patch`.
**검증:** 현재 작업 트리로 패치 생성(약 0.6 MB, 미추적 소스 69개) → HEAD 깨끗한 작업 트리에 `git apply` 성공 → 변경·미추적 코드 파일 92개 전부 작업 트리와 바이트 일치. 이전 run의 metadata는 바꾸지 않음(8월 이후 run의 해시는 여전히 실제 코드와 다름 — 원장에 주의 문구 필요).

---

## 2026-10-20 — 작업 규칙 정리: CLAUDE.md로 모으기, 기술 노트 분리

**커밋:** (미커밋)
**요청:** 하네스 설정 대화형 정비 2번 항목 "규칙 정리". 사용자 선택: 실험 안전·보고 기준 묶음을 CLAUDE.md로 이동, 추가 규칙 두 개(검토 불가 시 대체 규칙, 임시 폴더에 중요 스크립트 금지), AGENTS.md 기술 설명은 별도 문서로, 같은 내용의 메모리 피드백 파일은 사연만 남겨 축소. 글쓰기·실행 환경 묶음은 CLAUDE.md로 옮기지 않음.
**파일:** `CLAUDE.md`, `docs/TECH_NOTES.md`(신규), 사용자 메모리(`feedback_claude_changes_log.md`, `feedback_plan_before_training.md`, `feedback_plan_checklist_routine.md`, `feedback_critic_review_before_answer.md`, `MEMORY.md`, `project_direction_policy_campaign.md` 머리 설명)
**변경:**
- `CLAUDE.md`: 기존 두 규칙(계획 목록, 변경 이력) 유지 + 작업 방식 2개(요청한 것만 바꾸기, 스크립트는 저장소 안에) + "실험 안전" 5개(학습 시작 금지, runs 소유권, 고정 환경·보상 의미, 모델·통계 짝, 이어 학습마다 새 YAML) + "결과 보고 기준" 8개(비판적 검토, 검토 불가 시 대체 규칙, 표 근거 열, 짝지은 비교, best_model 선택 효과, 학습 상태 확인, 기제 설명은 확인된 것만). 머리에 TECH_NOTES 안내와 "AGENTS.md는 따르지 않음" 명시. 22줄 → 약 80줄.
- `docs/TECH_NOTES.md`: AGENTS.md의 기술 설명(종료 의미, 관측·행동 정규화, 기본 PPO, 이어 학습, 콜백 빈도, 알려진 함정, 렌더링)을 리눅스 기준으로 옮기고, 실행 환경(conda 경로, launch_training.sh, zsh 주의점, 새 git 버전 기록)과 대화에서 쌓인 함정(낙상 페널티 0, getMvec 부호, max_episode_steps 가로채기, reset 잡음 0, fail_to 번호 순서)을 더함. 버린 것: PowerShell 기본 셸, `C:\` 경로, "보이는 창에서 학습", 왼쪽 정책을 "현재 대표"로 적은 낡은 상태.
- `AGENTS.md`는 손대지 않음(git 무시 대상 그대로).
- 메모리: 피드백 파일 4개를 "규칙 본문은 CLAUDE.md, 여기는 사연" 형식으로 축소(검토 파일에는 검토가 실제로 잡은 오류 사례 5개 추가), 목차 갱신, 캠페인 메모리의 낡은 설명("진행 중인 delta=0 전진 학습") 교체. 줄이기 전 사본은 세션 임시 폴더 `scratchpad/memory_backup_20261020/`.

---

## 2026-10-20 — 하네스 정비 1단계: 로그 파일 추적 제외, 원격 SSH 전환, 규칙 커밋

**커밋:** (이 항목을 포함한 커밋)
**요청:** 하네스 재점검 뒤 "하나씩 진행" — 제안 순서 1단계(커밋·push, SSH 전환, 로그 파일 제외).
**파일:** `.gitignore`, `MUJOCO_LOG.TXT`(추적 제외, 파일은 그대로 둠), `docs/TECH_NOTES.md`(알려진 함정 한 줄), git 원격 설정
**변경:** `MUJOCO_LOG.TXT`는 MuJoCo 발산 경고 490건(2026-07-27~08-11, 스케일링 실험)만 담고 그 뒤 변화가 없어 `git rm --cached` 후 무시 목록에 넣음. 원격 `origin`을 HTTPS에서 `git@github.com:VanguardDream/horcrux_env.git`으로 바꿈(HTTPS는 자격 증명 도우미가 없어 push가 막혔고, SSH 키는 이 저장소에 등록돼 있음). 2번 항목 결과(`CLAUDE.md`, `docs/TECH_NOTES.md`)를 함께 커밋.

---

## 2026-10-20 — 하네스 정비 2단계: 백업 스크립트와 보존 규칙

**커밋:** (미커밋)
**요청:** 하네스 재점검에서 "백업 없음"이 가장 큰 문제로 나와 2단계로 진행. 사용자 선택: 8TB 디스크(`/dev/sda`, ext4, 라벨 8TB, UUID 154f1c52-…)를 마운트해 사용, 범위는 `policies` + `runs` 전체(372GB), 보존 규칙은 "아무것도 지우지 않음".
**파일:** `scripts/backup_to_disk.sh`(신규), `CLAUDE.md`("실험 안전"에 백업·보존 항목 추가)
**변경:** rsync 추가·갱신 전용 백업(`--delete` 없음, `--partial`, `__pycache__` 제외) + git 번들(`horcrux_env.bundle`, 전체 이력)을 `<BACKUP_ROOT>/horcrux_env/`에 복사, `backup_log.txt`에 시작·종료·크기 기록. 마운트돼 있지 않으면 중단. `--dry-run` 지원. 마운트(관리자 권한)는 사용자가 직접 함 — fstab에 `nofail`로 등록해 디스크가 없어도 부팅이 막히지 않게 안내. 첫 백업은 마운트 뒤 실행.
**결과(18:19~18:57):** 첫 전체 백업 완료 — 371GB, 파일 수 원본·백업 일치(runs 30,768 / policies 15,519), git 번들 `0f6baa4` 검증 통과, 재실행 시 runs·policies 전송 0건. 그 뒤 범위에 `docs/`(덱·그림·기술 노트, 27파일 57MB)를 더하고 rsync 통계를 상세(`--stats`)로 바꿔 로그에 "전송 파일 수"가 남게 함. 진행률 출력(`--info=progress2`)은 캐리지 리턴으로 로그를 오염시켜 제거. 첫 시도는 세션 백그라운드(10분 제한)로 띄웠다가 중단하고 `setsid nohup`으로 다시 띄웠음(rsync `--partial`이라 이어서 복사). 백업 디스크 남은 공간 6.5TB.

---

## 2026-10-20 — 하네스 정비 3단계: 발표 덱 pptx 추적 중단

**커밋:** (이 항목을 포함한 커밋)
**요청:** 하네스 재점검 3단계. 사용자 선택: "추적 중단, 백업 디스크에 보관".
**파일:** `.gitignore`, `docs/Horcrux_*.pptx` 3개(추적 제외, 파일은 그대로 둠)
**변경:** `/docs/*.pptx`를 무시하되 템플릿 `docs/PPT샘플.pptx`는 예외로 추적 유지. 이미 커밋된 이력은 다시 쓰지 않음. 덱은 `docs/deck_src/` 스크립트로 다시 만들며, 백업 스크립트에 `docs/`를 추가하는 것은 진행 중인 첫 백업이 끝난 뒤(실행 중인 셸 스크립트 수정 방지).

---

## 2026-10-20 — 하네스 정비 4단계: 환경 회귀 테스트와 PreToolUse 확인 훅

**커밋:** (이 항목을 포함한 커밋)
**요청:** 하네스 재점검 4단계. 사용자 선택: pytest 설치, 훅은 "확인 요구", 보호 대상은 완성 계보 환경 전부.
**파일:** `tests/test_env_regression.py`(신규), `tests/golden.json`(신규, 기준값), `scripts/hooks/pretool_guard.py`(신규), `.claude/settings.json`(신규), `CLAUDE.md`("실험 안전"에 테스트·훅 항목), conda `horcrux`에 pytest 9.1.1 설치
**변경:**
- 테스트: 완성 계보의 실제 설정(resolved_config.yaml / iter4 YAML)으로 `plane-v0`(forward 전문가), `plane-rotation-v0`(ccw), `plane-unified-v0`(Stage 3), `plane-moving-init-v0`(iter4, 상태 은행 없으면 건너뜀)을 고정 시드 123·고정 행동열로 300스텝 돌려 관측 차원, 총 리턴, 보상·비용 항별 합계, 종료·절단 횟수, 마지막 무게중심을 `tests/golden.json`과 1e-6 허용으로 비교. 사전 확인: 네 환경 모두 재실행 차이 0(결정론), 환경당 약 0.5초. 보상은 info 항의 단순 합이 아니라(최대 차이 1e2~1e3) 분해 항등식 대신 항별 합계를 잠금. 기준값에는 plane_v3 종료 벌점 0 결함 등 현재 동작이 그대로 들어감(주석 명시).
- 훅: `PreToolUse`에서 Bash 명령에 `launch_training.sh`/`train.py`가 있으면 "ask"; 보호 파일 이름 + 쓰기 흔적(sed -i, >, tee, mv, cp, write_text 등)이 함께 있으면 "ask"; Edit/Write/MultiEdit/NotebookEdit 대상이 보호 파일이면 "ask". 보호 목록: plane_v3, plane_rotation_v1, plane_unified_v1, plane_moving_init_v1, gait_provider, gait_v2, gait_v3, phase_align. 훅은 우회 가능하므로 의미 변화 감지는 테스트가 맡음. 설정은 새 세션부터 적용.

---

## 2026-10-20 — 하네스 정비 5단계: 결과 파일 위치 규칙, 연구 일지, /report 커맨드

**커밋:** (이 항목을 포함한 커밋)
**요청:** 하네스 재점검 5단계 "연구 진행을 문서로 기록하면서 시각화·발표까지 이어지는 흐름". 사용자 선택: 결과 JSON은 `results/<주제>/`, 보고 명령은 슬래시 커맨드 `/report`, 일지는 실험 하나가 한 항목.
**파일:** `results/`(신규, 기존 결과 JSON 51개 4.7MB를 `runs/`에서 복사 — 원본은 그대로), `training/validate_paths.py`·`training/eval_phase_rules.py`·`training/eval_expert_transitions.py`(기본 출력 경로 `runs/…` → `results/…`), `training/bench_unified_ckpts.py`(사용 예), `docs/deck_src/build_deck_plain.py`(결과 JSON 읽는 경로 6곳 → `results/`), `docs/deck_src/README.md`, `docs/RESEARCH_LOG.md`(신규, 틀 + 2026-09 캠페인 7항목), `.claude/commands/report.md`(신규), `CLAUDE.md`("연구 기록" 절 신설)
**변경:** 평가·검증 스크립트의 기본 출력이 git 추적 폴더 `results/`가 되어 저장소만으로 덱의 수치 슬라이드를 다시 만들 수 있음(영상 슬라이드는 `runs/` 또는 백업 필요). 덱 빌드는 `docs/deck_src`를 데이터 폴더로 쓰며 포스터도 거기에 만들어 추적. `/report`: 결과 확인 → 판정 초안 → 비판적 검토 → 일지 항목 → 슬라이드 → 덱 빌드·검증·렌더 확인 → 변경 이력·백업 → 보고. 코드에 손으로 적힌 옛 수치는 이번에 JSON화하지 않고(docstring에 출처만 명시) 다음 실험부터 규칙 적용.

<!-- 이후 Claude가 변경을 가할 때마다 아래 형식으로 항목을 추가합니다.

## YYYY-MM-DD — 변경 제목

**커밋:** `<hash>`
**요청:** <사용자가 요청한 내용 — 변경의 배경과 목적>
**파일:** `<파일 경로>`
**변경:** <변경 내용 요약>

-->
