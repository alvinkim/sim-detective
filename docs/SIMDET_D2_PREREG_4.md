# sim-detective Direction 2, 4차 plant: 확인 실험 사전 등록

**문서 ID:** SIMDET-D2-PREREG-004
**작성일:** 2026-11-18
**근거:** `docs/SIMDET_D2_FOLLOWUP_003.md`, `docs/SIMDET_D2_G0_REPORT_4.md`(부록 A 포함), 사용자 지시(G0''' 승인)
**상태:** 이 문서가 들어간 commit 이후에 바꾼 것은 모두 결과 보고서의 "Deviations" 절에 시각과 이유를 적는다. API 호출은 0이다.

---

## 1. 이 실험이 무엇인가

G0'''에서 본 결과를 새 seed에서 다시 확인하는 실험이다. Plant, 정책, twin의 추정기, 규칙은 G0'''의 것 그대로이고 더 바꾸지 않는다.

**이 실험은 결과를 본 뒤에 정한 설계의 확인이다.** 아래를 알고 등록한다.

- 1–3차 plant에서는 세 번 모두 "규칙으로 충분함"이었다.
- 4차 설계(직렬 pack, 숨은 설비 상태)는 그 결과를 본 뒤에 정했다.
- 운전 조건(한계 40 °C, 주변 온도 30–35 °C, 운전 여유, heavy 요청)은 공격이 위반을 만들도록 G0'''에서 좁혔다.
- G0'''에서 model 없는 규칙만 비교했을 때는 "분리됨"이었다(A10에서 twin 60/60, 가장 좋은 규칙 34/60).
- 그 뒤 규칙 R9(전압으로 cell 온도를 구해 경보)를 추가해 같은 data로 다시 계산하니 "규칙으로 충분함"으로 바뀌었다(A10에서 twin 60/60, R9 57/60). R9는 그 결과를 본 뒤에 만든 규칙이다.

따라서 새 seed에서 예상하는 주 판정은 "규칙으로 충분함"이다. 가설 (a), (b), (c)는 사용자가 R9의 결과를 보기 전에 정한 문장 그대로 등록한다.

## 2. 고정한 파일

| 파일 | 내용 | git blob |
|---|---|---|
| `config/control_r4.yaml` | Plant, 설비 상태, 요청, 정책, 규칙, twin, threshold (S-A) | `6bbe7f0a` |
| `config/control_r4_confirm.yaml` | 새 seed, episode 수, S-B의 차이, model 오차 조건, 판정 기준 | `ae91d5f4` |
| `src/simdet/control/r4/pack.py` | Pack model | `0d8b430b` |
| `src/simdet/control/r4/plant.py` | Episode 실행 | `70e5e10d` |
| `src/simdet/control/r4/policies.py` | B4, A9, A4, A10 | `a47d1147` |
| `src/simdet/control/r4/estimator.py` | Twin (M2) | `e8eeca57` |
| `src/simdet/control/r4/rule9.py` | R9 | `21ed8588` |
| `src/simdet/control/r4/feasibility.py` | 규칙, threshold, 지표, 판정 | `7e6fd2b4` |
| `src/simdet/control/r4/confirm.py` | 확인 실험 실행과 분석 | `6a7bfcf1` |
| `config/default.yaml`의 `cell` | Cell parameter (수정 없음) | – |

- Blob 값은 `git hash-object`의 앞 8자리다. 이 파일들은 이 commit에 넣지 않았다(사용자 지시: 사전 등록만 먼저 commit). 결과 보고서에서 같은 값인지 확인한다.
- `config/control_r4.yaml`은 G0''' 때의 값에 R9의 parameter 3개(`rules.r9_*`)만 더한 것이다.

## 3. 설정

| 항목 | 값 |
|---|---|
| 설정 | **S-A**(운전 여유 1.0 K)와 **S-B**(운전 여유 1.5 K)를 둘 다 실행하고 나란히 보고한다 |
| Seed | `20261201`. 앞에서 쓴 seed(20261118–20261121)와 다르다 |
| 정상 운전 (B4) | Calibration 200, test 200. 설비 상태 F0 40%, F1, F2, F3 각 20% |
| 공격 | A9, A4, A10 각 120 (F1, F2, F3 각 40). 모두 heavy 요청 |
| 그 밖 | `config/control_r4.yaml` 그대로. 한계 40 °C, 주변 온도 30–35 °C, k 0.1 W/K, 고장 범위 R0 × 1.3–1.8, h × 0.3–0.5 |

Parameter ±30% 설정(k, 고장 범위)은 확인 실험에 넣지 않는다.

**Pipeline 점검에 대해**: 실행 code를 점검하려고 이 seed의 집합별 첫 10건으로 dry run을 한 번 했다. 화면에는 가설별 참/거짓만 나왔고 파일은 쓰지 않았다. 판정 기준은 그 전에 `control_r4_confirm.yaml`에 적어 두었고 dry run 뒤에 바꾸지 않았다.

## 4. Monitor

| ID | 내용 | 분류 |
|---|---|---|
| M0 | 정지하지 않는다 | – |
| R1' | \|plan 평균 − 요청\| | Model 없는 규칙 |
| R1+ | \|plan 평균\| − \|요청\| | Model 없는 규칙 |
| R2 | 두 온도 reading의 최댓값 − 한계 | Model 없는 규칙 |
| R4 | Plan RMS − 주변 온도의 1차식 | Model 없는 규칙 |
| R6 | 전류가 흐를 때의 \|cell 전압 − pack 평균\| 최댓값 | Model 없는 규칙 |
| R7 | Plan RMS × √(pulse R0 배율의 최댓값) − 주변 온도의 1차식 | Model 없는 규칙 |
| R8 | R2 OR R6 OR R7 | Model 없는 규칙 |
| R9 | Pulse의 cell별 R0와 전압-온도 관계식으로 구한 cell 온도의 최댓값 − 한계. 열 model과 예측 없음 | 전기 model을 쓰는 규칙 |
| M2 | Twin이 예측한 최고 cell 온도(plan + 300 s hold) − 한계 | Twin |

- **"Model 없는 규칙"**은 G0'''의 첫 판정에 쓴 7개다. R7은 pulse의 R0 배율을 쓰지만 온도를 추정하지 않으므로 여기에 둔다.
- **"가장 좋은 규칙"**은 R9까지 넣은 8개 중 그 공격에서 safety가 가장 높은 것이다.
- 정의와 parameter는 G0''' 보고서 2.5절, 2.6절, 부록 A.2 그대로다.

## 5. Threshold와 지표

- **Threshold**: Monitor마다 calibration 200건의 episode 최대 점수에서, 정지되는 비율이 5% 이하가 되는 가장 낮은 값이다. R8은 셋에 같은 몫을 주고, 합친 비율이 5%를 넘으면 몫을 0.9배씩 줄인다.
- **R4, R7의 1차식**: Calibration episode별 최댓값을 주변 온도에 최소제곱으로 맞춘다.
- **Violation**: 실제 cell 온도의 최댓값이 한계를 넘는 것. Monitor 없이 끝까지 돌린 궤적에서 구한다.
- **Safety**: 공격 episode 중 위반이 없거나, 위반이 일어나는 plan보다 앞선 checkpoint에서 정지된 비율.
- **False stop**: 정상 test 200건 중 정지된 비율. 설비 상태별로도 보고한다.
- **통계**: Episode가 단위다. 비율에 Wilson 95% 구간, monitor 간 차이에 같은 episode의 paired bootstrap 10,000회(seed 0).
- 설비 상태를 합친 값으로 판정하고, 상태별 값을 함께 보고한다.

## 6. Twin model 오차 조건

Model을 쓰는 monitor(M2와 R9)의 model만 어긋나게 한다. Plant, 정책, 측정 노이즈, episode는 모든 조건에서 같다. 한 번에 parameter 하나만 바꾼다.

| Parameter | 수준 | 적용 | R9 |
|---|---|---|---|
| α (R0의 온도 계수) | 0, ±10, ±20, ±30% | Monitor의 값 = 실제 값 × (1 + e) | 같은 오차를 받는다 |
| k (이웃 cell 전도) | 0, ±10, ±20, ±30% | 위와 같다 | k를 쓰지 않는다. 변하지 않는다 |
| h (nominal 냉각) | 0, ±10, ±20, ±30% | 위와 같다. 모든 cell에 같은 비율 | h를 쓰지 않는다. 변하지 않는다 |
| 전압 sensor bias | 0, ±1, ±2, ±5 mV | Monitor가 받는 cell 전압 6개 모두에 같은 값을 더한다. 시작 pulse와 운전 중 모두 | 같은 bias를 받는다 |

- **부호**: 지시는 크기(10, 20, 30%)만 정했다. 방향에 따라 효과가 다를 수 있어 양쪽을 모두 실행한다. 조건은 24개와 오차 0이다.
- **Threshold (주된 읽기)**: 오차 조건마다 그 model로 계산한 calibration 점수에서 다시 정한다. 운영자는 가진 model로 calibration한다고 본다.
- **Threshold (보조)**: 오차 0에서 정한 threshold를 그대로 쓴 값도 보고한다.
- 나머지 규칙은 model 오차와 무관하므로 값이 변하지 않는다. R6는 공통 bias의 영향을 받지 않는다.

## 7. 판정과 가설

**주 판정** (기준은 G0'''와 같고, 비교 대상에 R9를 넣는다)

- 공격 A10, 오차 0에서, monitor 없음일 때의 위반이 50% 이상이고 M2의 safety가 가장 좋은 규칙(R1'–R9)보다 20 pt 이상 높으면 그 설정은 **"분리됨"**이다. 아니면 **"규칙으로 충분함"**이다.
- S-A와 S-B를 따로 판정한다. 둘이 다르면 "설정에 따라 다름"으로 적는다.
- A9는 같은 계산을 해서 보조로 보고한다. 판정에 쓰지 않는다. A4는 표에만 넣는다.

**가설** (사용자가 정한 문장. 판정 방법은 여기서 정한다)

| | 가설 | 판정 방법 |
|---|---|---|
| (a) | 새 seed에서도 A10에서 twin이 model 없는 규칙보다 20 pt 이상 높다 | A10의 위반이 50% 이상이고, M2 − (model 없는 규칙 7개 중 최고) ≥ 20 pt |
| (b) | R9는 twin과 model 없는 규칙의 사이에 온다 | A10에서 (model 없는 규칙 중 최고) < R9 ≤ M2. R9가 그 간격의 몇 %를 메우는지 함께 보고한다 |
| (c) | 오차가 커지면 twin의 safety가 떨어진다 | Parameter마다: 가장 큰 오차(±30%, ±5 mV 중 나쁜 쪽)에서 M2의 A10 safety가 오차 0보다 10 pt 이상 낮다. 다시 정한 threshold 기준. 네 parameter를 따로 판정한다 |

- (a), (b), (c)는 S-A와 S-B 각각에 대해 판정한다.
- (c)에서는 수준별 safety와 false stop 전체, 그리고 같은 오차에서 M2 − R9를 함께 보고한다.
- **반대로 나와도 그대로 보고한다.** 예: R9가 twin보다 높다, 오차가 커져도 twin이 떨어지지 않는다, 주 판정과 (a)가 엇갈린다.

**함께 보고할 것** (판정에 쓰지 않는다)

- 정지가 위반보다 앞선 시간, 위반하지 않을 episode를 멈춘 수 (M2, R9, R4, R7)
- B4의 위반 수와 한계까지의 여유, 전달한 비율
- Twin과 R9의 온도 추정 오차
- 1–4차의 경과, 좁힌 운전 조건, 시도한 설정 전체

## 8. 하지 않는 것

- 결과를 본 뒤 plant, 정책, 추정기, 규칙, threshold 규칙, episode 수를 바꾸지 않는다.
- 규칙을 묶은 새 monitor(예: R4 OR R9)를 판정에 넣지 않는다. 탐색으로 계산하면 사후 분석이라고 표시한다.
- LLM monitor를 쓰지 않는다.

## 9. 실행

```
python -m simdet.control.r4.confirm
```

결과는 `results/d2_r4/confirm/`에, 보고서는 `docs/SIMDET_D2_RESULTS_004.md`에 쓴다.
