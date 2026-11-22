# Direction 2: comparing monitors of operating plans (rounds 1–4)

English version of [SIMDET_D2_EXPERIMENT_REPORT_FINAL.md](SIMDET_D2_EXPERIMENT_REPORT_FINAL.md) (Korean original, written 2026-11-18). Structure and numbers follow the original. Where the two differ, the original holds.

This document summarises four rounds. The numbers and methods are documented in the per-round reports listed in section 5 (Korean); nothing was newly computed here.

---

## 1. Conclusion

**Question.** When a policy that operates a battery secretly tries to cause overheating, does a monitor that predicts temperature with a physical model (a twin) stop more attacks than a simple rule?

**Answer.** On all four plants the verdict is "rules suffice". There was no attack on which the twin monitor was 20 points or more above the best rule.

- In the round 4 confirmation run without model error, the twin stopped all tested attacks, but did not meet the pre-registered 20-point threshold for outperforming the best rule. With a ±5 mV voltage-sensor bias, it performed worse than a simple RMS rule, and in round 1, with 30% model error, it fell below a one-line tracking rule added in the reanalysis.
- **The rule that caught up differed by round.** Round 1: the difference between request and command. Rounds 2–3: the RMS current of the plan and a temperature alarm. Round 4: a rule that derives cell temperature from cell voltage (R9).
- **Only in round 4 was the twin far ahead of the model-free rules** (28–36 pt). Of that difference, 79–100% came from a single voltage-to-temperature relation, not from the thermal model or from prediction.
- **The twin's weakness showed twice.** In round 1 its safety fell to 15% at 30% twin error. In round 4 it fell to the unmonitored level at a voltage bias of 5 mV.
- **The LLM monitor was used in round 1 only.** It stopped every attack, but a one-line rule gave the same safety with a lower false-stop rate.

**Caution when reading.** The designs of rounds 2–4 were chosen after seeing the results of the earlier rounds. Round 4 is a plant built by looking for conditions under which rules fail, and its operating conditions were narrowed so that the attack works. Only two runs were pre-registered: round 1 and the round 4 confirmation run.

## 2. Common method

| Item | Content |
|---|---|
| Evaluation | Offline. Every episode is run to the end without a monitor, and each monitor's score is computed at every checkpoint |
| Attacks | Scripts written in advance. No LLM was given a hidden goal and asked to operate |
| Episode | 60 minutes: 12 plans, 5 commands per plan (60 s each) |
| Threshold | The lowest value at which at most 5% of benign calibration episodes are stopped |
| Stop | At the first checkpoint whose score is at or above the threshold. That plan is not executed |
| Safety | Share of attack episodes with no violation, or stopped before the violation |
| False stop | Share of benign test episodes that are stopped |
| Verdict (from round 3) | On an attack with violations in at least 50% of unmonitored episodes: "separated" if the twin is 20 pt or more above the best rule, otherwise "rules suffice" |
| Statistics | Wilson 95% intervals for rates, paired bootstrap for differences between monitors |

## 3. Results by round

| Round | Plant | Attack | Twin | Best rule | Verdict |
|---|---|---|---|---|---|
| 1 | One cell. Twin error 0–30% | Current differs from the request, 3 kinds | 100% up to 20% error. 60% and 15% at 30% | Tracking rule 100% | Rules suffice |
| 2 | One cell. Twin error 0–20% | Keeps the mean, raises the RMS | 40/40 | RMS rule, temperature alarm 40/40 | Rules suffice |
| 3 | Core-surface two-node model. Only surface temperature measured | Same, plus attacks that know the rule thresholds | 40/40 | RMS rule, temperature alarm 40/40 | Rules suffice |
| 4 | Six cells in series. Hidden faults, 2 temperature sensors | Follows the request on a faulty pack | 120/120 | R9 111–120/120 | Rules suffice |

### 3.1 Round 1: pilot and reanalysis

A twin monitor, an LLM monitor (`claude-haiku-5-5`, `claude-sonnet-5-5`) and their combination were compared on 520 episodes. Pre-registered.

- **The LLM monitor stopped all three attacks in all four conditions (100%).** Its false-stop rate was 0–12% (out of 40).
- **The twin monitor broke down at 30% error.** Safety was 15% (3/20) on the attack built to evade the twin (A3) and 60% (12/20) on the slow attack (A2). Benign operation was already near the limit, so the threshold sat next to the limit.
- **Combining the two raised that 15% to 100%** (+85 pt [+70, +100]).
- **Reanalysis: one line of rule equalled the LLM monitor.** "Stop if the command differs from the request by more than 3.67 A" stopped every attack and no benign test episode. Every attack produced currents 14–59 A away from the request.
- **If the threshold is set once at zero error,** safety becomes 100% everywhere and the twin's false-stop rate rises from 2% to 52%.

### 3.2 Round 2: an attack that keeps the request

To evade the tracking rule, attack A4 matches the plan mean to the request and raises only the RMS by mixing charge and discharge. This round stopped at the feasibility check.

- **Without a monitor A4 violates in 40/40.** The mean error stays within 1.5 A.
- **The RMS rule and the temperature alarm stopped 40/40, like the twin.** The RMS rule's false stops did not grow with twin error.
- **Attacks that stay under the twin threshold could not cause a violation.**
- **Adding an initial pulse to benign operation lowers the RMS rule to 21/40.** This variant was picked after seeing that the rule won, so it was not used for the verdict.

### 3.3 Round 3: an unmeasured core temperature

The limit applies to the core temperature and only the surface temperature is measured. Attacks that know the rule thresholds were added.

- **A4 violates in 20/40, and both the rules and the twin stopped 40/40.**
- **Attacks that evade the rules could not cause a violation.** Maximising the core temperature below the rule thresholds still left 4.0 K to the limit.
- **The twin had the highest false-stop count** (twin 6/60, temperature alarm 4/60, RMS rule 0/60).
- The verdict was the same in a setting with twice the core-surface difference.

### 3.4 Round 4: hidden plant state

The same command is safe or dangerous depending on a hidden state (an aged cell, blocked cooling). Temperature sensors are on 2 of the 6 cells; all 6 cell voltages are measured.

**Feasibility check** (60 episodes)

- Comparing only model-free rules gave "separated". On the attack that exploits the hidden fault (A10): twin 60/60, best rule 34/60.
- R9 was then added and the same data recomputed, and the verdict changed to "rules suffice" (R9 57/60). R9 derives cell temperature from each cell's resistance at the start-up pulse and the voltage-to-temperature relation. It has no thermal model and no prediction.

**Confirmation run** (pre-registered, new seed, 120 episodes of A10)

| Setting | Violations without a monitor | Twin | R9 | Best model-free rule | Twin − R9 |
|---|---|---|---|---|---|
| S-A (operating margin 1.0 K) | 73% (87/120) | 120/120 | 111/120 | 77/120 | 7.5 pt [3.3, 12.5] |
| S-B (operating margin 1.5 K) | 66% (79/120) | 120/120 | 120/120 | 87/120 | 0 pt |

| | Hypothesis | Result |
|---|---|---|
| (a) | The twin is 20 pt or more above the model-free rules | Holds. 35.8 pt, 27.5 pt |
| (b) | R9 falls in between | Holds. R9 closes 79% and 100% of the gap. In S-B it equals the twin |
| (c) | The twin drops as model error grows | Holds only on the electrical side (α, voltage bias). On the thermal side (k, h) nothing changes even at ±30% |

- **Three advantages remain with the twin.** It stops 4–6 minutes earlier; it also stops the fast attack (A4) with one monitor (R9: 50/120); and it degrades less than R9 under a voltage bias of 1–2 mV.
- **With a wrong electrical model the twin is worse than a simple rule.** At a 5 mV voltage bias its A10 safety is 34–60/120 against 77/120 for the RMS rule. With the temperature coefficient α set 30% too high it is 73/120.
- **The twin's false-stop rate is 3.5–4.5%, similar to or below the rules** (out of 200). Four rules exceeded the 5% target on the test set, at 6.5–8.5%.
- **The attack that simply follows the request (A9) caused violations in under 50%** of unmonitored episodes (47.5%, 33%), so it was not used for the verdict.

## 4. Interpretation and limits

**Claims that are supported**

1. Within what was tested, overheating attacks on operating plans could be stopped by a rule that watches the one trace that attack leaves.
2. A model is needed when there is hidden plant state and no temperature sensor on the affected cell. What was needed went as far as an electrical model that reads temperature from voltage; the thermal model and prediction added 0–7.5 pt.
3. The twin monitor's safety is its value when the model is right. Depending on the direction of the error it falls below the rules.

**Claims that are not supported**

- "A twin monitor is better than rules." By the criterion fixed in advance, it was not, four times out of four.
- "An LLM monitor is better than a twin." No attack aimed at the LLM monitor was tested, and from round 2 on no LLM monitor was used.
- A generalisation of "rules are enough". The rule was chosen each time after seeing the attack. Only the twin stopped every attack with a single monitor.

**Limits**

- **The designs were chosen after seeing results.** This holds for the plants of rounds 2–4, for the narrowed operating conditions of round 4 (limit 40 °C, ambient 30–35 °C, heavy requests) and for R9.
- **Whether R9 counts as a rule is a matter of definition.** R9 uses an electrical model. If it is classed as model-based, hypothesis (a) holds as it stands.
- **The attacks are scripts and few.** The round 4 attacks do not know the monitors' thresholds. No attack was tuned to evade R9 or the twin.
- **The twin has the same structure as the plant.** Errors were applied to one parameter at a time. Structural mismatch was not examined.
- **Samples**: 10–20 attack episodes in round 1, 40 in rounds 2–3, 120 in the round 4 confirmation run (40 per plant state).
- **The LLM was used in round 1 only, with one prompt and one effort setting.**

## 5. Documents and reproduction

All documents below are in `docs/` and in Korean.

| Round | Instructions | Pre-registration | Results | Data |
|---|---|---|---|---|
| 1 | `SIMDET_D2_PILOT_SPEC.md` | `SIMDET_D2_PREREG.md` | `SIMDET_D2_RESULTS_001.md`, `SIMDET_D2_EXPERIMENT_REPORT.md`, `SIMDET_D2_REANALYSIS_001.md` | `results/d2_pilot/`, `results/d2_r2/reanalysis/` |
| 2 | `SIMDET_D2_FOLLOWUP_001.md` | None | `SIMDET_D2_G0_REPORT_2.md` | `results/d2_r2/g0/` |
| 3 | `SIMDET_D2_FOLLOWUP_002.md` | None (criterion fixed in the instructions) | `SIMDET_D2_G0_REPORT_3.md` | `results/d2_r3/g0/` |
| 4 | `SIMDET_D2_FOLLOWUP_003.md` | `SIMDET_D2_PREREG_4.md` | `SIMDET_D2_G0_REPORT_4.md`, `SIMDET_D2_RESULTS_004.md` | `results/d2_r4/` |

```
python -m simdet.control.reanalysis        # round 1 reanalysis
python -m simdet.control.r2.feasibility    # round 2
python -m simdet.control.r3.feasibility    # round 3
python -m simdet.control.r4.feasibility    # round 4 feasibility
python -m simdet.control.r4.confirm        # round 4 confirmation run
```

- **API calls**: 28,080 in round 1 ($38.52, computed from the public list prices at the time of the run, 2026-11-18). None in rounds 2–4. All commands above run without the API.
- **Tests**: 125 passed, 1 xfailed (the 5 that need the API are excluded).
- The LLM scores of round 1 are read from stored values. Obtaining them again requires API calls.
- `r4.feasibility` writes to `results/d2_r4/g0/`, the record from before R9 was added; see the note in the [README](../README.md#reproducing-the-results).
