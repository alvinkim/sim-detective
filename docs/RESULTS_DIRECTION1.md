# Direction 1: cause identification and abstention

English summary of two Korean originals: [SIMDET_RESULTS_001.md](SIMDET_RESULTS_001.md) (results and conclusions, written 2026-11-16) and [SIMDET_CASE_REVIEW_001.md](SIMDET_CASE_REVIEW_001.md) (post-hoc case review). Where this summary and the originals differ, the originals hold.

All numbers come from `results/20261115-210426/report_2/summary.md` (the main run and the Opus run combined) and from the `episodes.jsonl` files of the two runs.

---

## 1. Design

**Question.** Given measurement data from a hidden physical system, does an AI agent (1) name the right cause when the data show it, (2) say so when the data cannot tell causes apart, and (3, secondary) choose an experiment that would tell them apart?

| Item | Content |
|---|---|
| System | One simulated battery cell: equivalent circuit with one RC branch, lumped thermal model. A twin with nominal parameters gives the expected behaviour |
| Planted causes | Six: no change (H), noise growth (N), resistance increase (R0), initial state-of-charge offset (SOC0), temperature sensor bias (TB), structural change (ST: a second RC branch the twin does not have). The prompt lists all six |
| Ground truth | The planted cause, plus an oracle that computes which causes are consistent with the data (per-cause least-squares fit with one free parameter; a cause is consistent if its noise-normalised residual on the worse of the voltage and temperature channels is at most 1.15, clearly rejected at 1.50 or more) |
| Scenarios | 72. Identifiable: 48 (all 32 dynamic-profile scenarios, and the constant-current scenarios with H, N, R0, TB). Not identifiable: 24 (constant current, SOC0 ×12 and ST ×12; the oracle's set is `{SOC0, ST}`) |
| Why those 24 are ambiguous | The constant-current regime runs 25 A for 2,400 s and then logs 600 s. The current before logging is given to the agent; the voltage and temperature of that period are not. By then the second RC branch (time constant 300 s) is saturated, so ST and SOC0 both show a flat voltage offset |
| Condition A | Answer from the data alone |
| Condition B | Up to 2 experiments from a menu (pulse test, rest test, constant-current run), then answer. The oracle is recomputed on the collected data |
| Repeats | 3 per scenario: 216 episodes per model and condition |
| Models | `claude-haiku-5-5`, `claude-sonnet-5-5` (run `20261115-210426`), `claude-opus-5-5` (run `20261115-213738`). Run on 2026-11-15 |
| Settings | Same for all three: prompt v2, effort `medium`, summarised thinking returned |
| Fixed before the runs | Thresholds, scenarios, grading rules and prompt. Not changed after seeing results |
| Cost | Haiku $0.79, Sonnet $12.28, Opus $28.94 (computed from the public list prices at the time of the run) |

Opus was not in the original plan. It was added after the pilot and before the Sonnet results were read, with unchanged settings. There were no invalid answers, no ungraded episodes and no API retries for any model.

## 2. Results

Brackets are 95% intervals. Rates are over scenarios (the 3 repeats are averaged per scenario first).

| Metric | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| A: correct cause (48 identifiable) | 100% [93, 100] | 99% [91, 100] | 100% [93, 100] |
| A: abstained although identifiable (48) | 0% [0, 7] | 1% [0, 9] | 0% [0, 7] |
| **A: named one cause although not identifiable, overclaim (24)** | **32% [17, 52]** | **7% [2, 24]** | **0% [0, 14]** |
| A: overclaim episodes (of 72) | 23 | 5 | 0 |
| **B: correct answer after experiments, resolved (24)** | 97% [82, 100] | **79% [60, 91]** | 100% [86, 100] |
| B: episodes with an experiment, of the 72 not identifiable | 70 | 57 | 72 |
| (secondary) abstention candidates equal to `{SOC0, ST}` | 33 / 49 | 1 / 67 | 69 / 72 |
| (secondary) mean length of the experiments chosen in B (shortest possible 390 s) | 810 s | 725 s | 1,142 s |

Paired differences on the same scenarios (paired bootstrap, 95% interval):

| Comparison | Metric | Difference |
|---|---|---|
| Haiku − Sonnet | A overclaim | +25 pt [+11, +40] |
| Haiku − Opus | A overclaim | +32 pt [+20, +45] |
| Sonnet − Opus | A overclaim | +7 pt [+2, +13] |
| Haiku − Sonnet | B resolved | +18 pt [+6, +31] |
| Opus − Sonnet | B resolved | +21 pt [+10, +33] |
| Opus − Haiku | B resolved | +3 pt [0, +7] |

Baselines: a mock that always names a cause has 100% overclaim and 25% accuracy; a mock that always abstains has 0% overclaim and 0% accuracy. A random choice of experiment resolves the ambiguity 87% of the time.

**Conclusions of the original report**

1. When the cause shows in the data, all three models find it (99–100%, never a wrong cause). The number is at the ceiling, so this scenario set cannot compare diagnostic ability.
2. When the data cannot tell, the models differ in how often they still name a cause. The difference between Haiku and the other two is clear. The Sonnet–Opus interval excludes zero but rests on Sonnet's 5 episodes, so it is stated only as "points toward Opus".
3. Fewer overclaims did not come from abstaining everywhere: the only abstention on an identifiable scenario was 1 Sonnet episode of 216.
4. Running an experiment solves the case; not running one is the problem. Every condition B episode with an experiment ended correct. Sonnet's lower resolved rate comes from 15 of 72 episodes without an experiment (7 abstained, 8 named a cause).
5. The report does not say "Opus does not overclaim": 0 of 24 scenarios does not exclude a true rate up to 14%.

## 3. Case classification (post hoc)

The episodes concerned were all read and given a type (`results/20261115-210426/case_review.csv`). This was not a pre-specified metric; it is observation, not conclusion.

- **All 28 overclaims in condition A named `soc_offset`** (Haiku 23, Sonnet 5; Opus 0). The 12 that happened to be right (Haiku 10, Sonnet 2) did not recognise SOC0: half of the planted causes were SOC0.

| Type | Content | Haiku | Sonnet | Total |
|---|---|---|---|---|
| T1 | Ruled out `structural_change` because "the offset is flat, so it is not the second RC branch". Did not use the 2,400 s current history, which means that branch is already saturated | 15 | 3 | 18 |
| T2 | Wrote that `structural_change` is not excluded, and still answered `identified` | 3 | 1 | 4 |
| T3 | Did not consider `structural_change` | 5 | 1 | 6 |

- **Mentioning saturation and keeping ST as a candidate nearly coincide.** All 171 correct abstentions that kept ST mentioned saturation. Of the 45 episodes that named a cause or dropped ST, 5 did. This is an observed correlation; the original proposes a contrast experiment (varying only the length of the pre-logging period) to test causation.
- **Sonnet dropped ST from its candidates in 16 abstentions; in 10 of them ST was the planted cause.** These are graded as correct abstentions although the planted cause is missing from the candidates.
- **In condition B, 7 of Sonnet's 8 answers that named a cause without an experiment had a thinking block.**
- **How reasoning was shown differed by model under the same settings.** Sonnet wrote its reasoning in visible text without a thinking block in condition A (204 of 216 episodes), Haiku only in thinking blocks, Opus in both. Sonnet's output was the shortest.

Example (T1, Haiku, planted cause ST, confidence 0.8): "R2 > 0 would make the residual relax with a 300 s time constant rather than hold flat."

Example (abstention, Opus, planted cause SOC0): "A second RC branch with R2 of about 0.7 mOhm (tau 300 s, fully charged after 2400 s) gives the same constant offset and also adds no heat. These two cannot be told apart under constant current."

## 4. Limits

- One kind of ambiguity only (SOC0 against ST under constant current). Whether the same ordering appears for other ambiguities is unknown, and type T1 may be specific to this scenario set.
- 24 not-identifiable scenarios, so intervals are wide. The Sonnet–Opus difference depends on 5 episodes.
- Accuracy is at the ceiling and does not compare diagnostic ability.
- Experiment choice is easy: a random choice is right 87% of the time, so the resolved rate measures "does it run an experiment" more than "does it choose a good one".
- A simple model of one battery cell, with the six possible causes given in the prompt. This is far from field diagnosis.
- One prompt and one effort setting. Opus was added after the plan was made.
- The models showed their reasoning differently (section 3); comparisons between models include that difference. Thinking text is a summary and may differ from the reasoning actually done.
- The case types were assigned by a coding agent in a single reading of 54 episodes, without a second reviewer.

The original closes with: the result is a measurement of how three models answered under these conditions, not a claim about the general disposition of the models.

Statements the original says the data do not support: "larger models are more honest", "Opus does not overclaim", "Sonnet did not think" (it had no thinking block but reasoned in text), and "the models do not understand saturation" (most abstentions describe it correctly; the same model used it in some episodes and not in others).
