# sim-detective 사례 검토 (SIMDET-CASE-REVIEW-001)

- 작성일: 2026-11-16
- 대상: coding agent, 사용자
- 근거: commit `47b17ba`의 `results/20261115-210426/episodes.jsonl`(Haiku 5.5, Sonnet 5.5)과 `results/20261115-213738/episodes.jsonl`(Opus 5.5)
- 관련 문서: `docs/SIMDET_RESULTS_001.md`

## 1. 성격

- 이 문서는 사후 분석이다. 실행 전에 정한 채점 항목이 아니므로, 여기의 내용은 결론이 아니라 관찰로만 쓴다.
- 채점 규칙, 시나리오, 임계값, prompt는 바꾸지 않는다. 실험을 다시 돌리지 않는다.
- `SIMDET_RESULTS_001.md`의 수치는 `episodes.jsonl`에서 다시 세어 확인했고, 일치한다.

## 2. 요약

1. 조건 A에서 원인을 단정한 28건(Haiku 23, Sonnet 5)은 모두 `soc_offset`을 골랐다. `structural_change`를 고른 경우는 없다.
2. 그 근거는 대부분 같다. 28건 중 18건은 "R2 branch가 있으면 residual이 서서히 변해야 하는데 평평하다"는 이유로 `structural_change`를 배제했다(T1). 기록 전 2,400 s의 전류 이력으로 R2 branch가 이미 포화돼 있다는 점을 빠뜨렸다. 6건은 `structural_change`를 아예 따지지 않았고(T3), 4건은 배제되지 않는다고 쓰고도 단정했다(T2).
3. Sonnet이 기권하면서 `structural_change`를 후보에서 뺀 16건도 10건이 T1이다. 16건 중 10건은 심은 원인이 `structural_change`였다.
4. 포화를 언급했는지와 `structural_change`를 후보로 남겼는지가 거의 일치한다. 맞게 기권하고 `structural_change`를 후보에 넣은 171건은 모두 포화를 언급했다. 단정했거나 `structural_change`를 후보에서 뺀 45건 중 포화를 언급한 것은 5건이고(부분적 언급 2건은 따로), 5건 모두 T2다.
5. 세 model은 추론을 보여 주는 방식이 달랐다. Sonnet 5.5는 조건 A에서 thinking block을 내지 않고 보이는 text block에 추론을 썼다(216건 중 204건, 중앙값 1,490자). Haiku는 thinking block에만, Opus는 양쪽에 썼다. 세 model의 비교는 이 차이를 포함한 비교다.

## 3. 조건 A에서 단정한 28건

### 3.1 고른 원인

| model | 단정 | 답한 원인 | 심은 원인이 SOC0 (우연히 맞음) | 심은 원인이 ST (틀림) |
|---|---|---|---|---|
| Haiku 5.5 | 23 | 모두 `soc_offset` | 10 | 13 |
| Sonnet 5.5 | 5 | 모두 `soc_offset` | 2 | 3 |
| Opus 5.5 | 0 | – | – | – |

- 확신도: Haiku 0.5–0.8 (중앙값 0.7), Sonnet 0.4–0.85.
- Haiku의 23건은 15개 시나리오에 퍼져 있다. 3회 반복이 모두 단정으로 나온 시나리오는 2개(`0ecf604c`, `605ef500`)다.

### 3.2 추론의 유형

28건을 모두 읽고 붙인 유형이다. thinking 요약, text block, `rationale`을 모두 봤다. episode별 유형은 `results/20261115-210426/case_review.csv`에 있다.

| 유형 | 내용 | Haiku | Sonnet | 합 |
|---|---|---|---|---|
| T1 | "offset이 평평하므로 R2가 아니다"로 `structural_change`를 배제. 포화를 언급하지 않음 | 15 | 3 | 18 |
| T2 | `structural_change`가 배제되지 않는다고 쓰고 판정은 `identified` | 3 | 1 | 4 |
| T3 | `structural_change`를 따지지 않음. 한 번도 언급하지 않았거나(5건), 제안한 실험의 결과로만 언급(1건) | 5 | 1 | 6 |

- 단정한 28건 중 포화를 언급한 것은 3건(Haiku 2, Sonnet 1)이고 모두 T2다. Sonnet의 1건은 text block에만 있고 `rationale`에는 없다. T2의 나머지 1건(Haiku)은 "일정 전류에서는 R2도 비슷해 보일 수 있다"는 부분적 언급이다.
- T3는 처음 판에 없던 유형이다. `soc_offset`과 `r0_increase`만 비교하고, 온도로 R0를 지운 뒤 `soc_offset`으로 정했다.
- 따로 표시한 것: "`soc_offset`과 `r0_increase`는 이 data로 가를 수 없다"고 쓰고도 단정한 것이 5건 있다(Haiku 4, Sonnet 1). T1 2건, T3 3건과 겹친다. 유형은 `structural_change`를 어떻게 다뤘는지로만 붙였다.

### 3.3 맞게 기권한 답과의 차이

| model | 맞게 기권 | 포화를 언급 | 언급 없음 |
|---|---|---|---|
| Haiku 5.5 | 49 | 48 | 1 (후보 `{R0, SOC0}`) |
| Sonnet 5.5 | 67 | 53 | 14 (모두 후보 `{R0, SOC0}`. 그중 1건은 부분적 언급) |
| Opus 5.5 | 72 | 72 | 0 |

- 세는 방법: thinking 요약, text block, `rationale`에서 R2 branch를 말하는 문장에 포화 표현("saturated", "settled", "fully charged", "steady state", "exp(-8)" 등)이 있는지를 정규식으로 찾았다. 걸리지 않은 22건은 직접 읽어 판정했고, 그중 7건이 다른 표현으로 포화를 언급했다. 정규식에 걸렸는데 `structural_change`를 후보에서 뺀 2건도 직접 읽었다. 그 밖에 정규식에 걸린 것은 따로 읽지 않았다.
- `structural_change`를 후보에 넣은 기권 171건(Haiku 48, Sonnet 51, Opus 72)은 모두 포화를 언급했다.
- Sonnet의 53건 중 적어도 11건은 text block에만 있고 `rationale`에는 없다. Haiku의 4건은 thinking 요약에만 있다.

### 3.4 대표 사례

- **T1, Haiku, `605ef500` (심은 원인 ST, 확신도 0.8)**: "R2 > 0 would make the residual relax with a 300 s time constant rather than hold flat."
- **T1, Sonnet, `a64582a6` (심은 원인 SOC0, 확신도 0.7)**: "The offset is already present at t=2400, which argues against structural_change (R2 would grow over ~300 s)."
- **T2, Haiku, `c3f80a56` (심은 원인 SOC0, 확신도 0.5)**: "It is also consistent with a small R2 (... saturated after 2400 s of history), so structural_change is not excluded. ... the steady offset alone cannot distinguish these three causes." 판정은 `identified`.
- **T3, Haiku, `b362f66c` (심은 원인 ST, 확신도 0.8)**: thinking 요약과 `rationale` 어디에도 `structural_change`나 R2가 나오지 않는다. "Alternatives fit poorly: r0_increase would need r0_scale ≈ 1.21 ... A temperature bias would need about +7 K".
- **기권, Opus (심은 원인 SOC0)**: "A second RC branch with R2 of about 0.7 mOhm (tau 300 s, fully charged after 2400 s) gives the same constant offset and also adds no heat. These two cannot be told apart under constant current."

## 4. Sonnet의 기권 후보

조건 A에서 Sonnet이 맞게 기권한 67건의 후보는 다음과 같다.

| 후보 | 건수 | 내용 |
|---|---|---|
| `{R0, SOC0, ST}` | 50 | 포화는 짚었다. 온도로 R0를 배제하지 않았다 |
| `{R0, SOC0}` | 16 | ST를 뺐다. 유형은 T1 10건, T2 2건, T3 4건. 심은 원인은 ST 10건, SOC0 6건 |
| `{SOC0, ST}` (oracle과 같음) | 1 | |

- **16건이 더 중요하다.** 채점은 `correct_abstain`이지만, 10건에서는 심은 원인이 후보에 없다. 내용상으로는 3장의 단정과 같은 오류다.
- **16건의 유형.** T1이 10건이다(심은 원인 ST 8, SOC0 2). T3 4건은 `structural_change`를 언급하지 않았다. T2 2건(`919757b6`, `cc86d2dd`)은 text block에 "2,400 s 뒤라 R2 branch가 이미 자리 잡아 평평한 offset과 구분되지 않는다"고 쓰고, `rationale`에서는 "평평하므로 R2가 아니다"로 뺐다. T1 중 1건(`98acedd6`)은 "R2의 과도 구간은 대부분 지났겠지만 drift가 조금은 남을 것"이라고 썼다. 2,400 s는 시정수의 8배라 남는 것이 없다.
- **50건은 성격이 다르다.** R0를 배제하려면 "저항이 그만큼 늘었다면 온도가 0.2–0.6 K 더 높아야 한다"는 계산이 필요하다. Opus는 이 계산을 적고 R0를 지웠다. Sonnet은 온도가 같다는 것을 `temp_sensor_bias`의 배제에만 썼다.
- Sonnet은 R0가 실제로 심어진 CC 시나리오에서는 18번 중 17번을 맞혔다. R0가 있을 때 알아보는 것과, 없을 때 없다고 판단하는 것이 다르게 나타났다.

비교: Haiku는 기권 49건 중 33건이 `{SOC0, ST}`, 15건이 `{R0, SOC0, ST}`, 1건이 `{R0, SOC0}`이다. Opus는 72건 중 69건이 `{SOC0, ST}`, 3건이 `{R0, SOC0, ST}`이다.

## 5. thinking의 차이

설정은 세 model이 같다 (adaptive thinking, effort medium, 요약 표시). 길이는 글자 수의 중앙값이고, 해당 block이 없는 episode는 0으로 넣었다.

| model | 조건 | thinking block이 있는 episode | thinking 요약 길이 | text block이 있는 episode | 보이는 text 길이 | `rationale` 길이 | 출력 token |
|---|---|---|---|---|---|---|---|
| Haiku 5.5 | A | 216 / 216 | 2,537 | 0 / 216 | 0 | 972 | 2,675 |
| Haiku 5.5 | B | 216 / 216 | 2,581 | 0 / 216 | 0 | 951 | 2,724 |
| Sonnet 5.5 | A | 0 / 216 | 0 | 204 / 216 | 1,490 | 467 | 950 |
| Sonnet 5.5 | B | 97 / 216 | 0 | 141 / 216 | 840 | 461 | 834 |
| Opus 5.5 | A | 216 / 216 | 814 | 152 / 216 | 1,660 | 885 | 1,555 |
| Opus 5.5 | B | 216 / 216 | 797 | 41 / 216 | 0 | 948 | 1,305 |

- **세 model은 추론을 보여 주는 방식이 달랐다.** Haiku는 thinking block에만 썼다. Sonnet은 조건 A에서 thinking block 없이 `submit` 앞의 text block에 썼다. Opus는 양쪽에 썼다.
- Sonnet이 추론을 하지 않은 것은 아니다. 다만 출력량이 셋 중 가장 적고(출력 token 중앙값 950), `rationale`도 가장 짧다.
- thinking 요약은 요약본이고 text block은 원문이다. 세 model의 기록을 같은 기준으로 비교할 수 없다. `rationale`만 보면 Sonnet의 추론이 빠진다(3.3에서 포화 언급 가운데 적어도 11건이 text block에만 있었다).
- 4장의 후보 문제가 추론 방식이나 양의 차이에서 생긴 것인지는 이 data로 알 수 없다.
- 추론의 양으로 순서가 설명되지는 않는다. Haiku는 출력이 가장 많고 32%를 단정했고, Sonnet은 가장 적고 7%를 단정했다.

## 6. 조건 B에서 Sonnet이 실험을 하지 않은 15건

원인을 가를 수 없는 72 episode를 실험 여부와 thinking 여부로 나눈 것이다.

| 실험 | thinking block | 건수 | 판정 |
|---|---|---|---|
| 함 | 있음 | 51 | 모두 정답 |
| 함 | 없음 | 6 | 모두 정답 |
| 안 함 | 없음 | 7 | 기권 (실험 없이 `not_identifiable` 제출) |
| 안 함 | 없음 | 1 | 단정 (`soc_offset`) |
| 안 함 | 있음 | 7 | 단정 (`soc_offset`) |

- 실험을 하지 않고 단정한 8건은 모두 `soc_offset`이다. 8건을 모두 읽었고 T1이 7건, T3가 1건이다. 포화를 언급한 것은 없다. 그중 7건은 thinking block이 있었다. thinking block이 있어도 같은 오류가 나왔다.
- Haiku가 조건 B에서 실험 없이 단정한 2건은 T1 1건, T3 1건이다.
- 실험을 하지 않고 기권한 7건은 "rest test를 하면 가를 수 있다"고 `next_experiment`에 적고도 실험을 요청하지 않았다.

## 7. 해석할 때의 주의

1. 유형 분류는 coding agent가 대상 54건(조건 A 단정 28, Sonnet의 `{R0, SOC0}` 기권 16, 조건 B 단정 10)을 읽고 붙인 것이다. 한 번 읽은 결과이고 두 번째 검토자는 없다. thinking 요약은 R2 branch, 포화, 전류 이력을 말하는 문단을 골라 읽었고, text block과 `rationale`은 전문을 읽었다. 3.3의 포화 언급은 정규식과 읽기를 섞어 셌다.
2. thinking은 요약본이다. model이 실제로 한 추론과 다를 수 있다. 유형은 thinking 요약, text block, `rationale` 가운데 한 곳에라도 근거가 있으면 그에 따라 붙였다.
3. 가를 수 없는 경우가 한 종류(SOC0와 ST)이므로, T1은 이 시나리오 set에 특유한 오류일 수 있다.
4. "포화를 떠올리면 기권하고, 떠올리지 못하면 단정한다"는 것은 관찰된 상관이다. 인과를 보이려면 12장의 실험이 필요하다.

## 8. `SIMDET_RESULTS_001.md`에 반영할 것

채점 결과와 표는 건드리지 않는다. 다음만 추가한다.

1. **4장 "한계"에 한 항목 추가**: 세 model은 추론을 보여 주는 방식이 달랐다. Sonnet 5.5는 조건 A에서 thinking block 없이 text block에 추론을 썼고(204 / 216), Haiku는 thinking block에만, Opus는 양쪽에 썼다. 설정은 같았다. model 사이의 비교는 이 차이를 포함한다.
2. **3장 "보조 관찰"에 추가**:
   - 조건 A에서 단정한 28건은 모두 `soc_offset`이다. 3.2의 유형 표.
   - Sonnet이 `structural_change`를 후보에서 뺀 16건 중 10건은 심은 원인이 `structural_change`였다.
   - 조건 B에서 Sonnet이 실험 없이 단정한 8건 중 7건은 thinking이 있었다.
3. **3장 결론 4의 문장 수정**: "Sonnet의 resolved가 낮은 것은 72번 중 15번에서 실험을 하지 않았기 때문이다(7번은 기권, 8번은 단정)"는 그대로 두고, 6장의 표를 참조로 붙인다.
4. **5장 "다음 버전"에 한 행 추가**: 12장의 실험.
5. 이 문서를 `docs/SIMDET_CASE_REVIEW_001.md`로 넣고 `SIMDET_RESULTS_001.md`에서 참조한다.

## 9. coding agent가 할 일

1. 8장의 내용을 `docs/SIMDET_RESULTS_001.md`에 반영한다.
2. 3.2와 3.3의 건수를 전수 읽기로 확정한다. 조건 A에서 단정한 28건과 Sonnet의 `{R0, SOC0}` 16건이 대상이다. 각 episode에 유형(T1, T2, 그 외)을 붙인 표를 `results/20261115-210426/case_review.csv`로 저장한다. 이 문서의 건수와 다르면 이 문서의 표를 고치고 차이를 적는다.
3. 이 문서의 5장과 6장 표를 `episodes.jsonl`에서 다시 계산해 확인한다.
4. README의 결과 요약에 5장의 한계 한 줄을 넣는다.
5. 실험을 다시 돌리지 않는다. API를 호출하지 않는다.
6. commit과 push는 사용자가 요청할 때만 한다.

## 10. 확인된 사실

아래는 근거가 확인된 사실의 목록이다.

- 원인이 data에 드러나는 48개 시나리오에서 세 model의 정답률은 99–100%다.
- 원인을 가를 수 없는 24개 시나리오에서 원인을 단정한 비율은 Haiku 5.5 32% [17, 52], Sonnet 5.5 7% [2, 24], Opus 5.5 0% [0, 14]다 (95% 구간, 같은 설정).
- 단정한 28건은 모두 같은 원인을 골랐다.
- 그 다수는 "평평한 offset은 두 번째 RC branch가 아니다"라는 근거였고, 주어진 전류 이력에서 그 branch가 이미 포화돼 있다는 점을 쓰지 않았다 (사후 분석).
- simulator가 정답과 "가를 수 없음"을 계산으로 보증하기 때문에, 틀린 답을 추론 단계까지 추적할 수 있었다.
- 우연히 맞은 단정 12건(Haiku 10, Sonnet 2)은 SOC0를 알아본 것이 아니다. 단정은 항상 `soc_offset`이었고, 심은 원인의 절반이 SOC0였다.
- 한계: 모호함이 한 종류, 가를 수 없는 시나리오 24개, prompt와 effort 하나, 세 model이 추론을 보여 주는 방식이 달랐다(Sonnet은 조건 A에서 thinking block 없이 text로 추론).

## 11. 쓰면 안 되는 표현

- "큰 model일수록 정직하다", "Opus는 overclaim하지 않는다": 24개 시나리오와 한 종류의 모호함으로는 말할 수 없다.
- "Sonnet은 무엇이 헷갈리는지 모른다": 추론을 보여 주는 방식과 양이 다른 조건의 결과다. 같은 Sonnet이 51건에서는 포화를 짚고 `structural_change`를 후보에 넣었다.
- "Sonnet은 thinking을 하지 않았다": thinking block이 없었을 뿐이고, text block에 추론을 썼다.
- "우연히 맞은 단정은 절반쯤 맞힌 것이다": 단정은 항상 같은 원인을 골랐다(3.1).
- "model이 포화를 이해하지 못한다": 기권한 답의 다수는 포화를 정확히 썼다. 같은 model이 어떤 episode에서는 쓰고 어떤 episode에서는 쓰지 않았다.

## 12. 다음 버전에서 할 실험 (지금 하지 않는다)

**포화 여부를 바꾸는 대조 실험.** 같은 심은 원인과 같은 크기에서 사전 구간의 길이만 바꾼다.

| 조건 | 사전 구간 | R2 branch | oracle의 판정 |
|---|---|---|---|
| 짧음 | 예: 0–300 s | 관측 구간 안에서 변함 | SOC0와 ST를 가를 수 있음 |
| 김 | 2,400 s (현재) | 포화 | 가를 수 없음 |

- 볼 것: 같은 model이 짧은 조건에서는 원인을 맞히고, 긴 조건에서는 기권으로 바꾸는가.
- T1("평평하면 ST가 아니다")을 규칙처럼 쓰는 model은 두 조건 모두에서 같은 답을 낼 것이다. 전류 이력을 실제로 쓰는 model은 답을 바꿀 것이다.
- 이 실험은 별도의 시나리오 set과 사전 등록으로 한다. 지금 결과와 섞어 집계하지 않는다.
- **먼저 확인할 조건.** 사전 구간을 줄이면 포화 여부만 바뀌지 않는다. 기록 구간의 SOC와 cell 온도도 달라진다. 짧은 조건이 실제로 가를 수 있는지는 oracle로 먼저 계산하고, SOC0와 ST 쌍의 delta chi2 감사를 두 조건 모두에 돌린다. 두 조건의 residual 크기가 비슷하도록 크기도 다시 보정한다.
- 추론 표시 방식을 맞춘 조건(예: 세 model 모두 thinking block을 쓰게 한 조건)을 함께 두면 5장의 교란도 분리할 수 있다.

## 13. 변경 기록

### 2026-11-16, coding agent (9장 작업)

`episodes.jsonl`에서 다시 세고, 대상 episode를 읽은 뒤 고쳤다. API는 호출하지 않았다.

**확인하고 그대로 둔 값**: 3.1의 표, 4장의 후보 건수(50 / 16 / 1), 5장의 thinking block 수와 출력 token과 `rationale` 길이, 6장의 표.

**달라진 값**

| 곳 | 처음 | 고친 뒤 | 이유 |
|---|---|---|---|
| 3.2 T1 (Haiku / Sonnet) | 13 이상 / 3 이상 | 15 / 3 | 전수 읽기 |
| 3.2 T2 | 4 / 1 | 3 / 1 | T2를 `structural_change`에 대한 것으로 한정했다. "R0와 SOC0를 가를 수 없다"고 쓰고 단정한 5건은 따로 표시했다 |
| 3.2 그 외 | 6 이하 / 1 이하 | T3 5 / 1 | "T1의 다른 표현"이 아니라 `structural_change`를 따지지 않은 경우였다. 유형 T3를 새로 뒀다 |
| 3.2 단정 중 포화 언급 | 2건 | 3건, 부분적 언급 1건 | Sonnet 1건이 text block에만 있었다 |
| 3.3 Haiku | 40 / 49 | 48 / 49 | thinking 요약과 다른 표현을 포함 |
| 3.3 Sonnet | 34 / 67 | 53 / 67 | text block과 다른 표현을 포함 |
| 3.3 Opus | 45 / 72 | 72 / 72 | 다른 표현을 포함 ("fully charged", "settled", "8 time constants" 등) |
| 4장 16건의 근거 | "T1과 같은 근거" | T1 10, T2 2, T3 4 | 전수 읽기 |
| 6장 실험 없이 단정한 8건 | "읽은 사례의 근거는 T1" | T1 7, T3 1 | 전수 읽기 |

**고친 표현**

- 2장, 5장, 8장 1번, 10장, 11장: "Sonnet은 thinking을 하지 않았다"를 "thinking block 없이 text block에 추론을 썼다"로 바꿨다. 5장의 "짧은 text block"은 사실과 달랐다(중앙값 1,490자).
- 5장 표에 thinking 요약 길이, text block 수, 보이는 text 길이 열을 넣었다.
- 7장 1번, 2번: 분류한 주체와 근거로 삼은 범위를 실제대로 고쳤다.

**추가한 내용**

- 2장 4번: 포화 언급과 `structural_change`를 후보로 남기는 것의 대응.
- 3.4: T3 사례.
- 10장: 우연히 맞은 단정 12건에 대한 사실. 11장: 쓰면 안 되는 표현 2개.
- 12장: 대조 실험 전에 확인할 조건.
- `results/20261115-210426/case_review.csv`: 54건의 episode별 유형.
