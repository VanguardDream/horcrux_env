# bsmotor_dt — 보존된 DT 대조군 정책 (back-EMF 물리, 7.86M)

`bsmotor_gd`의 **대조군(direct torque, no-GD)** 원본 run 보존본. 관절 수
스케일링 질의(Hhic Q5) 대응 캠페인에서 GD와 동일 조건으로 학습된 짝이다
(2026-08-12 완주, runs/corl2026_scaling에서 이동, 12런 전부 final_model 존재).

## GD와의 차이 (이것만 다르고 나머지 전부 동일)

- 환경: `horcrux_env/plane-direct-torque-scalable-v0` — **gait prior 없음**,
  정책이 관절 토크를 직접 출력 (torque_min/max ±2.7 N·m)
- GD 쪽의 gait 파라미터(파동 수 고정 e, δ=0)는 해당 없음

## 공통 설정 (bsmotor_gd와 동일)

- **model_variant: motor** (τ = ctrl − 0.503·ω, XM430 12V back-EMF —
  토크-속도 엔벨로프 물리 강제)
- 보상: yaw 패널티 10.0(방향 정렬 표준), joy=[1,0,0], 나머지 기본
- PPO run-3 레시피 (lr 1e-4 linear→0, n_epochs 10, target_kl 0.04),
  7,864,320 스텝, unhealthy 30, 시드 42/43/44, n ∈ {6, 10, 14, 20}
- config: `runs/corl2026_scaling/configs/ppo_plane_scaling_dt_bsmotor_n*.yaml`
  (run별 적용본은 각 타임스탬프 폴더의 resolved_config.yaml — **run 식별은
  반드시 resolved_config.yaml의 seed로**)

## 성능 (결정론 롤아웃 3000스텝, ../bsmotor_gd/alignment_feasibility.csv)

| run | v_x (m/s) | 평균 \|ω\| (rad/s) | 판정 |
|---|---|---|---|
| n06 s42/43/44 | 0.12 / 0.00 / 0.05 | 2.4 / 0.03 / 3.0 | 부분 보행 (s43 실패) |
| n10 s42/43/44 | 0.24 / 0.32 / 0.00 | 2.7 / 3.1 / 0.01 | 2/3 보행 (s44 실패) |
| n14 s42/43/44 | 0.50 / 0.36 / 0.53 | 2.6~3.0 | **3/3 보행** |
| n20 s42/43/44 | 0.83 / 0.92 / 0.53 | 2.5~2.9 | **3/3 보행** |

## GD 대비 판정 (정직 기록)

- back-EMF 물리가 엔벨로프를 강제하는 이 체계에서는 **DT가 표본 효율
  (0.52~0.81×)·최고 속도(n20 0.92 vs GD 0.59 m/s) 우세** — 물리가 실현성을
  보장하면 prior 제약 비용이 이득을 상회
- GD의 잔여 우위: 시드 일관성(n≥10 9/9 vs DT 8/9), 보수적 관절 속도
  (1.1~1.9 vs 2.5~3.1 rad/s; 무부하 한계 5.97)
- 용도: 리부탈 Q5 헤드라인은 논문 원 물리 매트릭스(analysis_delta0) 유지,
  bsmotor 쌍은 "actuator 충실도 × prior 이득" 논의(저널 확장판) 자료
- 분석 산출물: `runs/corl2026_scaling/analysis_bsmotor7M/`

## 진행 중 (2026-08-12 현재)

후속 계보 `dt_bsmsym` (configs/ppo_plane_scaling_dt_bsmsym_n*.yaml)이
runs/corl2026_scaling에서 학습 중 — 완주 후 별도 보존 예정. 이 폴더의
12런은 완결 상태로 변경 없음.

## 사용법

```bash
# 예: n=14 시드 42 정책 평가 (타임스탬프 폴더의 resolved_config.yaml로 시드 확인)
conda run -n horcrux python training/evaluate.py \
  policies/corl2026_scaling/bsmotor_dt/dt_bsmotor_n14/20260812-030113-585617_scaling_dt_bsmotor_n14/final_model.zip
```
