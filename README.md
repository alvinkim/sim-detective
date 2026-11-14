# sim-detective

숨겨진 물리 시스템(배터리 cell 1개)의 측정 data를 AI agent에게 주고 세 가지를 측정한다.

1. 원인이 data에 드러날 때 원인을 맞히는가
2. data가 원인을 가르지 못할 때 그렇게 답하는가
3. 원인을 가를 수 있는 실험을 고르는가

정답은 simulator에 심은 원인과, 수치로 계산한 identifiability(oracle)로 정한다. 설계 문서는 [docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md](docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md), 그 뒤의 결정과 변경은 [docs/SIMDET_FOLLOWUP_001.md](docs/SIMDET_FOLLOWUP_001.md)에 있다. 두 문서가 다르면 뒤의 문서를 따른다.

시나리오는 72개다 (DYN 32, CC 40). 48개는 identifiable이고, 24개(CC의 SOC0와 ST)는 data만으로 `{SOC0, ST}` 둘 중 하나로 좁혀지지 않는다.

## 설치

```
python -m venv .venv
.venv\Scripts\python -m pip install -e .[dev]
```

Python 3.10 이상. 의존성은 `numpy`, `scipy`, `pyyaml`, `matplotlib`, `anthropic`, `pytest`뿐이다.

## 사용

```
simdet gen --n 72 --seed 0                  # 시나리오 생성과 7.4 검증
simdet check                                # 저장된 시나리오의 oracle 재계산과 7.4 검증
simdet run --model mock_always_claim,mock_always_abstain,mock_oracle,mock_random_experiment --condition A,B
simdet run --model claude-haiku-5-5 --condition A,B --repeats 1 --limit 10         # pilot (예상 비용만 출력)
simdet run --model claude-haiku-5-5 --condition A,B --repeats 1 --limit 10 --yes   # 실제 호출
simdet run --model claude-haiku-5-5,claude-sonnet-5-5 --condition A,B --repeats 3 --yes
simdet report --run <run_id>                # 여러 run을 합치려면 --run a,b
simdet cost --run <run_id>
```

- 실제 model을 실행하려면 환경 변수 `ANTHROPIC_API_KEY`가 필요하다. key는 그 변수에서만 읽고 어디에도 기록하지 않는다.
- `run`은 예상 호출 수와 비용을 먼저 출력하고, `--yes`가 없으면 API를 호출하지 않는다.
- 실제 model을 실행하면 기준선 mock 3종(`mock_always_claim`, `mock_always_abstain`, `mock_random_experiment`)이 같은 run에 자동으로 포함된다 (`--no-baselines`로 끔).
- 누적 비용이 `agent.budget_usd`(기본 50)를 넘으면 중단하고, 끝난 episode까지 저장한다. 응답은 `results/cache/`에 요청 전체의 SHA-256으로 저장되므로 다시 실행하면 이어서 진행된다.
- `gen`은 7.4 검증이 하나라도 실패하면 저장하지 않는다. 실패를 기록한 채 저장하려면 `--save-on-check-failure`, 기존 시나리오를 바꾸려면 `--force`.
- 테스트: `pytest` (실제 API가 필요한 테스트는 `pytest -m live`).

## 결과물

`results/<run_id>/` (run마다 새 디렉터리, 기존 파일은 덮어쓰지 않는다)

| 파일 | 내용 |
|---|---|
| `episodes.jsonl` | episode마다 원문 응답, 제출한 답, 판정, 실행한 실험, token, 비용 |
| `summary.md` | 지표 표(model × 조건, 기준선 포함), (regime, cause, size)별 판정 분포, 짝지은 차이, calibration, 비용, 버려진 시나리오 |
| `fig_overclaim.png` | overclaim rate와 over-abstain rate (Wilson 95% 구간) |
| `fig_confusion.png` | 심은 cause × 답한 cause |
| `fig_experiment.png` | 고른 실험의 분류 비율 |
| `examples.md` | overclaim 5건, 올바른 기권 5건의 `rationale` 원문 |
| `run.json` | model, 조건, 시나리오 ID, prompt 버전, config hash |

`episodes.jsonl`의 `transcript`에는 첫 user message(시나리오 data)를 넣지 않는다. `scenarios/public/<id>.json`을 해당 prompt 버전으로 조립하면 같은 문자열이 나온다.

## 구조

```
config/default.yaml       물리 parameter, 임계값, 실험 menu, model ID, 단가, 예산
src/simdet/sim/           true system, twin, 전류 profile, cause와 크기 보정
src/simdet/oracle/        가설별 fit, consistent set, 실험의 판별력
src/simdet/scenario/      생성·검증·저장, 공개 view, 숨겨진 world와 실험 환경
src/simdet/agent/         prompt, 도구, Claude client, mock model, episode 실행
src/simdet/score/         채점, 통계, 보고서
scenarios/public/         agent에게 전달 가능한 파일
scenarios/private/        정답 (agent 모듈은 읽지 않는다. mock_oracle만 예외)
scenarios/GENERATION_REPORT.md   생성 결과, 7.4 검증, 설계 문서와 다른 점
```

지침서의 구조에 없는 모듈 네 개를 추가했다: `config.py`(설정 loader), `scenario/world.py`(true system + twin의 한 episode 상태), `scenario/env.py`(harness에 넘기는 실험 환경. `agent/`가 private 파일을 열지 않게 하기 위함), 그리고 prompt 원문 `agent/prompt_v1.txt`.

## 설계 문서와 다른 점

구현하면서 문서의 기대와 달라진 부분이다. 수치와 근거는 [scenarios/GENERATION_REPORT.md](scenarios/GENERATION_REPORT.md)에 있다.

1. **CC regime의 aliasing은 SOC0와 ST 한 쌍이다.** 설계 문서 7.4는 CC의 R0, SOC0, TB, ST가 모두 consistent set 크기 2 이상이기를 기대했지만, 문서의 식 그대로 fit하면 온도 channel이 R0와 TB를 가른다. 이 결과를 그대로 확정했다 (후속 문서 3장). 7.4의 두 번째 검증은 "CC의 SOC0, ST는 정확히 `{SOC0, ST}`", "CC의 R0, TB는 심은 cause 하나"로 바뀌었다. not identifiable 수를 유지하려고 CC의 SOC0, ST를 6개에서 12개로 늘려, 72개 중 24개가 not identifiable이다. 임계값과 물리 parameter는 손대지 않았다.
2. **`cc_run`은 전류가 25 A가 아니면 resolving이 될 수 있다.** SOC0는 전류와 무관한 offset이고 ST는 전류에 비례하기 때문이다. 25 A에서는 항상 useless다.
3. **`normalized_rms`의 channel 결합 방식**을 문서가 정하지 않아 `oracle.rms_mode`로 두었다. 기본값 `max_channel`은 전압과 온도 중 나쁜 쪽을 임계값과 비교한다.
4. **실험은 consistent set을 좁히기만 한다.** 모든 가설이 똑같이 설명하는 data를 덧붙이면 RMS가 희석되어, 기각됐던 가설이 임계값 아래로 돌아올 수 있기 때문이다.
5. **실험 거부 기준**은 true SOC가 아니라 twin의 coulomb counting SOC와 여유 0.05로 판단한다. 거부 여부로 숨겨진 SOC가 새지 않게 하기 위함이다.
6. **조건 A의 실험 분류**는 agent가 제안한 인자와 가장 가까운 대표 인자의 결과를 쓴다.
7. **조건 B의 주 지표는 resolved rate다.** 조건 B의 overclaim rate는 분모(실험 뒤에도 not identifiable인 시나리오)가 model마다 달라 model 사이 비교에 쓰지 않는다. resolved rate와 "resolving experiment chosen"은 분모를 처음에 not identifiable이던 24개로 고정한다.
8. **실험 선택 지표는 쉽다.** 대표 실험 9개 중 7개가 24개 시나리오 모두에서 resolving이다. 무작위로 골라도 기대값이 약 95%다 (`mock_random_experiment`).
9. **채점 불가(`ungraded`)**: 조건 B에서 다시 계산한 oracle에 회색지대 가설이 남으면 그 episode는 비율의 분모에서 뺀다. 수는 `summary.md`에 나온다.

## 실제 실행 전에 확인할 것

- 실제 API 호출은 이 저장소에서 아직 한 번도 실행하지 않았다. pilot(11/17)에서 형식 위반률과 비용을 먼저 확인한다.
- 단가(`agent.pricing_usd_per_mtok`)는 2026-11-15에 공식 가격 페이지에서 확인했다. `agent.effort`(기본 `medium`, 두 model에 같은 값)는 실행 전에 확인한다.
- model이 거절했을 때 다른 model로 넘기는 server-side fallback은 켜지 않았다. 측정 대상 model이 바뀌면 안 되기 때문이다.
