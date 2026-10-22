# training/ — 설치와 실행

2026-10-22에 줄였다. 예전 판(2026-07, PowerShell 기준 385줄)의 기술 설명은 `docs/TECH_NOTES.md`로 옮겼고,
작업 규칙은 `CLAUDE.md`에 있다. 여기에는 설치, 스모크 실행, 자주 쓰는 명령만 둔다.

## 설치 (리눅스, conda)

```bash
bash scripts/setup_conda_env.sh            # conda 환경 horcrux 생성, CUDA PyTorch, 설치 검증, 스모크 학습까지
bash scripts/setup_conda_env.sh --cpu      # GPU 없는 컴퓨터
```

파이썬 경로는 `/home/bong/anaconda3/envs/horcrux/bin/python`이다(이 문서의 `python`은 이 경로를 뜻한다).

## 스모크 실행 (경로 확인용, 학습 성능 기준 아님)

```bash
python training/run_env.py                                   # 환경이 돌아가는지
python training/train.py --config training/configs/smoke.yaml  # 학습 경로 전체 (환경 2개, 작은 망, 256스텝)
python -m pytest tests -q                                    # 완성 계보 환경의 회귀 테스트 (약 3초)
```

환경 파일을 고쳤으면 회귀 테스트를 돌린다. 기준값을 바꾸는 것이 의도라면
`python tests/test_env_regression.py --update` 뒤에 변경 이력에 적는다.

## 학습

```bash
scripts/launch_training.sh training/configs/<설정>.yaml <태그>   # 셸·세션과 분리해 실행, 로그·PID 파일 생성
tail -f <experiment.output_dir>/console_<태그>.log
kill "$(cat <experiment.output_dir>/<태그>.pid)"                 # 멈추기
tensorboard --logdir runs --port 6006
```

학습은 사용자 승인 뒤에만 띄운다(`CLAUDE.md` "실험 안전"). 설정 파일 하나가 실험 하나이고, 이어 학습은 새 YAML과 새
`experiment.name`을 쓴다. run 폴더의 `metadata.json`에 코드 버전(커밋, 수정 여부, 변경분 패치)이 남는다.

## 평가와 분석

```bash
python training/evaluate.py <model.zip> --episodes 5          # 짝이 맞는 정규화 통계를 자동으로 찾음
python training/validate_paths.py run --tag <이름> --model <zip> --vecnorm <pkl>   # 경로 9종 × 시드 10 → results/path_validation/
python training/validate_paths.py compare results/path_validation/<a>.json results/path_validation/<b>.json
python training/bench_unified_ckpts.py --out results/unified_bench/<이름>.json --cand "이름=model.zip:vecnormalize.pkl"
python training/path_following.py --path square --policy unified --model <zip> --vecnorm <pkl>   # 시연 영상
```

결과 JSON은 `results/<주제>/`에 두고 git이 추적한다. 실험이 끝난 뒤의 정리(연구 일지, 슬라이드, 덱, 백업)는
`/report` 커맨드를 쓴다.

## 폴더

- `train.py`, `evaluate.py`, `run_env.py`: 학습, 평가, 환경 확인
- `configs/`: 실험 YAML (`smoke.yaml`은 경로 확인용)
- `callbacks/`: info 지표 기록, 영상 녹화, 정규화 통계 저장
- `validate_paths.py`, `bench_unified_ckpts.py`, `eval_phase_rules.py`, `eval_expert_transitions.py`,
  `path_following.py`, `distill_experts.py`, `build_moving_state_bank.py`: 검증·분석 도구 (각 파일 머리 설명 참조)
