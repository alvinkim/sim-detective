# sim-detective

숨겨진 물리 시스템(배터리 cell 1개)의 측정 data를 AI agent에게 주고 다음을 측정한다.

1. 원인이 data에 드러날 때 원인을 맞히는가
2. data가 원인을 가르지 못할 때 그렇게 답하는가
3. (보조) 원인을 가를 수 있는 실험을 고르는가

정답은 simulator에 심은 원인과, 수치로 계산한 identifiability(oracle)로 정한다.

## 문서

뒤의 문서가 앞의 문서와 다르면 뒤의 문서를 따른다.

| 문서 | 내용 |
|---|---|
| [docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md](docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md) | 처음의 설계 |
| [docs/SIMDET_FOLLOWUP_001.md](docs/SIMDET_FOLLOWUP_001.md) | CC의 aliasing을 SOC0와 ST로 확정, 72개 시나리오, 조건 B 지표 |
| [docs/SIMDET_IMPROVEMENT_PROPOSAL_001.md](docs/SIMDET_IMPROVEMENT_PROPOSAL_001.md) | 수정 보완 제안 (P1–P8) |
| [docs/SIMDET_DECISION_001.md](docs/SIMDET_DECISION_001.md), [docs/SIMDET_DECISION_002.md](docs/SIMDET_DECISION_002.md) | 제안에 대한 결정 |
| [scenarios/GENERATION_REPORT.md](scenarios/GENERATION_REPORT.md) | 생성 결과, 검증 수치, 변경 이력 |

## 시나리오

72개다 (DYN 32, CC 40).

- **identifiable 48개.** DYN 전체와 CC의 H, N, R0, TB. 크기는 small / large (residual 이동 8 / 16 mV).
- **not identifiable 24개.** CC의 SOC0 12개와 ST 12개. data만으로는 `{SOC0, ST}` 둘 중 하나로 좁혀지지 않는다. 크기는 6–20 mV에서 cause마다 12등분한 구간에 하나씩 뽑았다. 집계에서는 13 mV 미만(`6-13mV`)과 이상(`13-20mV`)으로 나눈다.

CC regime은 25 A를 2,400 s 흘린 뒤 600 s를 기록한다. 기록 전 2,400 s의 전류는 `history`로 agent에게 주고, 그 구간의 전압과 온도는 주지 않는다.

## 설치

```
python -m venv .venv
.venv\Scripts\python -m pip install -e .[dev]
```

Python 3.10 이상. 의존성은 `numpy`, `scipy`, `pyyaml`, `matplotlib`, `anthropic`, `pytest`뿐이다.

## 사용

```
simdet gen --n 72 --seed 0                  # 시나리오 생성, 7.4 검증, aliasing 감사
simdet check                                # 저장된 시나리오의 oracle 재계산, 검증, 감사
simdet run --model mock_always_claim,mock_always_abstain,mock_oracle,mock_random_experiment --condition A,B
simdet run --model claude-haiku-5-5 --condition A,B --repeats 1          # pilot: 예상 비용만 출력
simdet run --model claude-haiku-5-5 --condition A,B --repeats 1 --yes    # pilot: 실제 호출 (72개 전체)
simdet cost --run <pilot_run_id> --project-repeats 3                     # 실측으로 본 실행 비용과 시간 추정
simdet run --model claude-haiku-5-5,claude-sonnet-5-5 --condition A,B --repeats 3 --yes
simdet report --run <run_id>                # 여러 run을 합치려면 --run a,b
```

- 실제 model을 실행하려면 환경 변수 `ANTHROPIC_API_KEY`가 필요하다. key는 그 변수에서만 읽고 어디에도 기록하지 않는다.
- `run`은 예상 호출 수와 비용을 먼저 출력하고, `--yes`가 없으면 API를 호출하지 않는다.
- 실제 model을 실행하면 기준선 mock 3종(`mock_always_claim`, `mock_always_abstain`, `mock_random_experiment`)이 같은 run에 자동으로 포함된다 (`--no-baselines`로 끔).
- episode는 병렬로 실행한다 (`--workers`, 기본 4). 결과 파일은 정해진 순서로 쓰므로 worker 수와 무관하게 같다.
- 누적 비용이 `agent.budget_usd`(기본 50)를 넘으면 중단하고, 끝난 episode까지 저장한다. 응답은 `results/cache/`에 요청 전체의 SHA-256으로 저장되므로 다시 실행하면 이어서 진행된다.
- `gen`은 검증이나 감사가 하나라도 실패하면 저장하지 않는다. 실패를 기록한 채 저장하려면 `--save-on-check-failure`, 기존 시나리오를 바꾸려면 `--force`.
- 테스트: `pytest`. 실제 API가 필요한 테스트는 `pytest -m live` (조건 A 1 episode, 조건 B는 두 model × thinking 요약 유무. episode당 예산 상한 $0.50).

## 결과물

`results/<run_id>/` (run마다 새 디렉터리, 기존 파일은 덮어쓰지 않는다)

| 파일 | 내용 |
|---|---|
| `episodes.jsonl` | episode마다 원문 응답, 제출한 답, 판정, 실행한 실험, token, 비용, 소요 시간 |
| `summary.md` | 아래 "지표" 참조 |
| `fig_overclaim.png` | overclaim rate와 over-abstain rate (Wilson 95% 구간) |
| `fig_confusion.png` | 심은 cause × 답한 cause |
| `fig_experiment.png` | 고른 실험의 분류 비율 |
| `examples.md` | overclaim 5건, 올바른 기권 5건의 `rationale` 원문 |
| `run.json` | model, 조건, 시나리오 ID, prompt 버전, config 전체, git commit, library 버전 |

`episodes.jsonl`의 `transcript`에는 첫 user message(시나리오 data)를 넣지 않는다. `scenarios/public/<id>.json`을 해당 prompt 버전으로 조립하면 같은 문자열이 나온다.

현재 시나리오로 만든 run만 서로 비교할 수 있다. `results/20261115-031254`(60개 set)와 `results/20261115-035847`(72개, 구간 변경 전)은 이전 시나리오로 만든 mock run이고, 기록으로만 남긴다.

## 지표

- **주 지표.** 조건 A의 overclaim rate와 over-abstain rate, 조건 B의 resolved rate(처음에 not identifiable이던 시나리오 중 실험 뒤 정답을 낸 비율).
- **조건 B의 overclaim rate**는 분모(실험 뒤에도 not identifiable인 시나리오)가 model마다 달라 model 사이 비교에 쓰지 않는다.
- **구간.** 모든 비율에 시나리오 단위 Wilson 95% 구간을 낸다. identifiable 시나리오는 18가지 설계의 noise 반복이므로, 설계 단위로 다시 뽑은 bootstrap 구간을 함께 낸다. identifiable 쪽 결론은 설계 단위 구간으로 쓴다. not identifiable 24개는 크기가 서로 달라 시나리오 단위 구간을 쓴다.
- **쉬운 묶음과 어려운 묶음.** TB는 쉽고(bias가 온도 noise의 35배 / 71배) CC의 small R0는 어렵다(발열로 인한 온도 차이로만 구분). 이 둘을 뺀 열을 따로 낸다.
- **기권의 질.** 올바른 기권에서 후보가 oracle의 set과 같은지, 심은 cause를 포함하는지, 몇 개를 적었는지 집계한다. 판정에는 넣지 않는다.
- **실험 선택은 보조 지표다.** 대표 실험 9개 중 6개가 24개 시나리오 모두에서 resolving이라, 무작위로 골라도 기대값이 87%다. SOC0와 ST는 전류를 바꾸거나 끊기만 하면 갈리기 때문이다. resolving 실험을 고른 경우의 실험 길이를 함께 낸다 (가장 짧은 것은 390 s).

## 구조

```
config/default.yaml       물리 parameter, 임계값, 실험 menu, model ID, 단가, 예산
src/simdet/sim/           true system, twin, 전류 profile, cause와 크기 보정
src/simdet/oracle/        가설별 fit, consistent set, 실험의 판별력, aliasing 감사
src/simdet/scenario/      생성·검증·저장, 공개 view, 숨겨진 world와 실험 환경
src/simdet/agent/         prompt (v1, v2), 도구, Claude client, mock model, episode 실행
src/simdet/score/         채점, 통계, 보고서
scenarios/public/         agent에게 전달 가능한 파일
scenarios/private/        정답 (agent 모듈은 읽지 않는다. mock_oracle만 예외)
```

## 처음 설계와 다른 점

수치와 근거는 [scenarios/GENERATION_REPORT.md](scenarios/GENERATION_REPORT.md)에 있다.

1. **CC regime의 aliasing은 SOC0와 ST 한 쌍이다.** 처음 설계는 CC에서 R0, SOC0, TB, ST가 모두 겹치기를 기대했지만, 그 식 그대로 fit하면 온도 channel이 R0와 TB를 가른다. 이 결과를 확정했고, 7.4의 두 번째 검증을 "CC의 SOC0, ST는 정확히 `{SOC0, ST}`", "CC의 R0, TB는 심은 cause 하나"로 바꿨다. 임계값은 손대지 않았다.
2. **CC의 구간 길이를 바꿨다** (사전 1,200 → 2,400 s, 관측 1,200 → 600 s). 이전 길이에서는 ST의 두 번째 RC branch가 관측 구간 안에서 아직 포화 중이라 SOC0와 통계적으로 구분됐다. `simdet gen`과 `simdet check`가 이 쌍을 delta chi2로 감사한다.
3. **기록 전 전류 이력을 agent에게 준다** (prompt v2). oracle이 쓰는 정보를 agent도 갖게 하기 위함이다.
4. **`normalized_rms`의 channel 결합 방식**을 처음 설계가 정하지 않아 `oracle.rms_mode`로 두었다. 기본값 `max_channel`은 전압과 온도 중 나쁜 쪽을 임계값과 비교한다.
5. **실험은 consistent set을 좁히기만 한다.** 모든 가설이 똑같이 설명하는 data를 덧붙이면 RMS가 희석되어, 기각됐던 가설이 임계값 아래로 돌아올 수 있기 때문이다.
6. **실험 거부 기준**은 true SOC가 아니라 twin의 coulomb counting SOC와 여유 0.05로 판단한다. 거부 여부로 숨겨진 SOC가 새지 않게 하기 위함이다.
7. **`cc_run`은 전류가 25 A가 아니면 resolving이 될 수 있다.** 25 A에서는 항상 useless다.
8. **조건 A의 실험 분류**는 agent가 제안한 인자와 가장 가까운 대표 인자의 결과를 쓴다.
9. **채점 불가(`ungraded`)**: 조건 B에서 다시 계산한 oracle에 회색지대 가설이 남으면 그 episode는 비율의 분모에서 뺀다. 수는 `summary.md`에 나온다.

## 실제 실행 전에 확인할 것

- 실제 API 호출은 이 저장소에서 아직 한 번도 실행하지 않았다. 먼저 `pytest -m live`로 API 경로를 점검한다.
- `agent.thinking_display`는 기본값이 꺼짐(`null`)이다. `summarized`로 켜면 사례 검토에 쓸 추론 요약이 응답에 들어온다. live 테스트에서 두 model이 설정을 받는 것을 확인한 뒤, pilot 시작 전에 켤지 정하고 pilot과 본 실행에서 같은 값을 쓴다.
- 단가(`agent.pricing_usd_per_mtok`)는 2026-11-15에 공식 가격 페이지에서 확인했다. `agent.effort`(기본 `medium`, 두 model에 같은 값)는 실행 전에 확인한다.
- pilot 결과를 본 뒤에는 시나리오, 임계값, 채점 규칙, prompt를 바꾸지 않는다.
- model이 거절했을 때 다른 model로 넘기는 server-side fallback은 켜지 않았다. 측정 대상 model이 바뀌면 안 되기 때문이다.
