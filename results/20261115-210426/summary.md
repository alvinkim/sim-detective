# sim-detective summary

- runs: 20261115-210426
- episodes: 2160, scenarios: 72, prompt version: v2
- Main metrics: overclaim rate and over-abstain rate in condition A; resolved rate in condition B. Experiment choice is a secondary metric (see its baseline below).
- Rates are over scenarios (repeats averaged per scenario first), with Wilson 95% intervals.
- `mock_always_claim`, `mock_always_abstain` and `mock_random_experiment` are baselines.

## Metrics

| Model | Cond. | Cause accuracy (identifiable) | Cause accuracy, TB excluded | Overclaim rate (not identifiable) | Over-abstain rate (identifiable) | Over-abstain rate, CC small R0 excluded | Invalid |
|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | A | 100% [93, 100] (n=48) | 100% [90, 100] (n=36) | 32% [17, 52] (n=24) | 0% [0, 7] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| claude-haiku-5-5 | B | 100% [95, 100] (n=71.3333) | 100% [94, 100] (n=59.3333) | 100% [15, 100] (n=0.666667) | 0% [0, 5] (n=71.3333) | 0% [0, 5] (n=68.3333) | 0% [0, 5] (n=72) |
| claude-sonnet-5-5 | A | 99% [91, 100] (n=48) | 99% [89, 100] (n=36) | 7% [2, 24] (n=24) | 1% [0, 9] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| claude-sonnet-5-5 | B | 100% [95, 100] (n=67) | 100% [93, 100] (n=55) | 53% [19, 85] (n=5) | 0% [0, 5] (n=67) | 0% [0, 6] (n=64) | 0% [0, 5] (n=72) |
| mock_always_abstain | A | 0% [0, 7] (n=48) | 0% [0, 10] (n=36) | 0% [0, 14] (n=24) | 100% [93, 100] (n=48) | 100% [92, 100] (n=45) | 0% [0, 5] (n=72) |
| mock_always_abstain | B | 0% [0, 5] (n=72) | 0% [0, 6] (n=60) | n/a | 100% [95, 100] (n=72) | 100% [95, 100] (n=69) | 0% [0, 5] (n=72) |
| mock_always_claim | A | 25% [15, 39] (n=48) | 33% [20, 50] (n=36) | 100% [86, 100] (n=24) | 0% [0, 7] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| mock_always_claim | B | 25% [15, 39] (n=48) | 33% [20, 50] (n=36) | 100% [86, 100] (n=24) | 0% [0, 7] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| mock_random_experiment | A | 0% [0, 7] (n=48) | 0% [0, 10] (n=36) | 0% [0, 14] (n=24) | 100% [93, 100] (n=48) | 100% [92, 100] (n=45) | 0% [0, 5] (n=72) |
| mock_random_experiment | B | 0% [0, 5] (n=68.3333) | 0% [0, 6] (n=56.3333) | 0% [0, 51] (n=3.66667) | 100% [95, 100] (n=68.3333) | 100% [94, 100] (n=65.3333) | 0% [0, 5] (n=72) |

- In condition B the oracle is recomputed on the data the agent collected. The overclaim rate in B is therefore taken over the scenarios that were still not identifiable after that model's own experiments: its denominator differs by model, so do not compare it between models. Use the resolved rate below.
- TB scenarios are easy (t_bias is 35 or 71 times SIGMA_T) and lift cause accuracy; CC small R0 is hard (separated only by self-heating in T_meas) and an abstention there counts as over-abstain. The two extra columns leave those strata out; grading is unchanged.

## Design-level intervals (identifiable scenarios)

The identifiable scenarios are a few designs (regime, cause, size) repeated with different noise. Here whole designs are resampled (bootstrap), so the interval does not treat the repeats of a design as independent. Quote these intervals for conclusions about the identifiable scenarios.

| Model | Cond. | Cause accuracy | Cause accuracy, TB excluded | Over-abstain rate | Over-abstain rate, CC small R0 excluded |
|---|---|---|---|---|---|
| claude-haiku-5-5 | A | 100% [100, 100] (18 designs) | 100% [100, 100] (14 designs) | 0% [0, 0] (18 designs) | 0% [0, 0] (17 designs) |
| claude-haiku-5-5 | B | 100% [100, 100] (22 designs) | 100% [100, 100] (18 designs) | 0% [0, 0] (22 designs) | 0% [0, 0] (21 designs) |
| claude-sonnet-5-5 | A | 99% [98, 100] (18 designs) | 99% [97, 100] (14 designs) | 1% [0, 2] (18 designs) | 0% [0, 0] (17 designs) |
| claude-sonnet-5-5 | B | 100% [100, 100] (22 designs) | 100% [100, 100] (18 designs) | 0% [0, 0] (22 designs) | 0% [0, 0] (21 designs) |
| mock_always_abstain | A | 0% [0, 0] (18 designs) | 0% [0, 0] (14 designs) | 100% [100, 100] (18 designs) | 100% [100, 100] (17 designs) |
| mock_always_abstain | B | 0% [0, 0] (22 designs) | 0% [0, 0] (18 designs) | 100% [100, 100] (22 designs) | 100% [100, 100] (21 designs) |
| mock_always_claim | A | 25% [6, 48] (18 designs) | 33% [8, 60] (14 designs) | 0% [0, 0] (18 designs) | 0% [0, 0] (17 designs) |
| mock_always_claim | B | 25% [6, 48] (18 designs) | 33% [8, 60] (14 designs) | 0% [0, 0] (18 designs) | 0% [0, 0] (17 designs) |
| mock_random_experiment | A | 0% [0, 0] (18 designs) | 0% [0, 0] (14 designs) | 100% [100, 100] (18 designs) | 100% [100, 100] (17 designs) |
| mock_random_experiment | B | 0% [0, 0] (22 designs) | 0% [0, 0] (18 designs) | 100% [100, 100] (22 designs) | 100% [100, 100] (21 designs) |

## Scenarios that start not identifiable

Both rates are over the scenarios that were not identifiable before any experiment, so the denominator is the same for every model. Resolved = the final answer is judged correct (only possible in condition B, after an experiment that leaves one cause).

| Model | Cond. | Resolved rate | Resolving experiment chosen (secondary) | Mean length of the resolving experiments chosen |
|---|---|---|---|---|
| claude-haiku-5-5 | A | 0% [0, 14] (n=24) | 99% [84, 100] (n=24) | 1152 s (n=71) |
| claude-haiku-5-5 | B | 97% [82, 100] (n=24) | 97% [82, 100] (n=24) | 810 s (n=70) |
| claude-sonnet-5-5 | A | 0% [0, 14] (n=24) | 99% [84, 100] (n=24) | 674 s (n=71) |
| claude-sonnet-5-5 | B | 79% [60, 91] (n=24) | 79% [60, 91] (n=24) | 725 s (n=57) |
| mock_always_abstain | A | 0% [0, 14] (n=24) | 100% [86, 100] (n=24) | 5400 s (n=72) |
| mock_always_abstain | B | 0% [0, 14] (n=24) | 100% [86, 100] (n=24) | 5400 s (n=72) |
| mock_always_claim | A | 0% [0, 14] (n=24) | 0% [0, 14] (n=24) | n/a |
| mock_always_claim | B | 0% [0, 14] (n=24) | 0% [0, 14] (n=24) | n/a |
| mock_random_experiment | A | 0% [0, 14] (n=24) | 85% [66, 94] (n=24) | 1328 s (n=61) |
| mock_random_experiment | B | 0% [0, 14] (n=24) | 85% [66, 94] (n=24) | 1328 s (n=61) |

- Experiment choice is easy on this scenario set: a uniformly random pick among the 9 representative experiments is resolving in 87% of cases (expected value; `mock_random_experiment` is one draw of it). Read "resolving experiment chosen" against that baseline.
- The shortest experiment that resolves every scenario takes 390 s; compare the mean length column with it.
- These scenarios have target shifts spread over a continuous range (one per equal slice of the range for each cause), so scenario-level Wilson intervals are used for them.

## Not identifiable scenarios by cause and size

| Model | Cond. | Cause | Size | Scenarios | Overclaim rate | Resolved rate | Resolving experiment chosen |
|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | A | SOC0 | 13-20mV | 6 | 28% [7, 66] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| claude-haiku-5-5 | A | SOC0 | 6-13mV | 6 | 28% [7, 66] (n=6) | 0% [0, 39] (n=6) | 94% [55, 100] (n=6) |
| claude-haiku-5-5 | A | ST | 13-20mV | 6 | 22% [5, 61] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| claude-haiku-5-5 | A | ST | 6-13mV | 6 | 50% [19, 81] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| claude-haiku-5-5 | B | SOC0 | 13-20mV | 6 | n/a | 100% [61, 100] (n=6) | 100% [61, 100] (n=6) |
| claude-haiku-5-5 | B | SOC0 | 6-13mV | 6 | 100% [8, 100] (n=0.333333) | 94% [55, 100] (n=6) | 94% [55, 100] (n=6) |
| claude-haiku-5-5 | B | ST | 13-20mV | 6 | 100% [8, 100] (n=0.333333) | 94% [55, 100] (n=6) | 94% [55, 100] (n=6) |
| claude-haiku-5-5 | B | ST | 6-13mV | 6 | n/a | 100% [61, 100] (n=6) | 100% [61, 100] (n=6) |
| claude-sonnet-5-5 | A | SOC0 | 13-20mV | 6 | 11% [1, 51] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| claude-sonnet-5-5 | A | SOC0 | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| claude-sonnet-5-5 | A | ST | 13-20mV | 6 | 11% [1, 51] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| claude-sonnet-5-5 | A | ST | 6-13mV | 6 | 6% [0, 45] (n=6) | 0% [0, 39] (n=6) | 94% [55, 100] (n=6) |
| claude-sonnet-5-5 | B | SOC0 | 13-20mV | 6 | 50% [7, 93] (n=1.33333) | 78% [39, 95] (n=6) | 78% [39, 95] (n=6) |
| claude-sonnet-5-5 | B | SOC0 | 6-13mV | 6 | 33% [3, 91] (n=1) | 83% [44, 97] (n=6) | 83% [44, 97] (n=6) |
| claude-sonnet-5-5 | B | ST | 13-20mV | 6 | 75% [15, 98] (n=1.33333) | 78% [39, 95] (n=6) | 78% [39, 95] (n=6) |
| claude-sonnet-5-5 | B | ST | 6-13mV | 6 | 50% [7, 93] (n=1.33333) | 78% [39, 95] (n=6) | 78% [39, 95] (n=6) |
| mock_always_abstain | A | SOC0 | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | A | SOC0 | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | A | ST | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | A | ST | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | B | SOC0 | 13-20mV | 6 | n/a | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | B | SOC0 | 6-13mV | 6 | n/a | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | B | ST | 13-20mV | 6 | n/a | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_abstain | B | ST | 6-13mV | 6 | n/a | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_always_claim | A | SOC0 | 13-20mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | A | SOC0 | 6-13mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | A | ST | 13-20mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | A | ST | 6-13mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | B | SOC0 | 13-20mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | B | SOC0 | 6-13mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | B | ST | 13-20mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_always_claim | B | ST | 6-13mV | 6 | 100% [61, 100] (n=6) | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) |
| mock_random_experiment | A | SOC0 | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 78% [39, 95] (n=6) |
| mock_random_experiment | A | SOC0 | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 89% [49, 99] (n=6) |
| mock_random_experiment | A | ST | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 89% [49, 99] (n=6) |
| mock_random_experiment | A | ST | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |
| mock_random_experiment | B | SOC0 | 13-20mV | 6 | 0% [0, 74] (n=1.33333) | 0% [0, 39] (n=6) | 78% [39, 95] (n=6) |
| mock_random_experiment | B | SOC0 | 6-13mV | 6 | 0% [0, 85] (n=0.666667) | 0% [0, 39] (n=6) | 89% [49, 99] (n=6) |
| mock_random_experiment | B | ST | 13-20mV | 6 | 0% [0, 85] (n=0.666667) | 0% [0, 39] (n=6) | 89% [49, 99] (n=6) |
| mock_random_experiment | B | ST | 6-13mV | 6 | 0% [0, 79] (n=1) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |

## Abstention quality

For episodes judged correct_abstain: how the listed candidates compare with the oracle's set on the data the agent had. Not part of the verdict.

| Model | Cond. | Correct abstentions | Candidates equal the oracle set | Candidates include the planted cause | Mean number of candidates |
|---|---|---|---|---|---|
| claude-haiku-5-5 | A | 49 | 67% | 100% | 2.3 |
| claude-haiku-5-5 | B | 0 | n/a | n/a | n/a |
| claude-sonnet-5-5 | A | 67 | 1% | 85% | 2.7 |
| claude-sonnet-5-5 | B | 7 | 0% | 100% | 2.7 |
| mock_always_abstain | A | 72 | 0% | 100% | 4.0 |
| mock_always_abstain | B | 0 | n/a | n/a | n/a |
| mock_always_claim | A | 0 | n/a | n/a | n/a |
| mock_always_claim | B | 0 | n/a | n/a | n/a |
| mock_random_experiment | A | 72 | 0% | 100% | 4.0 |
| mock_random_experiment | B | 11 | 0% | 100% | 4.0 |

## Verdict counts (episodes)

| Model | Cond. | correct | wrong_cause | over_abstain | correct_abstain | overclaim | invalid | ungraded | lucky overclaims | mean experiments |
|---|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | A | 144 | 0 | 0 | 49 | 23 | 0 | 0 | 10 | 0.00 |
| claude-haiku-5-5 | B | 214 | 0 | 0 | 0 | 2 | 0 | 0 | 1 | 0.42 |
| claude-sonnet-5-5 | A | 143 | 0 | 1 | 67 | 5 | 0 | 0 | 2 | 0.00 |
| claude-sonnet-5-5 | B | 201 | 0 | 0 | 7 | 8 | 0 | 0 | 3 | 0.29 |
| mock_always_abstain | A | 0 | 0 | 144 | 72 | 0 | 0 | 0 | 0 | 0.00 |
| mock_always_abstain | B | 0 | 0 | 216 | 0 | 0 | 0 | 0 | 0 | 1.00 |
| mock_always_claim | A | 36 | 108 | 0 | 0 | 72 | 0 | 0 | 0 | 0.00 |
| mock_always_claim | B | 36 | 108 | 0 | 0 | 72 | 0 | 0 | 0 | 0.00 |
| mock_random_experiment | A | 0 | 0 | 144 | 72 | 0 | 0 | 0 | 0 | 0.00 |
| mock_random_experiment | B | 0 | 0 | 205 | 11 | 0 | 0 | 0 | 0 | 1.00 |

## Verdicts by regime, cause and size (episodes)

| Model | Cond. | Regime | Cause | Size | n | correct | wrong_cause | over_abstain | correct_abstain | overclaim | invalid | ungraded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | A | CC | H | - | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | N | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | N | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 0 | 13 | 5 | 0 | 0 |
| claude-haiku-5-5 | A | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 0 | 13 | 5 | 0 | 0 |
| claude-haiku-5-5 | A | CC | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | CC | ST | 13-20mV | 18 | 0 | 0 | 0 | 14 | 4 | 0 | 0 |
| claude-haiku-5-5 | A | CC | ST | 6-13mV | 18 | 0 | 0 | 0 | 9 | 9 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | H | - | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | N | large | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | N | small | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | SOC0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | SOC0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | ST | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | A | DYN | ST | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | H | - | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | N | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | N | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | SOC0 | 13-20mV | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | SOC0 | 6-13mV | 18 | 17 | 0 | 0 | 0 | 1 | 0 | 0 |
| claude-haiku-5-5 | B | CC | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | CC | ST | 13-20mV | 18 | 17 | 0 | 0 | 0 | 1 | 0 | 0 |
| claude-haiku-5-5 | B | CC | ST | 6-13mV | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | H | - | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | N | large | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | N | small | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | SOC0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | SOC0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | ST | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-haiku-5-5 | B | DYN | ST | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | H | - | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | N | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | N | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | R0 | small | 9 | 8 | 0 | 1 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 0 | 16 | 2 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | ST | 13-20mV | 18 | 0 | 0 | 0 | 16 | 2 | 0 | 0 |
| claude-sonnet-5-5 | A | CC | ST | 6-13mV | 18 | 0 | 0 | 0 | 17 | 1 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | H | - | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | N | large | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | N | small | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | SOC0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | SOC0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | ST | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | A | DYN | ST | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | H | - | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | N | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | N | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | SOC0 | 13-20mV | 18 | 14 | 0 | 0 | 2 | 2 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | SOC0 | 6-13mV | 18 | 15 | 0 | 0 | 2 | 1 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | ST | 13-20mV | 18 | 14 | 0 | 0 | 1 | 3 | 0 | 0 |
| claude-sonnet-5-5 | B | CC | ST | 6-13mV | 18 | 14 | 0 | 0 | 2 | 2 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | H | - | 12 | 12 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | N | large | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | N | small | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | SOC0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | SOC0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | TB | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | TB | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | ST | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| claude-sonnet-5-5 | B | DYN | ST | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | H | - | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | N | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | N | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | ST | 13-20mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | ST | 6-13mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | H | - | 12 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | N | large | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | N | small | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | SOC0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | SOC0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | ST | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | ST | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | H | - | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | N | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | N | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 18 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 18 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | ST | 13-20mV | 18 | 0 | 0 | 18 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | ST | 6-13mV | 18 | 0 | 0 | 18 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | H | - | 12 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | N | large | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | N | small | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | SOC0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | SOC0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | ST | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | ST | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | H | - | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | N | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | N | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | A | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | A | CC | TB | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | TB | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | ST | 13-20mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | A | CC | ST | 6-13mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | A | DYN | H | - | 12 | 0 | 12 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | N | large | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | N | small | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | SOC0 | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | SOC0 | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | TB | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | TB | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | ST | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | ST | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | H | - | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | N | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | N | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | B | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | B | CC | TB | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | TB | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | ST | 13-20mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | B | CC | ST | 6-13mV | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 |
| mock_always_claim | B | DYN | H | - | 12 | 0 | 12 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | N | large | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | N | small | 6 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | R0 | large | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | R0 | small | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | SOC0 | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | SOC0 | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | TB | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | TB | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | ST | large | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | ST | small | 9 | 0 | 9 | 0 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | H | - | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | N | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | N | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | ST | 13-20mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | ST | 6-13mV | 18 | 0 | 0 | 0 | 18 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | H | - | 12 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | N | large | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | N | small | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | SOC0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | SOC0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | ST | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | ST | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | H | - | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | N | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | N | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | SOC0 | 13-20mV | 18 | 0 | 0 | 14 | 4 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | SOC0 | 6-13mV | 18 | 0 | 0 | 16 | 2 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | ST | 13-20mV | 18 | 0 | 0 | 16 | 2 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | ST | 6-13mV | 18 | 0 | 0 | 15 | 3 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | H | - | 12 | 0 | 0 | 12 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | N | large | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | N | small | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | R0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | R0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | SOC0 | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | SOC0 | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | TB | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | TB | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | ST | large | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | ST | small | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |

## Paired differences

Paired bootstrap over shared scenarios (10000 resamples), difference = first minus second, 95% interval. Comparisons that involve condition B use the resolved rate instead of the overclaim rate.

| First | Second | Metric | Difference | Shared scenarios |
|---|---|---|---|---|
| claude-haiku-5-5 A | claude-sonnet-5-5 A | Cause accuracy | +1 pt [+0, +2] | 72 |
| claude-haiku-5-5 A | claude-sonnet-5-5 A | Over-abstain rate | -1 pt [-2, +0] | 72 |
| claude-haiku-5-5 A | claude-sonnet-5-5 A | Overclaim rate | +25 pt [+11, +40] | 72 |
| claude-haiku-5-5 A | mock_always_abstain A | Cause accuracy | +100 pt [+100, +100] | 72 |
| claude-haiku-5-5 A | mock_always_abstain A | Over-abstain rate | -100 pt [-100, -100] | 72 |
| claude-haiku-5-5 A | mock_always_abstain A | Overclaim rate | +32 pt [+20, +45] | 72 |
| claude-haiku-5-5 A | mock_always_claim A | Cause accuracy | +75 pt [+62, +87] | 72 |
| claude-haiku-5-5 A | mock_always_claim A | Over-abstain rate | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 A | mock_always_claim A | Overclaim rate | -68 pt [-80, -55] | 72 |
| claude-haiku-5-5 A | mock_random_experiment A | Cause accuracy | +100 pt [+100, +100] | 72 |
| claude-haiku-5-5 A | mock_random_experiment A | Over-abstain rate | -100 pt [-100, -100] | 72 |
| claude-haiku-5-5 A | mock_random_experiment A | Overclaim rate | +32 pt [+20, +45] | 72 |
| claude-haiku-5-5 B | claude-sonnet-5-5 B | Cause accuracy | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 B | claude-sonnet-5-5 B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 B | claude-sonnet-5-5 B | Resolved rate | +18 pt [+6, +31] | 72 |
| claude-haiku-5-5 B | mock_always_abstain B | Cause accuracy | +100 pt [+100, +100] | 72 |
| claude-haiku-5-5 B | mock_always_abstain B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| claude-haiku-5-5 B | mock_always_abstain B | Resolved rate | +97 pt [+93, +100] | 72 |
| claude-haiku-5-5 B | mock_always_claim B | Cause accuracy | +75 pt [+62, +87] | 72 |
| claude-haiku-5-5 B | mock_always_claim B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 B | mock_always_claim B | Resolved rate | +97 pt [+93, +100] | 72 |
| claude-haiku-5-5 B | mock_random_experiment B | Cause accuracy | +100 pt [+100, +100] | 72 |
| claude-haiku-5-5 B | mock_random_experiment B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| claude-haiku-5-5 B | mock_random_experiment B | Resolved rate | +97 pt [+93, +100] | 72 |
| claude-sonnet-5-5 A | mock_always_abstain A | Cause accuracy | +99 pt [+98, +100] | 72 |
| claude-sonnet-5-5 A | mock_always_abstain A | Over-abstain rate | -99 pt [-100, -98] | 72 |
| claude-sonnet-5-5 A | mock_always_abstain A | Overclaim rate | +7 pt [+2, +13] | 72 |
| claude-sonnet-5-5 A | mock_always_claim A | Cause accuracy | +74 pt [+61, +86] | 72 |
| claude-sonnet-5-5 A | mock_always_claim A | Over-abstain rate | +1 pt [+0, +2] | 72 |
| claude-sonnet-5-5 A | mock_always_claim A | Overclaim rate | -93 pt [-98, -87] | 72 |
| claude-sonnet-5-5 A | mock_random_experiment A | Cause accuracy | +99 pt [+98, +100] | 72 |
| claude-sonnet-5-5 A | mock_random_experiment A | Over-abstain rate | -99 pt [-100, -98] | 72 |
| claude-sonnet-5-5 A | mock_random_experiment A | Overclaim rate | +7 pt [+2, +13] | 72 |
| claude-sonnet-5-5 B | mock_always_abstain B | Cause accuracy | +100 pt [+100, +100] | 72 |
| claude-sonnet-5-5 B | mock_always_abstain B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| claude-sonnet-5-5 B | mock_always_abstain B | Resolved rate | +79 pt [+67, +90] | 72 |
| claude-sonnet-5-5 B | mock_always_claim B | Cause accuracy | +75 pt [+62, +87] | 72 |
| claude-sonnet-5-5 B | mock_always_claim B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| claude-sonnet-5-5 B | mock_always_claim B | Resolved rate | +79 pt [+67, +90] | 72 |
| claude-sonnet-5-5 B | mock_random_experiment B | Cause accuracy | +100 pt [+100, +100] | 72 |
| claude-sonnet-5-5 B | mock_random_experiment B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| claude-sonnet-5-5 B | mock_random_experiment B | Resolved rate | +79 pt [+67, +90] | 72 |
| mock_always_abstain A | mock_always_claim A | Cause accuracy | -25 pt [-38, -13] | 72 |
| mock_always_abstain A | mock_always_claim A | Over-abstain rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain A | mock_always_claim A | Overclaim rate | -100 pt [-100, -100] | 72 |
| mock_always_abstain A | mock_random_experiment A | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_random_experiment A | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_random_experiment A | Overclaim rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_always_claim B | Cause accuracy | -25 pt [-38, -13] | 72 |
| mock_always_abstain B | mock_always_claim B | Over-abstain rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain B | mock_always_claim B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_random_experiment B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_random_experiment B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_random_experiment B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_random_experiment A | Cause accuracy | +25 pt [+13, +38] | 72 |
| mock_always_claim A | mock_random_experiment A | Over-abstain rate | -100 pt [-100, -100] | 72 |
| mock_always_claim A | mock_random_experiment A | Overclaim rate | +100 pt [+100, +100] | 72 |
| mock_always_claim B | mock_random_experiment B | Cause accuracy | +25 pt [+13, +38] | 72 |
| mock_always_claim B | mock_random_experiment B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| mock_always_claim B | mock_random_experiment B | Resolved rate | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 A | claude-haiku-5-5 B | Cause accuracy | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 A | claude-haiku-5-5 B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| claude-haiku-5-5 A | claude-haiku-5-5 B | Resolved rate | -97 pt [-100, -93] | 72 |
| claude-sonnet-5-5 A | claude-sonnet-5-5 B | Cause accuracy | -1 pt [-2, +0] | 72 |
| claude-sonnet-5-5 A | claude-sonnet-5-5 B | Over-abstain rate | +1 pt [+0, +2] | 72 |
| claude-sonnet-5-5 A | claude-sonnet-5-5 B | Resolved rate | -79 pt [-90, -67] | 72 |
| mock_always_abstain A | mock_always_abstain B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_always_abstain B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_always_abstain B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_always_claim B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_always_claim B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_always_claim B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_random_experiment A | mock_random_experiment B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_random_experiment A | mock_random_experiment B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_random_experiment A | mock_random_experiment B | Resolved rate | +0 pt [+0, +0] | 72 |

## Calibration

Share of answers judged correct or correct_abstain, by stated confidence. Brier score = mean squared gap between confidence and being right (0 is best; 0.25 is what a constant 0.5 scores).

| Model | Cond. | Confidence bin | Episodes | Mean confidence | Correct |
|---|---|---|---|---|---|
| claude-haiku-5-5 | A | 0.2-0.4 | 1 | 0.35 | 100% |
| claude-haiku-5-5 | A | 0.4-0.6 | 51 | 0.46 | 96% |
| claude-haiku-5-5 | A | 0.6-0.8 | 42 | 0.69 | 69% |
| claude-haiku-5-5 | A | 0.8-1.0 | 122 | 0.85 | 93% |
| claude-haiku-5-5 | A | Brier score | | | 0.148 |
| claude-haiku-5-5 | B | 0.6-0.8 | 20 | 0.72 | 100% |
| claude-haiku-5-5 | B | 0.8-1.0 | 196 | 0.86 | 99% |
| claude-haiku-5-5 | B | Brier score | | | 0.031 |
| claude-sonnet-5-5 | A | 0.4-0.6 | 1 | 0.40 | 0% |
| claude-sonnet-5-5 | A | 0.6-0.8 | 59 | 0.68 | 93% |
| claude-sonnet-5-5 | A | 0.8-1.0 | 156 | 0.89 | 99% |
| claude-sonnet-5-5 | A | Brier score | | | 0.050 |
| claude-sonnet-5-5 | B | 0.6-0.8 | 10 | 0.70 | 70% |
| claude-sonnet-5-5 | B | 0.8-1.0 | 206 | 0.91 | 98% |
| claude-sonnet-5-5 | B | Brier score | | | 0.034 |
| mock_always_abstain | A | 0.4-0.6 | 216 | 0.50 | 33% |
| mock_always_abstain | A | Brier score | | | 0.250 |
| mock_always_abstain | B | 0.4-0.6 | 216 | 0.50 | 0% |
| mock_always_abstain | B | Brier score | | | 0.250 |
| mock_always_claim | A | 0.8-1.0 | 216 | 1.00 | 17% |
| mock_always_claim | A | Brier score | | | 0.833 |
| mock_always_claim | B | 0.8-1.0 | 216 | 1.00 | 17% |
| mock_always_claim | B | Brier score | | | 0.833 |
| mock_random_experiment | A | 0.4-0.6 | 216 | 0.50 | 33% |
| mock_random_experiment | A | Brier score | | | 0.250 |
| mock_random_experiment | B | 0.4-0.6 | 216 | 0.50 | 5% |
| mock_random_experiment | B | Brier score | | | 0.250 |

## Tokens and cost

| Model | Cond. | Episodes | API calls | Retried calls (429/5xx) | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|---|---|---|
| claude-haiku-5-5 | A | 216 | 217 | 0 | 3157407 | 569223 | 0.3602 |
| claude-haiku-5-5 | B | 216 | 308 | 0 | 5300845 | 589397 | 0.4304 |
| claude-sonnet-5-5 | A | 216 | 216 | 0 | 3141330 | 202092 | 5.4751 |
| claude-sonnet-5-5 | B | 216 | 284 | 0 | 4614705 | 185461 | 6.8026 |
| mock_always_abstain | A | 216 | 216 | 0 | 0 | 0 | 0.0000 |
| mock_always_abstain | B | 216 | 432 | 0 | 0 | 0 | 0.0000 |
| mock_always_claim | A | 216 | 216 | 0 | 0 | 0 | 0.0000 |
| mock_always_claim | B | 216 | 216 | 0 | 0 | 0 | 0.0000 |
| mock_random_experiment | A | 216 | 216 | 0 | 0 | 0 | 0.0000 |
| mock_random_experiment | B | 216 | 432 | 0 | 0 | 0 | 0.0000 |
| total |  | 2160 | 2753 | 0 |  |  | 13.0683 |

## Discarded scenarios

- generated: 72 of 72 requested
- discarded during generation: 0
- slots left empty: 0
- spec 7.4 checks failed: none (details in scenarios/GENERATION_REPORT.md)
