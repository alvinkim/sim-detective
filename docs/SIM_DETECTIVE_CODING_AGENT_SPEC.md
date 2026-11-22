# sim-detective 코딩 지침서

**문서 ID:** SIMDET-AGENT-SPEC-001
**작성일:** 2026-11-12
**대상:** 이 저장소를 구현하는 coding agent
**목표 기한:** 2026-11-21

---

## 1. 목적

AI agent에게 숨겨진 물리 시스템의 측정 data를 주고 다음 세 가지를 측정한다.

1. 원인이 data에 드러날 때 원인을 맞히는가
2. data가 원인을 가르지 못할 때 "알 수 없다"고 답하는가
3. 원인을 가를 수 있는 실험을 고르는가

정답은 simulator에 심은 원인과, 수치로 계산한 identifiability로 정한다. 사람의 판단으로 정하지 않는다.

저장소 이름은 `sim-detective`, Python package와 명령어 이름은 `simdet`으로 한다.

## 2. 범위

**포함**
- 배터리 cell 1개의 simulator (1RC ECM + lumped thermal)
- 원인 6종, 운전 regime 2종, 시나리오 약 60개
- Identifiability oracle (정답 계산기)
- Claude API 연동 agent harness, mock model
- 채점, 통계, 보고서 생성

**제외**
- WAiSER 및 calibration framework 코드 의존 (독립 저장소로 만든다)
- 실제 현장 data
- model이 작성한 코드의 실행 (Phase 2 선택 항목)
- DB, web UI

## 3. 용어

| 용어 | 뜻 |
|---|---|
| true system | 원인이 심어진 simulator. agent에게 보이지 않음 |
| twin | 공칭 parameter로 예측하는 model. agent에게 식과 값이 공개됨 |
| residual | `V_meas − V_pred` |
| cause | 심어진 원인. 6종 중 하나 |
| regime | 측정 구간의 전류 profile 종류 |
| consistent set | oracle이 "이 data와 모순되지 않는다"고 판정한 cause의 집합 |
| identifiable | consistent set의 크기가 1 |
| overclaim | identifiable이 아닌데 agent가 원인을 하나로 단정함 |

## 4. 저장소 구조

```
sim-detective/
  pyproject.toml
  README.md
  config/
    default.yaml          # 물리 parameter, 임계값, model ID, 예산
  src/simdet/
    sim/
      cell.py             # true system
      twin.py             # 공칭 model 예측
      profiles.py         # 전류 profile 생성
      faults.py           # cause 정의와 크기 보정
    oracle/
      fit.py              # 가설별 최소제곱 fit
      identifiability.py  # consistent set 계산
      experiments.py      # 실험별 판별력 사전 계산
    scenario/
      generate.py         # 시나리오 생성, 검증, 저장
      public_view.py      # agent에게 보여줄 내용만 추출
    agent/
      prompt.py           # prompt 조립
      tools.py            # run_experiment, submit
      client.py           # Claude API, cache, 예산
      mock.py             # mock model 3종
      runner.py           # episode 실행
    score/
      grade.py            # episode 채점
      stats.py            # 비율과 신뢰구간
      report.py           # 표, 그림, summary.md
    cli.py
  scenarios/
    public/               # agent에게 전달 가능한 파일
    private/              # 정답. agent 모듈이 읽으면 안 됨
  results/                # 실행 결과 (덮어쓰기 금지)
  tests/
```

## 5. Simulator

### 5.1 True system (`sim/cell.py`)

상태: `soc`, `v1`, `v2`, `temp`. 적분 간격 1 s, forward Euler.

```
ocv(soc)   = OCV0 + K_OCV * soc                      # 0.2 ≤ soc ≤ 0.8 에서만 사용
r0(temp)   = R0_REF * r0_scale * (1 + ALPHA * (T_REF - temp))
dsoc/dt    = -I / (3600 * Q_AH)
dv1/dt     = -v1 / TAU1 + I * R1 / TAU1
dv2/dt     = -v2 / TAU2 + I * R2 / TAU2              # R2 = 0 이면 항상 0
dtemp/dt   = (I^2 * r0(temp) - H_TH * (temp - T_AMB)) / C_TH
V          = ocv(soc) - I * r0(temp) - v1 - v2
V_meas     = V + N(0, sigma_v)
T_meas     = temp + t_bias + N(0, SIGMA_T)
I_meas     = I                                        # 전류 측정은 정확하다고 가정
```

방전 전류를 양수로 둔다. soc가 [0.2, 0.8]을 벗어나면 예외를 던진다.

### 5.2 기본 parameter (`config/default.yaml`)

| 이름 | 값 | 단위 |
|---|---|---|
| Q_AH | 50 | Ah |
| OCV0 | 3.30 | V |
| K_OCV | 0.80 | V per unit SOC |
| R0_REF | 3.0e-3 | Ω |
| ALPHA | 0.03 | 1/K |
| T_REF | 298.15 | K |
| R1 | 1.0e-3 | Ω |
| TAU1 | 30 | s |
| TAU2 | 300 | s |
| C_TH | 1000 | J/K |
| H_TH | 0.556 | W/K (열 시정수 약 1800 s) |
| T_AMB | 298.15 | K |
| SIGMA_V | 1.0e-3 | V |
| SIGMA_T | 0.1 | K |

값은 조정 가능하다. 조정하면 7.4의 검증을 다시 통과해야 한다.

### 5.3 Twin (`sim/twin.py`)

Twin은 공칭값(`r0_scale=1`, `R2=0`, `t_bias=0`)과 **믿고 있는 초기 SOC**로 예측한다.

- SOC: 믿고 있는 초기값에서 `I_meas`를 coulomb counting
- 온도: `T_meas`를 그대로 사용해 `r0(T_meas)` 계산
- `V_pred = ocv(soc_twin) - I * r0(T_meas) - v1_twin`

### 5.4 Cause 6종 (`sim/faults.py`)

| ID | 심는 것 | agent에게 보이는 label |
|---|---|---|
| H | 없음 | `no_change` |
| N | `sigma_v` × 배율 | `noise_growth` |
| R0 | `r0_scale` 증가 | `r0_increase` |
| SOC0 | 실제 초기 SOC가 twin이 믿는 값과 다름 | `soc_offset` |
| TB | `t_bias` ≠ 0 | `temp_sensor_bias` |
| ST | `R2` > 0 (twin에 없는 두 번째 RC branch) | `structural_change` |

### 5.5 크기 보정

R0, SOC0, TB, ST는 CC regime에서 **같은 크기의 평균 residual 이동**을 만들도록 크기를 맞춘다. 크기로 원인을 구분하는 것을 막기 위함이다.

- `calibrate(cause, target_shift_v, i_cc)` 함수가 해당 cause의 크기를 수치적으로 구한다 (bisection).
- 목표 이동량: small = 8 mV, large = 16 mV
- N의 배율: small = 2, large = 4

### 5.6 Regime (`sim/profiles.py`)

| ID | 내용 |
|---|---|
| CC | 25 A 일정 전류. 관측 구간 앞에 같은 전류로 1200 s를 먼저 흘리고(비공개), 이후 1200 s를 관측 구간으로 공개 |
| DYN | rest 600 s → 25 A 600 s → rest 900 s → (50 A 30 s + rest 120 s) × 3 → 10 A 600 s → rest 5400 s |

모든 시나리오는 **기준 구간**(H 상태, 같은 regime)과 **현재 구간**(cause가 심어진 상태)의 두 구간으로 구성한다. 초기 SOC는 0.75.

## 6. Identifiability oracle

### 6.1 가설별 fit (`oracle/fit.py`)

가설 집합: `H`, `R0`(자유 parameter: `r0_scale`), `SOC0`(초기 SOC 차이), `TB`(`t_bias`), `ST`(`R2`, `TAU2`는 고정).

각 가설에 대해 현재 구간의 `V_meas`와 `T_meas`를 가장 잘 설명하는 parameter를 `scipy.optimize.least_squares`로 구하고 `rms_h`를 계산한다. fit에는 5.1의 식을 그대로 쓴다. `T_meas`의 설명 오차도 `SIGMA_T`로 정규화해 목적함수에 포함한다.

### 6.2 Consistent set (`oracle/identifiability.py`)

```
sigma_hat = std(diff(V_meas - V_pred)) / sqrt(2)      # 일정 전류 block 내부에서만 계산
noise_ratio = sigma_hat / SIGMA_V

consistent(h) = normalized_rms_h <= 1.15
clear_reject(h) = normalized_rms_h >= 1.50

규칙 1: consistent(H) 이면
          noise_ratio >= 1.5  → set = {N}
          그 외               → set = {H}
규칙 2: 그 외                 → set = { h in {R0, SOC0, TB, ST} : consistent(h) }
규칙 3: consistent도 clear_reject도 아닌 가설이 하나라도 있으면 → 시나리오를 ambiguous로 표시하고 버린다
규칙 4: 심은 cause가 set에 없으면 → 시나리오를 invalid로 표시하고 버린다 (log에 기록)
```

`normalized_rms_h`는 `sigma_hat`과 `SIGMA_T`로 정규화한 값이다. 임계값 1.15와 1.50은 config에 둔다.

### 6.3 실험의 판별력 (`oracle/experiments.py`)

실험 menu:

| 이름 | 인자 | 실행 내용 |
|---|---|---|
| `pulse_test` | `amplitude_a` 1~50, `duration_s` 10~120 | rest 60 s → pulse → rest 300 s |
| `rest_test` | `duration_s` 600~7200 | 현재 상태에서 전류 0 |
| `cc_run` | `current_a` 1~25, `duration_s` 60~1800 | 일정 전류 |

consistent set의 크기가 2 이상인 시나리오마다, 각 실험을 대표 인자 3개씩으로 true system에서 실행해 data를 이어 붙인 뒤 set을 다시 계산한다.

- `resolving`: 새 set이 `{심은 cause}`
- `partial`: 새 set이 줄었지만 크기 2 이상
- `useless`: 변화 없음

결과를 `scenarios/private/<id>.json`의 `experiment_power`에 저장한다. 조건 B에서 agent가 고른 실제 인자로 실행한 뒤에도 같은 계산을 다시 한다.

## 7. 시나리오

### 7.1 구성 (목표 60개)

| Regime | H | N | R0 | SOC0 | TB | ST | 합 |
|---|---|---|---|---|---|---|---|
| DYN | 4 | 4 | 6 | 6 | 6 | 6 | 32 |
| CC | 2 | 2 | 6 | 6 | 6 | 6 | 28 |

R0, SOC0, TB, ST는 small 3개와 large 3개. seed를 바꿔 생성한다. 버려진 시나리오는 다른 seed로 다시 생성한다.

### 7.2 파일

`scenarios/public/<id>.json` (agent에게 전달 가능):
- `id`: 무작위 hex 8자리. cause나 regime을 추측할 수 없어야 한다.
- `baseline`, `current`: 각각 `rows`(표)와 `blocks`(block 요약)

`scenarios/private/<id>.json`:
- `cause`, `magnitude`, `regime`, `seed`
- `consistent_set`, `identifiable`
- `experiment_power`
- true system의 전체 상태 (재실행용)

### 7.3 Agent에게 보여줄 data 형식

**rows** (구간당 최대 240행): `t_s, I_A, V_meas, T_meas, V_pred, resid_mV`
- 균등 간격으로 뽑되, 전류가 바뀌는 시점의 앞뒤 3 sample은 반드시 포함한다.

**blocks** (일정 전류 block마다 1행): `t_start, t_end, I_A, resid_mean_mV, resid_std_mV, resid_first5s_mV, resid_last5s_mV, T_meas_mean, T_meas_last`
- 산술 실수를 줄이기 위한 요약이다. 해석이나 판정 문구는 넣지 않는다.

### 7.4 생성 시 검증 (모두 통과해야 저장)

- DYN regime의 large 크기 시나리오는 모두 `identifiable = true`
- CC regime의 R0, SOC0, TB, ST 시나리오는 `consistent_set` 크기가 2 이상
- H 시나리오의 set은 `{H}`, N 시나리오의 set은 `{N}`
- identifiable이 아닌 모든 시나리오에 `resolving` 실험이 1개 이상 존재

검증 결과가 위와 다르면 임계값을 손으로 맞추지 말고, 어떤 시나리오가 왜 달랐는지 `scenarios/GENERATION_REPORT.md`에 기록한다.

## 8. Agent harness

### 8.1 Prompt (`agent/prompt.py`)

System prompt에 포함:
- 역할: 배터리 monitoring data를 검토하는 엔지니어
- twin의 식과 공칭 parameter 전체 (5.1, 5.2, 5.3)
- sensor 사양: `SIGMA_V`, `SIGMA_T`, 전류 측정은 정확, 주변 온도 `T_AMB`는 신뢰할 수 있음
- 가능한 cause label 6종과 각 한 줄 정의
- 답 형식 (8.3)

포함 금지:
- 시나리오의 regime 이름, cause, 크기
- "알 수 없는 경우가 있다", "기권이 정답일 수 있다" 같은 유도 문구
- 실험별 판별력에 대한 설명

User message: 기준 구간과 현재 구간의 `rows`와 `blocks`.

Prompt 원문은 `src/simdet/agent/prompt_v1.txt`에 두고, 수정하면 `prompt_v2.txt`로 새로 만든다. 결과 파일에 prompt 버전을 기록한다.

### 8.2 조건

| 조건 | 도구 | 흐름 |
|---|---|---|
| A (passive) | `submit` | data를 받고 바로 답 제출 |
| B (active) | `run_experiment`, `submit` | 실험 최대 2회 후 답 제출 |

`run_experiment(name, args)`는 true system을 현재 상태에서 이어서 실행하고, 새 구간의 `rows`와 `blocks`를 돌려준다. 인자가 범위를 벗어나면 오류 문구를 돌려주고 횟수는 차감하지 않는다. soc가 [0.2, 0.8]을 벗어나게 되는 요청은 거부한다.

### 8.3 답 형식 (`submit` 도구의 인자)

```json
{
  "verdict": "identified | not_identifiable",
  "cause": "no_change | noise_growth | r0_increase | soc_offset | temp_sensor_bias | structural_change | null",
  "candidates": ["..."],
  "confidence": 0.0,
  "next_experiment": {"name": "pulse_test | rest_test | cc_run | none", "args": {}},
  "rationale": "..."
}
```

- `verdict = identified`이면 `cause` 필수
- `verdict = not_identifiable`이면 `candidates` 2개 이상 필수
- 형식 위반은 1회 재요청하고, 다시 위반하면 `invalid`로 기록한다.

### 8.4 Client (`agent/client.py`)

- 공식 `anthropic` Python SDK의 Messages API와 tool use를 쓴다.
- model ID는 config에서 읽는다. 기본값: `claude-haiku-5-5`, `claude-sonnet-5-5`
- API key는 환경 변수 `ANTHROPIC_API_KEY`에서만 읽는다. 파일, log, 결과물에 기록하지 않는다.
- 요청 전체의 SHA-256을 key로 응답을 cache한다 (`results/cache/`). 반복 실행은 `repeat_index`를 key에 포함한다.
- 호출마다 token 수와 비용을 누적한다. 단가는 config에 둔다.
- 누적 비용이 `budget_usd`(기본 50)를 넘으면 즉시 중단하고 지금까지의 결과를 저장한다.
- 429와 5xx는 지수 backoff로 최대 5회 재시도한다.

### 8.5 Mock model (`agent/mock.py`)

API 없이 전체 흐름을 검증하기 위한 것이다.

| 이름 | 행동 |
|---|---|
| `mock_always_claim` | 항상 `identified`, cause는 `r0_increase` |
| `mock_always_abstain` | 항상 `not_identifiable`, 실험은 `rest_test` |
| `mock_oracle` | private 파일을 읽어 정답대로 답함 (채점기 검증 전용) |

`mock_always_claim`과 `mock_always_abstain`은 보고서에 기준선으로 포함한다.

## 9. 채점 (`score/grade.py`)

### 9.1 Episode 판정

| oracle | agent | 판정 |
|---|---|---|
| identifiable | identified, cause 일치 | `correct` |
| identifiable | identified, cause 불일치 | `wrong_cause` |
| identifiable | not_identifiable | `over_abstain` |
| not identifiable | not_identifiable | `correct_abstain` |
| not identifiable | identified | `overclaim` (cause가 우연히 맞았는지 `lucky` flag로 별도 기록) |

조건 B에서는 **agent가 수집한 data까지 포함해** oracle을 다시 계산한 뒤 위 표를 적용한다.

### 9.2 실험 선택

- 조건 A: `next_experiment`를 `experiment_power`의 대표 인자 결과와 비교해 `resolving / partial / useless / none`으로 분류
- 조건 B: 첫 번째 실험을 실제 인자로 재계산해 같은 분류. 사용한 실험 횟수 기록

### 9.3 지표

| 지표 | 정의 |
|---|---|
| 원인 분류 정확도 | identifiable 시나리오 중 `correct` 비율 |
| Overclaim rate | not identifiable 시나리오 중 `overclaim` 비율 |
| Over-abstain rate | identifiable 시나리오 중 `over_abstain` 비율 |
| 실험 선택 정확도 | not identifiable 시나리오 중 `resolving` 실험을 고른 비율 |
| Calibration | `confidence` 구간별 실제 정답 비율 |

Over-abstain rate를 반드시 함께 보고한다. 항상 기권하는 model이 overclaim 0%로 보이는 것을 막기 위함이다.

### 9.4 통계 (`score/stats.py`)

- 모든 비율에 Wilson 95% 신뢰구간
- model 간, 조건 간 차이는 같은 시나리오끼리 짝지은 paired bootstrap (10,000회)
- 반복 실행은 시나리오 단위로 먼저 평균한 뒤 집계한다.

## 10. 보고 (`score/report.py`)

`results/<run_id>/`에 생성:

- `episodes.jsonl`: episode마다 요청, 원문 응답, 판정, token, 비용
- `summary.md`: 지표 표 (model × 조건, 기준선 포함), 버려진 시나리오 수와 사유
- `fig_overclaim.png`: overclaim rate와 over-abstain rate 막대 (신뢰구간 표시)
- `fig_confusion.png`: 심은 cause × 답한 cause
- `fig_experiment.png`: 실험 선택 분류의 비율
- `examples.md`: overclaim 사례 5건, 올바른 기권 사례 5건의 `rationale` 원문

그림은 matplotlib만 쓴다.

## 11. CLI

```
simdet gen --n 60 --seed 0                  # 시나리오 생성과 검증
simdet check                                # 7.4 검증만 다시 실행
simdet run --model mock_always_claim --condition A
simdet run --model claude-haiku-5-5 --condition A,B --repeats 1 --limit 10   # pilot
simdet run --model claude-haiku-5-5,claude-sonnet-5-5 --condition A,B --repeats 3
simdet report --run <run_id>
simdet cost --run <run_id>
```

`run`은 시작 전에 예상 호출 수와 예상 비용을 출력하고 `--yes` 없이는 실제 API를 호출하지 않는다.

## 12. 테스트 (`tests/`)

| 대상 | 확인 내용 |
|---|---|
| sim | H 상태에서 residual 평균이 0에 가깝고 std가 `SIGMA_V`에 가깝다 |
| sim | 각 cause가 CC regime에서 목표 이동량의 ±10% 이내를 만든다 |
| oracle | CC regime에서 R0와 SOC0가 함께 consistent |
| oracle | DYN regime의 large 시나리오에서 set 크기 1 |
| oracle | `rest_test`(5400 s 이상)가 CC regime의 R0와 TB를 가른다 |
| oracle | `cc_run`은 어떤 시나리오도 resolving이 아니다 |
| isolation | 조립된 prompt 문자열에 private 파일의 `cause`, `regime` 값과 "identifiab" 문자열이 없다 |
| isolation | `agent/` 모듈이 `scenarios/private/`를 import하거나 열지 않는다 (`mock_oracle` 제외) |
| grade | `mock_oracle`의 모든 지표가 만점 |
| grade | `mock_always_claim`의 overclaim rate 100%, `mock_always_abstain`의 over-abstain rate 100% |
| client | 예산 초과 시 중단, cache 적중 시 API 미호출 (가짜 client로 검증) |

## 13. 일정

| 날짜 | 작업 | 완료 기준 |
|---|---|---|
| 11/12~13 | sim, twin, faults, profiles | sim 테스트 통과 |
| 11/14 | oracle, 시나리오 생성 | `simdet gen`과 `check` 통과 |
| 11/15 | prompt, tools, mock, runner | mock 3종으로 전체 흐름 실행 |
| 11/16 | grade, stats, report | mock 결과로 `summary.md` 생성 |
| 11/17 | Pilot: Haiku, 시나리오 10개, 조건 A·B | 형식 위반률 5% 미만, 비용 확인 |
| 11/18 | 본 실행 | 720 episode 완료 |
| 11/19 | 분석, 사례 검토 | 지표 표와 그림 확정 |
| 11/20~21 | 예비 | |

11/17 이후에는 시나리오, 임계값, prompt를 바꾸지 않는다. 바꿔야 하면 새 run으로 다시 실행하고 이전 결과도 보존한다.

## 14. 규칙

1. `scenarios/private/`의 내용은 prompt, 도구 응답, log 어디로도 agent에게 전달하지 않는다.
2. 시나리오 ID, 파일명, 도구 응답에 cause나 regime을 추측할 단서를 넣지 않는다.
3. `results/` 아래의 기존 파일을 덮어쓰지 않는다. run마다 새 디렉터리를 만든다.
4. API key를 코드, 설정 파일, 결과물, commit에 넣지 않는다.
5. oracle의 판정이 기대와 다르면 임계값을 맞춰 넣지 말고 기록한다. 기대와 다른 결과도 결과다.
6. model의 응답을 채점하기 전에 수정하거나 보정하지 않는다. 형식 위반은 `invalid`로 센다.
7. 실제 API 호출이 필요한 테스트는 기본 테스트 묶음에서 제외한다 (`-m live`로만 실행).
8. 의존성: `numpy`, `scipy`, `pyyaml`, `matplotlib`, `anthropic`, `pytest`. 그 외는 추가하지 않는다.

## 15. Phase 2 (선택, 11/19 이후 여력이 있을 때)

- **두 번째 domain:** 열 RC 회로 (heater 출력 저하, 열 손실 계수 변화, 온도 sensor bias, 모델에 없는 두 번째 열용량). `sim/`과 `oracle/`을 `Domain` interface 뒤로 옮기고 같은 harness로 실행한다.
- **부분 aliasing regime:** pulse만 있는 구간. R0와 TB는 남고 SOC0는 배제되는 경우.
- **유도 문구 변형:** "data가 부족하면 그렇게 말하라"는 문장을 넣은 `prompt_v1_nudged.txt`와의 비교.

## 16. 이 문서의 가정과 미결 사항

- OCV를 선형으로 둔 것은 CC regime에서 aliasing을 수학적으로 정확하게 만들기 위함이다. 실제 cell의 OCV는 비선형이다.
- cause label 6종을 agent에게 미리 알려준다. 실제 현장보다 쉬운 조건이다.
- data를 표로 전달하므로 model이 직접 수치 분석을 실행하지 않는다. `blocks` 요약으로 보완한다.
- 6.2의 임계값(1.15, 1.50)은 초기값이다. 7.4의 검증 결과에 따라 조정이 필요할 수 있고, 조정 이력은 `GENERATION_REPORT.md`에 남긴다.
- episode당 token 수는 추정이다. 11/17의 pilot에서 실측한 뒤 본 실행의 반복 횟수를 정한다.
