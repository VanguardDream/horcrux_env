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

<!-- 이후 Claude가 변경을 가할 때마다 아래 형식으로 항목을 추가합니다.

## YYYY-MM-DD — 변경 제목

**커밋:** `<hash>`
**요청:** <사용자가 요청한 내용 — 변경의 배경과 목적>
**파일:** `<파일 경로>`
**변경:** <변경 내용 요약>

-->
