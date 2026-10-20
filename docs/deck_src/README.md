# 발표 덱 빌드 스크립트

python-pptx로 사용자 템플릿(`docs/PPT샘플.pptx`) 위에 덱을 만드는 스크립트 모음이다. 세션 임시 폴더에만
있던 것을 다시 만들 수 있도록 여기에 보관한다 (2026-09-11).

| 스크립트 | 만드는 파일 | 비고 |
|---|---|---|
| `build_deck.py` | `docs/Horcrux_transition_research_2026-09.pptx` | 16:9 초기판 (템플릿 없음) |
| `build_deck_template.py` | `docs/Horcrux_transition_research_2026-09_template.pptx` (33장판) | 템플릿 적용판 |
| `build_deck_plain.py` | `docs/Horcrux_transition_research_2026-09_template.pptx` (40장, 현재판) | 쉬운 문장판. 인자로 데이터 폴더를 받는다 |
| `make_phase_figures.py` | `docs/figures/phase_selection/*.png` | 위상 선택 근거 덱의 그림 |
| `build_deck_phase.py` | `docs/Horcrux_phase_selection_math_2026-09.pptx` | 위상 선택 근거 덱 |

실행 예 (conda `horcrux` 환경):

```bash
/home/bong/anaconda3/envs/horcrux/bin/python docs/deck_src/build_deck_plain.py docs/deck_src
```

- `build_deck_plain.py`는 `curves.json`(텐서보드 곡선 요약), `bench_ckpts.json`(체크포인트 벤치마크),
  그리고 `results/` 아래 결과 JSON(`results/moving_state_bank/eval_*.json`, `results/path_validation/*.json`,
  `results/unified_bench/*.json`, `results/path_follow_demo/v*_summary.json`; 2026-10-20부터 git 추적)을 읽는다.
  영상 포스터는 처음 실행할 때 `<데이터 폴더>/posters/`에 만들고(추적함), 영상 파일과 v2 시연 폴더
  (`runs/path_follow_demo/*`, `runs/policy_showcase/*`)는 `runs/` 원본을 참조한다. `runs/`가 없는 컴퓨터에서는
  영상 슬라이드만 비고 나머지는 만들어진다(백업 디스크의 `runs/`를 복원하면 전부 된다).
- 실험이 끝난 뒤의 정리 절차(결과 JSON → 연구 일지 `docs/RESEARCH_LOG.md` → 슬라이드 → 덱 → 백업)는
  `/report` 커맨드(`.claude/commands/report.md`)에 있다.
- `make_phase_figures.py`는 상태 은행 `runs/moving_state_bank/bank_iter1.npz`와
  `training/eval_phase_rules.py`(궤도 표, 규칙)를 쓰고, 실험 결과 `runs/moving_state_bank/eval_phase_rules*.json`이
  있으면 거리-실패 곡선과 규칙 비교 그림도 만든다. 인자 없이 실행하면 전부 만들고, `f1 f5 f8`처럼 일부만 고를 수 있다.
- `build_deck_phase.py`는 위 그림과 실험 JSON을 읽어 17장을 만든다. 실험 결과가 없으면 해당 슬라이드에 대기 문구를 넣는다.
- 검증과 렌더는 pptx 스킬의 `validate.py --original docs/PPT샘플.pptx`와 LibreOffice PDF 변환으로 했다.
