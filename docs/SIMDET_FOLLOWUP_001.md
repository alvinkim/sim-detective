# sim-detective 후속 작업 지침 (SIMDET-FOLLOWUP-001)

- 작성일: 2026-11-15
- 대상: coding agent
- 기준 문서: `docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md` (SIMDET-AGENT-SPEC-001)
- 기준 상태: commit `b44eeda`, run `results/20261115-031254` (mock 3종만 실행)
- 마감: 2026-11-21

이 문서와 기준 문서가 다르면 이 문서를 따른다.

## 1. 현재 상태

- pipeline(simulator, oracle, 시나리오 생성, 채점, 보고서)은 완성됐다.
- mock 3종의 결과가 이론값과 일치한다. 채점기는 검증된 것으로 본다.
- 실제 Claude model은 아직 한 번도 호출하지 않았다. 실험 결과는 없다.
- 기준 문서의 가정 하나가 틀렸다. CC regime에서 R0와 TB는 온도 channel로 구분된다. 겹치는 쌍은 SOC0와 ST뿐이다. 근거는 `scenarios/GENERATION_REPORT.md`의 수기 기록에 있다.

## 2. 이미 반영된 변경 (다시 하지 말 것)

| 파일 | 변경 | 이유 |
|---|---|---|
| `config/default.yaml` | `scenario.plan.CC`의 SOC0, ST를 6에서 12로 | not identifiable 시나리오를 12개에서 24개로 늘려 overclaim rate의 신뢰구간을 좁힘 |
| `.gitattributes` | 새 파일. `* text=auto`, `*.png binary` | 줄바꿈(CRLF) 차이만으로 수정된 것처럼 보이던 문제 해결 |

두 변경은 아직 commit되지 않았다. 시나리오도 아직 다시 생성하지 않았다.

## 3. 결정 사항

1. CC의 aliasing은 SOC0와 ST 한 쌍으로 확정한다. 열 model을 숨기거나 발열을 줄여 네 원인을 겹치게 하는 안은 채택하지 않는다.
2. oracle 임계값(1.15, 1.50, noise ratio 1.5)과 `rms_mode: max_channel`, 물리 parameter는 바꾸지 않는다.
3. 기준 문서 7.4의 두 번째 검증("CC의 R0, SOC0, TB, ST가 모두 consistent set 크기 2 이상")은 다음으로 바꾼다.
   - CC의 SOC0, ST 시나리오는 consistent set이 정확히 `{SOC0, ST}`이다.
   - CC의 R0, TB 시나리오는 consistent set이 심은 cause 하나다.
4. 시나리오 수는 72개다 (DYN 32, CC 40. identifiable 48, not identifiable 24).

## 4. 작업

순서대로 진행한다. 각 작업의 완료 기준을 만족해야 다음으로 넘어간다.

### T1. 7.4 검증 수정

- `src/simdet/scenario/generate.py`의 두 번째 검증을 3장 3번대로 바꾼다.
- `tests/test_oracle.py`의 strict xfail("CC에서 R0와 SOC0가 함께 consistent")을 지우고, 새 검증에 맞는 테스트로 바꾼다.
- 완료 기준: 수정 후 `simdet gen`이 `--save-on-check-failure` 없이 저장된다.

### T2. 시나리오 재생성

```
simdet gen --n 72 --seed 0 --force
```

- 완료 기준
  - `scenarios/GENERATION_REPORT.md`에 identifiable 48, not identifiable 24, discarded 0이 나온다.
  - 모든 not identifiable 시나리오에 resolving experiment가 있다.
  - 수기 기록(marker 아래)이 그대로 남아 있다. 그 아래에 이번 변경을 날짜와 함께 덧붙인다.
- 버려진 시나리오나 빈 slot이 생기면 임계값을 조정하지 말고 그 사실을 보고한다.

### T3. 테스트

- 시나리오 개수 60이나 not identifiable 12를 고정해 둔 테스트를 72, 24로 고친다.
- 완료 기준: `pytest`가 전부 통과한다 (`-m live` 제외).

### T4. 보고서에 세부 집계 추가

`summary.md`에 표 하나를 추가한다. model × 조건마다 (regime, cause, size)별 episode 수와 판정 분포를 낸다. 이유는 다음 두 묶음이 전체 지표를 왜곡할 수 있기 때문이다.

- **TB (쉬움)**: `t_bias`가 3.6 K / 7.1 K로 `SIGMA_T`의 35배 / 71배다. cause accuracy를 끌어올린다.
- **CC의 small R0 (어려움)**: 온도 channel RMS 2.4로만 구분된다. agent는 기록 전 1,200 s의 발열을 직접 계산해야 한다. 여기서의 기권은 over_abstain으로 채점된다.

추가로 지표 표에 "cause accuracy (TB 제외)"와 "over-abstain rate (CC small R0 제외)" 두 열을 넣는다. 채점 규칙 자체는 바꾸지 않는다.

- 완료 기준: mock run의 `summary.md`에 새 표와 두 열이 나오고, `tests/test_stats_report.py`에 해당 테스트가 있다.

### T5. 조건 B의 지표 정리

조건 B에서는 agent가 모은 data로 oracle을 다시 계산하므로 overclaim rate의 분모가 model마다 다르다. model 사이 비교에 쓰기 어렵다. 다음과 같이 한다.

- 조건 B의 주 지표를 두 개로 둔다. 분모는 둘 다 "처음에 not identifiable이던 시나리오"로 고정한다.
  - **resolved rate**: 실험 후 최종 판정이 correct인 비율
  - **resolving experiment chosen**: 이미 있는 지표. 그대로 둔다.
- 기존 overclaim rate (B)는 표에 남기되, 분모가 model마다 다르다는 주석을 붙인다.
- 짝지은 차이 표에서 A와 B의 비교, model 사이 B의 비교는 resolved rate로 낸다.
- 완료 기준: mock_oracle B의 resolved rate가 100%, mock_always_claim B가 0%로 나온다.

### T6. 실험 선택의 기준선 확인

`mock_always_abstain`의 "resolving experiment chosen"이 100%다. 이 mock이 어떤 실험을 어떻게 고르는지 확인한다.

- 고정된 실험 하나가 우연히 항상 resolving이라면, 실험 선택 지표가 너무 쉽다는 뜻이다. 그 사실을 `GENERATION_REPORT.md` 수기 기록에 적는다.
- menu의 representative 9개 중 하나를 무작위로 고르는 `mock_random_experiment`를 추가해 기준선으로 쓴다 (seed 고정).
- 완료 기준: `summary.md`에 무작위 선택의 resolving 비율이 나온다. 이 값이 80%를 넘으면 사용자에게 보고하고 지시를 기다린다.

### T7. 단가 확인

`config/default.yaml`의 `agent.pricing_usd_per_mtok`은 확인되지 않은 값이다.

- Anthropic 공식 가격 페이지에서 `claude-haiku-5-5`, `claude-sonnet-5-5`의 input / output 단가와 cache 배수를 확인해 고친다. 출처 URL과 확인 날짜를 주석으로 남긴다.
- 확인할 수 없으면 추측으로 채우지 말고 사용자에게 묻는다.

### T8. 문서 갱신

- `README.md`: `simdet gen --n 60` 예시를 72로, "60개 중 not identifiable 12개"를 72개, 24개로. "설계 문서와 다른 점" 1번에 3장의 결정을 반영한다.
- `docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md`는 고치지 않는다. 차이는 이 문서와 README에만 적는다.

### T9. 실행

1. mock 재실행: `simdet run --model mock_always_claim,mock_always_abstain,mock_oracle,mock_random_experiment --condition A,B`
   - 완료 기준: always_claim A의 overclaim 100% (n=24), always_abstain A의 over-abstain 100% (n=48), oracle A의 accuracy 100%.
2. pilot: `simdet run --model claude-haiku-5-5 --condition A,B --repeats 1 --limit 10` 으로 예상 비용을 먼저 출력한다.
   - **`--yes`를 붙인 실제 호출은 사용자 승인을 받은 뒤에 한다.**
   - pilot에서 볼 것: invalid 비율, episode당 실제 token과 비용, 조건 B의 평균 실험 횟수, `examples.md`의 rationale이 data의 숫자를 인용하는지.
   - invalid 비율이 10%를 넘으면 본 실행을 하지 않고 원인을 보고한다. prompt를 고치면 `prompt_v2.txt`로 새로 만들고 v1은 남긴다. 기권을 암시하는 문구는 넣지 않는다.
3. 본 실행: `simdet run --model claude-haiku-5-5,claude-sonnet-5-5 --condition A,B --repeats 3 --yes`
   - pilot 비용으로 추정한 총액이 `budget_usd`(50)를 넘으면 repeats를 줄이는 안을 사용자에게 제시한다.
4. `simdet report --run <run_id>`

## 5. 규칙

- API key는 환경 변수 `ANTHROPIC_API_KEY`에서만 읽는다. 코드, log, commit, 결과 파일에 쓰지 않는다.
- 결과를 보고 나서 임계값, 물리 parameter, 채점 규칙, prompt를 바꾸지 않는다. 바꿔야 한다고 판단되면 먼저 보고한다.
- `results/`의 기존 run은 지우거나 덮어쓰지 않는다.
- commit과 push는 사용자가 요청할 때만 한다.
- 기대와 다른 결과(예: 두 model의 overclaim rate가 모두 0%에 가깝다)도 그대로 보고한다. 그 경우 시나리오를 더 어렵게 만드는 수정은 하지 않는다.

## 6. 완료 보고에 포함할 것

- 작업별(T1–T9) 완료 여부와 완료 기준의 실제 값
- 최종 지표 표 (model × 조건, 기준선 포함, 95% 구간)
- 총 비용과 API 호출 수
- 버려진 시나리오, invalid 응답, 재시도 횟수
- 이 문서와 다르게 한 점과 그 이유
