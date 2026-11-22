# sim-detective 공개 전 점검

**문서 ID:** SIMDET-PUBLIC-AUDIT
**작성일:** 2026-11-22
**근거:** 공개 준비 지침서 SIMDET-PUBLIC-001
**대상:** `master`의 `fac3933`, 그리고 `git rev-list --all`이 내는 commit 20개 전부 (remote branch 포함)

이 문서는 두 부분이다. 1부(1–7절)는 아무것도 바꾸기 전에 한 점검(P1)이고, 2부(8–12절)는 그 뒤에 한 정리(P2)다.

**Git 이력은 다시 쓰지 않았다.** 2부에서 고친 문장은 현재 파일에서만 바뀌었고, 이전 commit에는 고치기 전의 문장이 남아 있다.

---

# 1부. 점검 (P1)

## 1. 요약

| 항목 | 결과 | 처리 |
|---|---|---|
| 비밀 값 | 없음 | 없음 |
| 회사 자료 | Code, 수치, 고객 정보는 없음. 내부 project 이름이 지침서 한 줄에 있었음 | 8절 |
| 개인 정보 | 파일 내용에는 없음. Commit author의 이름과 이메일은 공개됨 | 그대로 둔다 (사용자 결정) |
| 일정과 관련된 개인적 문구 | 6개 파일, 9개 줄과 절 제목 하나 | 8절 |
| 크기와 불필요한 파일 | 추적 파일 112 MB. Cache와 임시 파일은 추적된 적 없음 | 없음 |
| 재현 | 새 환경에서 설치와 test 성공. 명령 두 개에 주의할 점 있음 | README에 적었다 |

## 2. 비밀 값

**결과: 없음.**

`REVS=$(git rev-list --all)`로 commit 20개 전부를 대상으로 했다.

| 찾은 것 | 명령 | 결과 |
|---|---|---|
| `sk-ant` | `git grep -I -l -e "sk-ant" $REVS` | 0건 |
| `sk-ant` (추가, 삭제 이력) | `git log --all --oneline -S "sk-ant"` | 0건 |
| `ANTHROPIC_API_KEY=` | `git grep -I -n -E "ANTHROPIC_API_KEY\s*=" $REVS` | 0건 |
| `api_key` | `git grep -I -n -i -E "api[_-]?key" $REVS` | 환경 변수를 읽는 code와 "key를 기록하지 않는다"는 문서뿐 |
| `Bearer `, `x-api-key`, `authorization` | `git grep -I -n -i -E ...` | 0건 |
| `.env`, `secret`, `credential`, `.pem`, `.key` 파일 | `git log --all --name-only --format= \| sort -u \| grep -i -E ...` | 0건 |
| 다른 서비스의 key 형식 (GitHub, AWS, Slack, Google, private key) | `git grep -I -l -E "(ghp_...\|github_pat_\|AKIA...\|xox[bap]-\|AIza...\|BEGIN ... PRIVATE KEY)" $REVS` | 0건 |

- **`api_key`가 나오는 곳**: `src/simdet/agent/client.py`(환경 변수 `ANTHROPIC_API_KEY`를 읽는 세 줄), `tests/test_agent.py`, `tests/test_live.py`, README와 지침서의 "환경 변수에서만 읽는다"는 문장.
- **Token처럼 보이는 긴 문자열**: Direction 1의 `results/2026.../episodes.jsonl`에 세 종류가 있다. 모두 인증에 쓰는 값이 아니다.

| Field | 내용 | 길이 |
|---|---|---|
| `transcript[].content[].signature`, `responses[].content[].signature` | API가 thinking block에 붙여 돌려준 서명 | 약 1,500자 |
| `...content[].id`, `tool_use_id` | Tool 호출 ID (`toolu_...`) | 30자 |
| `responses[].request_sha` | 요청 본문의 SHA-256 (cache key) | 64자 |

- 계정 식별 값(`msg_...`, `req_...`, 조직 ID)은 결과 파일에 없다(`git grep -I -l -E "msg_[A-Za-z0-9]{10,}|req_[A-Za-z0-9]{10,}|org-[A-Za-z0-9]{6,}" HEAD -- results`, 0건).
- `results/cache/`(응답 cache)는 `.gitignore`에 있고 추적된 적이 없다.

## 3. 회사 자료

**결과: 회사 code, 내부 수치, 고객 정보는 없다.**

방법: 저자의 직장과 관련된 고유명사(제품 이름, 내부 project 이름, 고객 이름으로 보이는 것)와 `회사`, `사내`, `고객`, `방산`을 `git grep -I -i -l -e "<검색어>" $REVS`로 찾았다. 검색어 목록은 이 문서에 적지 않는다.

| 찾은 것 | 결과 |
|---|---|
| 내부 project 이름 | 지침서 한 곳(`docs/SIMDET_D2_PILOT_SPEC.md`의 "하지 않는 것" 목록)에 이름만 있었다. 내용은 없다. 8절에서 처리했다 |
| 저자가 일하는 제품의 이름 | `docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md` 한 줄. "그 code에 의존하지 않는다"는 문장이다. 그대로 둔다 |
| `회사` | 지침서 4개의 6줄. 모두 "회사 code와 수치를 쓰지 않는다"는 문장이다. 그대로 둔다 |
| 그 밖의 검색어 | 단어로는 0건. 두 검색어가 결과 파일에서 걸렸지만 thinking 서명(base64) 안의 우연한 글자열이었다 (`git grep -I -c -w` 0건) |

## 4. 개인 정보

**결과: 파일 내용에는 없다. Commit author 정보는 공개된다.**

| 찾은 것 | 명령 | 결과 |
|---|---|---|
| 이메일 주소 | `git grep -I -o -h -E "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" $REVS` | 0건 |
| 로컬 경로, PC 사용자 이름 | `git grep -I -n -i -E "C:\\\\|D:\\\\|[A-Z]:/Users|/c/Users|/home/|\\\\Users\\\\|AppData|<사용자 이름>" $REVS` | 0건 |
| 전화번호 | `git grep -I -n -E "01[016789]-[0-9]{3,4}-[0-9]{4}|\+82" HEAD` | 문서 0건. 결과 파일에서 걸린 것은 base64 안의 `+82` 글자열이다 |
| `run.json`의 환경 정보 | `environment` field를 직접 확인 | Git commit, Python version, package version뿐. Host 이름, 사용자 이름, 경로 없음 |

- **Commit author** (`git log --all --format='%an <%ae>' | sort | uniq -c`): 20개 commit 모두 한 사람의 이름과 이메일 주소 하나다(표기가 다른 것이 1건). Committer도 같다. 이 문서에는 주소를 옮겨 적지 않았다.
- **공개하면 그 이름과 이메일을 누구나 볼 수 있다.** 사용자가 그대로 두기로 정했다.
- Commit 20개 모두 message 끝에 `Co-Authored-By: Claude ...` 줄이 있다.
- `sim-detective.code-workspace`가 추적되고 있다. 내용은 `"path": "."`뿐이다.

## 5. 일정과 관련된 개인적 문구

**결과: 6개 파일에 9개 줄과 절 제목 하나가 있었다.**

명령: `git grep -I -n -i -E "<일정, 제출, 발표와 관련된 단어들>" HEAD`.

| 파일 | 있던 것 |
|---|---|
| `docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md` | 목표 기한 줄의 괄호 안 구절 |
| `docs/SIMDET_FOLLOWUP_001.md` | 마감 줄의 괄호 안 구절 |
| `docs/SIMDET_DECISION_001.md` | 문장 2개 |
| `docs/SIMDET_D2_PILOT_SPEC.md` | 목표 기한 줄의 괄호 안 구절, 한 문장의 앞 단어 |
| `docs/SIMDET_CASE_REVIEW_001.md` | 10절의 제목과 안내 문장 |
| `docs/SIMDET_IMPROVEMENT_PROPOSAL_001.md` | "마감"이라는 단어 3곳 |

기술 내용과 무관한 문구다. 8절에서 처리했다.

## 6. 크기와 불필요한 파일

**결과: 문제 없음.**

| 항목 | 명령 | 결과 |
|---|---|---|
| 추적 파일 | `git ls-files \| wc -l`, `git ls-files -z \| xargs -0 du -ch` | 353개, 112 MB |
| `.git` | `du -sh .git`, `git count-objects -vH` | 29 MB |
| 5 MB를 넘는 파일 | `git ls-tree -r -l HEAD \| awk '$4>5000000'` | 8개 (아래) |
| 이력에만 있는 큰 파일 | `git rev-list --objects --all \| git cat-file --batch-check=...` | 없음 |
| 추적되는 cache, 임시 파일 | `git ls-files \| grep -E "__pycache__\|\.pyc$\|\.venv\|results/cache\|\.tmp$\|\.pytest_cache\|egg-info\|\.vscode\|\.claude"` | 0건 |
| 과거에 추적된 적 | `git log --all --name-only --format= \| sort -u \| grep -E ...` | 0건 |

| 크기 | 파일 |
|---|---|
| 22.1 MB | `results/20261115-210426/episodes.jsonl` |
| 13.5 MB | `results/20261115-213738/episodes.jsonl` |
| 11.1 MB | `results/d2_r4/confirm/episodes_S-A.json` |
| 11.1 MB | `results/d2_r4/confirm/episodes_S-B.json` |
| 6.1 MB | `results/20261115-205152/episodes.jsonl` |
| 5.7 MB | `results/d2_pilot/live_haiku/episodes.json` |
| 5.7 MB | `results/d2_pilot/live_sonnet/episodes.json` |
| 5.7 MB | `results/d2_pilot/mock/episodes.json` |

- 가장 큰 파일이 22 MB로 GitHub의 파일 크기 경고선(50 MB)보다 작다.
- `.gitignore`에는 `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `results/cache/`, `*.tmp`, `.env`가 있다. 더할 것이 없다.

## 7. 재현 확인 (정리 전)

방법: `git clone`으로 `fac3933`을 빈 폴더에 받아 새 가상 환경을 만들었다. `ANTHROPIC_API_KEY`는 지운 채로 실행했다. Python 3.13.1.

- 설치(`pip install -e .[dev]`)와 test(125 통과, 5 제외, 1 xfail)가 성공했다.
- `simdet check`, mock 실행, 보고서, Direction 2의 1–3차 명령이 성공했고, 1–3차의 출력은 저장소의 파일과 byte 단위로 같았다.
- **`simdet gen --n 72 --seed 0`은 종료 code 2로 끝난다.** 시나리오가 이미 있으면 거부하는 의도된 동작이다.
- **`python -m simdet.control.r4.feasibility`는 `results/d2_r4/g0/`의 파일 2개를 덮어쓴다.** 그 폴더는 규칙 R9를 넣기 전의 기록이고, 지금의 code는 R9를 포함해 계산한다. 새 출력은 `results/d2_r4/g0_r9/`의 파일과 byte 단위로 같다.

정리 뒤에 다시 한 확인은 11절에 있다.

---

# 2부. 정리 (P2)

## 8. 고친 것

사용자의 결정에 따라 현재 파일만 고쳤다. 기술 내용, 숫자, 판정은 바꾸지 않았다.

| 파일 | 바꾼 것 |
|---|---|
| `docs/SIMDET_D2_PILOT_SPEC.md` | "하지 않는 것"의 내부 project 이름을 "회사 코드와 관련 문서"로 바꿨다. 목표 기한 줄의 괄호 안 구절을 지웠다. 한 문장의 앞 단어 하나를 지웠다 |
| `docs/SIM_DETECTIVE_CODING_AGENT_SPEC.md` | 목표 기한 줄의 괄호 안 구절을 지웠다. 이 파일에서 바꾼 것은 이 한 곳이다 |
| `docs/SIMDET_FOLLOWUP_001.md` | 마감 줄의 괄호 안 구절을 지웠다 |
| `docs/SIMDET_DECISION_001.md` | 문장 2개를 지웠다 |
| `docs/SIMDET_CASE_REVIEW_001.md` | 10절의 제목을 "확인된 사실"로 바꾸고 안내 문장의 앞 문장을 지웠다. 사실 7개는 그대로다 |
| `docs/SIMDET_IMPROVEMENT_PROPOSAL_001.md` | "마감 전에는"을 "지금은"으로, "마감 이후의"를 "이번 버전 이후의"로 바꾸고, 남은 날 수를 적은 문장 하나를 지웠다 |

`git diff --stat`으로 본 변경은 이 6개 파일에서 12줄 추가, 14줄 삭제다.

**새로 만든 것과 옮긴 것**

| 파일 | 내용 |
|---|---|
| `README.md` | 영어로 새로 썼다 |
| `README.ko.md` | 이전의 한국어 README. 맨 위에 영문 README로 가는 링크와, 문서 표에 새 문서 3개의 행을 더했다 |
| `docs/RESULTS_DIRECTION1.md` | Direction 1의 영문 요약 |
| `docs/RESULTS_DIRECTION2.md` | `SIMDET_D2_EXPERIMENT_REPORT_FINAL.md`의 영어판 |
| `docs/README.md` | `docs/`의 영문 색인. 영문 요약 2개를 먼저 가리키고, 한국어 문서를 묶음별로 한 줄씩 설명한다 |
| `LICENSE` | MIT |
| `docs/SIMDET_PUBLIC_AUDIT.md` | 이 문서 |

**바꾸지 않은 것** (`git status --short`로 확인)

- `results/`, `config/`, `src/`, `tests/`, `scenarios/`: 변경 없음.
- 사전 등록(`SIMDET_D2_PREREG.md`, `SIMDET_D2_PREREG_4.md`): 변경 없음.
- 결과 보고서와 차수별 보고서(`SIMDET_RESULTS_001.md`, `SIMDET_D2_RESULTS_001.md`, `SIMDET_D2_RESULTS_004.md`, `SIMDET_D2_G0_REPORT*.md`, `SIMDET_D2_REANALYSIS_001.md`, `SIMDET_D2_EXPERIMENT_REPORT*.md`): 변경 없음.
- `.gitignore`: 변경 없음.

**API 비용 표기**: 한국어 보고서의 비용 숫자는 그대로 두었다. 영문 README와 영문 요약에는 "실행 당시의 공개 단가로 계산한 값"이라는 것과 실행 날짜를 함께 적었다. 계정 정보는 어디에도 없다.

## 9. README 숫자 대조표

영문 `README.md`의 숫자와 출처다. Direction 2의 4차 숫자는 결과 파일(`results/d2_r4/confirm/summary.json`)에서 직접 다시 읽어 확인했다.

**Direction 1**

| README의 숫자 | 출처 파일 | 줄 또는 field |
|---|---|---|
| 72개, 48 / 24 | `docs/SIMDET_RESULTS_001.md` | 11 |
| 3회 반복 | `docs/SIMDET_RESULTS_001.md` | 13 |
| 실행일 2026-11-15 | `README.ko.md` | 46 |
| 정답률 100% [93, 100], 99% [91, 100], 100% [93, 100] | `docs/SIMDET_RESULTS_001.md`, `results/20261115-210426/report_2/summary.md` | 28 / 13, 17, 15 |
| 기권 0% [0, 7], 1% [0, 9], 0% [0, 7] | 위와 같다 | 29 / 13, 17, 15 |
| Overclaim 32% [17, 52], 7% [2, 24], 0% [0, 14] | 위와 같다 | 30 / 13, 17, 15 |
| Resolved 97% [82, 100], 79% [60, 91], 100% [86, 100] | `docs/SIMDET_RESULTS_001.md` | 32 |
| 차이 +25 [+11, +40], +32 [+20, +45], +7 [+2, +13] | `docs/SIMDET_RESULTS_001.md` | 43–45 |
| "5 episodes" | `docs/SIMDET_RESULTS_001.md` | 31, 55 |
| 기준선 100% / 25%, 0% / 0%, 무작위 실험 87% | `docs/SIMDET_RESULTS_001.md` | 50 |
| 단정 28건 (Haiku 23, Sonnet 5), 모두 `soc_offset` | `docs/SIMDET_RESULTS_001.md` | 31, 72 |
| 그중 18건 (T1 15 + 3) | `docs/SIMDET_RESULTS_001.md` | 77 |
| Opus 0 / 24, 상한 14% | `docs/SIMDET_RESULTS_001.md` | 58 |
| 2,400 s, 600 s | `config/default.yaml` | `regimes.CC.pre_s`, `observe_s` |
| 임계값 1.15, 1.50 | `config/default.yaml` | `oracle.consistent_max`, `clear_reject_min` |
| 감사 200 seed | `config/default.yaml` | `scenario.alias_audit.seeds` |
| 비용 $0.79, $12.28, $28.94 | `docs/SIMDET_RESULTS_001.md` | 16 |

**Direction 2**

| README의 숫자 | 출처 파일 | 줄 또는 field |
|---|---|---|
| 판정 기준 50%, 20 pt | `docs/SIMDET_D2_EXPERIMENT_REPORT_FINAL.md`, `config/control_r4_confirm.yaml` | 39 / `criteria` |
| 차수별 표 (100%, 60%, 15%, 40/40, 120/120, 111–120/120) | `docs/SIMDET_D2_EXPERIMENT_REPORT_FINAL.md` | 46–49 |
| S-A: 위반 87/120 (73%), 규칙 77, R9 111, twin 120 | `summary.json` | `settings.S-A.hypotheses.violation_rate_unmonitored` = 0.725, `T0.monitors.{R4,R9,M2}.safety.A10.all.k` = 77, 111, 120 |
| S-B: 위반 79/120 (66%), 규칙 87, R9 120, twin 120 | `summary.json` | `settings.S-B` 같은 field = 0.658, 87, 120, 120 |
| Twin − R9 7.5 pt [3.3, 12.5], 0 pt | `summary.json` | `T0.paired.A10.M2_minus_R9` |
| 35.8 pt, 27.5 pt | `summary.json` | `hypotheses.a.difference_pt` |
| 79%, 100% | `summary.json` | `hypotheses.b.share_of_gap_closed_by_r9` = 0.791, 1.0 |
| 전압 bias −5 mV 34/120, +5 mV 60/120 (S-A) | `summary.json`, `docs/SIMDET_D2_RESULTS_004.md` | `model_errors.v_bias_mv-5`, `v_bias_mv+5`의 `recalibrated.monitors.M2.safety.A10.all.k` / 222, 228 |
| 열 parameter ±30%에서 120/120 | `summary.json`, `docs/SIMDET_D2_RESULTS_004.md` | `model_errors.k±0.3`, `h±0.3` / 214–215 |
| 3.67 A | `docs/SIMDET_D2_REANALYSIS_001.md` | 15 |
| 한계 40 °C, 주변 30–35 °C, heavy 요청 | `docs/SIMDET_D2_RESULTS_004.md` | 75–78 |
| 28–36 pt | `docs/SIMDET_D2_EXPERIMENT_REPORT_FINAL.md` | 19 |
| 표본 10–20, 40, 120 | `docs/SIMDET_D2_EXPERIMENT_REPORT_FINAL.md` | 127 |
| 28,080회, $4.26, $34.26, 2026-11-18 | `docs/SIMDET_D2_EXPERIMENT_REPORT.md` | 281–283, 7 |

**Model 이름**: `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`. `config/default.yaml`의 `agent.models`와 `pricing_usd_per_mtok`, `config/control.yaml`의 `llm_monitor.models`, 결과 파일의 `model` field와 같다.

## 10. 링크

Markdown 링크의 대상 파일과 anchor가 있는지 script로 확인했다.

| 파일 | 내부 링크 | 깨진 것 |
|---|---|---|
| `README.md` | 9 | 0 |
| `README.ko.md` | 29 | 0 |
| `docs/RESULTS_DIRECTION1.md` | 2 | 0 |
| `docs/RESULTS_DIRECTION2.md` | 2 | 0 |
| `docs/README.md` | 26 | 0 |

README의 "Repository layout"에 적은 경로도 모두 있다.

## 11. 재현 확인 (정리 뒤)

방법: 새 clone에 이번에 바꾼 파일을 덮어 놓고, 새 가상 환경에서 영문 README의 명령을 그대로 실행했다. `ANTHROPIC_API_KEY`는 없다. Python 3.13.1, Windows.

| README의 명령 | 결과 |
|---|---|
| `python -m venv .venv`, `.venv\Scripts\python -m pip install -e .[dev]`, activate | 성공 |
| `pytest` | 125 통과, 5 제외, 1 xfail. 133초 |
| `simdet check` | 성공. 모든 항목 PASS |
| `simdet run --model mock_... --condition A,B` | 성공. `results/<run_id>/`를 새로 만든다 |
| `simdet report --run <run_id>` | 성공 |
| `simdet gen --n 72 --seed 0` | 종료 code 2. README에 적은 대로다 |
| `simdet report --run 20261115-210426,20261115-213738` | 성공. `report_3/`을 새로 만들고 기존 파일은 그대로다 |
| `python -m simdet.control.report --run live_haiku --run live_sonnet` | 성공. 추적 중인 파일에 변경 없음 |
| `python -m simdet.control.reanalysis` | 성공. 변경 없음 |
| `python -m simdet.control.r2.feasibility` | 성공. 변경 없음 |
| `python -m simdet.control.r3.feasibility` | 성공. 변경 없음 |
| `python -m simdet.control.r4.feasibility` | 성공. `results/d2_r4/g0/`의 파일 2개가 바뀐다 (README에 적었다) |
| `git checkout -- results/d2_r4/g0` | 위의 변경이 되돌려진다 |
| `python -m simdet.control.r4.confirm` | 성공 (4,089초, 약 68분). `results/d2_r4/confirm/`의 추적 파일이 commit된 것과 byte 단위로 같다 (`git status`에 변경 없음). 판정도 같다: S-A, S-B 모두 "분리 아님", 가설 (a), (b) 성립, (c)는 α와 전압 bias에서만 성립 |
| API를 쓰는 명령 (`--yes` 없이) | 예상 비용만 출력하고 호출하지 않는다 |

"변경 없음"은 실행 뒤 `git status --short results`에 그 파일이 나오지 않는다는 뜻이다. 출력이 저장소의 파일과 byte 단위로 같다.

- macOS와 Linux의 설치 명령은 README에 적었지만 실행해 보지 않았다.
- API를 쓰는 명령은 `--yes`를 붙여 실행하지 않았다.

## 12. 확인 항목

| 항목 | 결과 |
|---|---|
| README의 숫자가 결과 파일 또는 보고서와 일치 | 9절 |
| README의 명령을 새 환경에서 실행 | 11절 |
| README의 내부 링크 | 10절 |
| Test | 125 통과, 1 xfail |
| 실험 결과, config, 사전 등록, 차수별 보고서에 변경 없음 | 8절 |

---

## 13. 공개 후 수정 (2026-11-22, SIMDET-PUBLIC-002)

저장소를 공개한 뒤(`fa204e4`) 외부 검토에서 나온 지적을 고쳤다. 결과 파일, config, code, test, 사전 등록 문서는 바꾸지 않았다. Git 이력도 다시 쓰지 않았으므로, 고치기 전의 문장은 이전 commit에 남아 있다.

| 파일과 줄 | 무엇을 | 왜 |
|---|---|---|
| `docs/RESULTS_DIRECTION2.md` 15줄 | "The twin monitor never lost."로 시작하던 항목을, 범위를 좁힌 문장으로 바꿨다 | 같은 문서의 결과와 어긋났다. 1차의 twin 오차 30% 조건과 4차의 전압 bias ±5 mV 조건에서 twin은 규칙보다 낮았다 |
| `docs/SIMDET_D2_EXPERIMENT_REPORT_FINAL.md` 20–21줄 | 한국어 원문의 같은 항목을 같은 뜻으로 고치고, 바로 아래에 정정 기록 한 줄을 남겼다 | 위와 같다 |
| `README.md` 72줄 | `git clone`의 placeholder를 실제 주소로 바꿨다 | 그대로 실행하면 실패했다 |
| `scenarios/GENERATION_REPORT.md` 77줄 | 수기 기록 앞에 영어 안내 한 줄을 추가했다. 기존 기록은 그대로다 | 수기 기록의 초기 설계 수치(식별 불가 12개)와 위쪽 요약의 최종 수치(24개)가 모순으로 읽힐 수 있었다 |
| `README.md` | 그림(`fig_overclaim.png`)은 넣지 않았다. 한 번 넣었다가 commit 전에 뺐다. 그림 파일은 그대로 있다 | 13.3절 |
| `constraints.txt` (새 파일), `README.md` 85줄 | Test가 통과한 환경의 패키지 버전 34개와 사용법 한 줄 | 설치 시점에 따라 버전이 달라질 수 있다. `pyproject.toml`은 바꾸지 않았다 |
| `README.md` 153줄 (2026-11-23) | "Repository layout" 표의 `scenarios/` 설명에, `private/`가 agent에게 숨기는 정답이고 비공개 자료가 아니라는 말을 넣었다 | 폴더 이름이 "공개하면 안 되는 자료"로 읽힐 수 있었다 |

### 13.1 정정 문장의 대조

| 표현 | 근거 | 결과 |
|---|---|---|
| "±5 mV", "worse than a simple RMS rule" | `SIMDET_D2_RESULTS_004.md` 222, 228, 232줄 | A10 safety(120건 중)가 −5 mV에서 twin 34(S-A), 41(S-B), +5 mV에서 60, 64이다. RMS 규칙(R4)은 77, 87이다. 두 부호, 두 설정 모두에서 twin이 낮으므로 "±5 mV"로 썼다 |
| "30% model error", "one-line tracking rule" | `SIMDET_D2_RESULTS_001.md` 15줄, `SIMDET_D2_REANALYSIS_001.md` 15줄 | Twin 오차 δ = 0.3에서 twin의 safety는 A3 15%(3/20), A2 60%(12/20)이다. 추종 규칙 R1(command와 요청의 차이 3.67 A)은 네 조건의 모든 공격을 막았다. R1은 1차의 사전 등록에 없었고 재분석에서 추가한 규칙이다. 정정 문장에 "added in the reanalysis"(한국어 원문은 "재분석에서 추가한")라고 밝혔다 |
| "stopped all tested attacks" | `results/d2_r4/confirm/summary.json` | 오차 0에서 twin(M2)은 A9, A4, A10 모두 120/120이다. S-A, S-B 같다 |
| "pre-registered 20-point threshold" | `SIMDET_D2_PREREG_4.md` 105줄 | A10에서 twin이 가장 좋은 규칙(R9 포함)보다 20 pt 이상 높으면 "분리됨"이다. 실제 차이는 7.5 pt와 0 pt이다 |

원래 항목의 뒤 문장("다만 매번 같은 safety를 내는 규칙이 있었다")은 새 문장과 겹쳐서 뺐다.

### 13.2 같은 표현의 검색

"never lost", "never lose", "한 번도 지지", "지지 않았다"를 `README.md`, `README.ko.md`, `docs/`의 모든 문서에서 찾았다. 위의 두 곳 외에는 없다.

### 13.3 그림의 숫자

- 조건 A의 막대는 README의 표와 같다. Overclaim 32%, 7%, 0%이고 over-abstain 0%, 1%, 0%이다.
- 그림에는 표에 없는 막대가 있다. 조건 B의 overclaim(Haiku 100%, Sonnet 53%)과 mock 3종이다. 조건 B의 overclaim은 그 model이 실험을 한 뒤에도 식별 불가로 남은 시나리오만 분모로 하므로 model끼리 비교할 수 없다(`report_2/summary.md` 26줄). 처음 읽는 사람이 이 막대를 model 비교로 읽을 수 있어서 그림을 README에 넣지 않았다.

### 13.4 확인

| 항목 | 결과 |
|---|---|
| `results/`, `config/`, `src/`, `tests/`, 사전 등록 문서 | 변경 없음 |
| `scenarios/` | `GENERATION_REPORT.md`에 안내 한 줄과 빈 줄 하나만 추가 |
| 내부 링크 | `README.md` 9, `README.ko.md` 29, `docs/README.md` 26, 영문 요약 2개씩. 깨진 것 0 |
| Test | 125 통과, 5 제외, 1 xfail |
| `constraints.txt` | 새 clone과 새 가상 환경(Windows, Python 3.13.1)에서 `pip install -e .[dev] -c constraints.txt`로 설치해 같은 버전이 깔리는 것과 test 통과를 확인했다 |

패키지 버전은 개발에 쓴 가상 환경의 것이다. 11절의 재현 확인에 쓴 가상 환경은 남아 있지 않아 그 버전과 같은지는 확인하지 못했다.
