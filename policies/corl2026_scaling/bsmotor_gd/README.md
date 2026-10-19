# bsmotor_gd — 보존된 GD 정책 (back-EMF 물리 + 정렬 레시피, 7.86M)

CoRL 2026 스케일링 실험 중 가장 완성도 높은 GD 계보의 원본 run 보존본
(2026-08-12 완주, runs/corl2026_scaling에서 이동).

## 설정 요약

- 환경: `horcrux_env/plane-scalable-v0`, **model_variant: motor**
  (τ = ctrl − 0.503·ω, XM430 12V back-EMF — 토크-속도 엔벨로프 물리 강제)
- 보상: yaw 패널티 10.0(방향 정렬 표준), 나머지 기본. gait: 파동 수 고정
  e = 30·14/n → n06=70 / n10=42 / n14=30 / n20=21, δ=0
- PPO run-3 레시피 (lr 1e-4 linear→0, n_epochs 10, target_kl 0.04),
  7,864,320 스텝, unhealthy 30(정확), 시드 42/43/44
- config: `runs/corl2026_scaling/configs/ppo_plane_scaling_gd_bsmotor_n*.yaml`
  (run별 적용본은 각 폴더 resolved_config.yaml)

## 성능 (결정론 롤아웃 3000스텝, alignment_feasibility.csv)

| run | v_x (m/s) | 몸통 yaw | 평균 \|ω\| (rad/s) | 판정 |
|---|---|---|---|---|
| n06 s42/43/44 | -0.02 / 0.00 / 0.00 | ±6° | 0.0~1.1 | 보행 실패 (정지 생존) |
| n10 s42/43/44 | 0.10 / 0.13 / 0.16 | 0° | 1.5~1.6 | **정면 보행** |
| n14 s42/43/44 | 0.28 / 0.22 / 0.32 | ≤2° | 1.5~1.8 | **정면 보행** |
| n20 s42/43/44 | 0.58 / 0.59 / 0.18 | ≤5° | 1.1~1.9 | **정면 보행** |

- 학습 최종 성능(F_n)이 n과 함께 단조 증가한 유일한 캠페인: 8.7k → 47k → 95k → 158k
- 전 정책이 액추에이터 엔벨로프 깊숙이 안쪽(≤1.9 rad/s, 한계 5.97)에서 동작
- 학습 곡선·표: `runs/corl2026_scaling/analysis_bsmotor7M/`

## 사용법

```bash
# 예: n=14 시드 42 정책 평가
conda run -n horcrux python training/evaluate.py \
  policies/corl2026_scaling/bsmotor_gd/n14_s42/final_model.zip
```
