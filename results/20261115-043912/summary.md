# sim-detective summary

- runs: 20261115-043912
- episodes: 576, scenarios: 72, prompt version: v2
- Main metrics: overclaim rate and over-abstain rate in condition A; resolved rate in condition B. Experiment choice is a secondary metric (see its baseline below).
- Rates are over scenarios (repeats averaged per scenario first), with Wilson 95% intervals.
- `mock_always_claim`, `mock_always_abstain` and `mock_random_experiment` are baselines.

## Metrics

| Model | Cond. | Cause accuracy (identifiable) | Cause accuracy, TB excluded | Overclaim rate (not identifiable) | Over-abstain rate (identifiable) | Over-abstain rate, CC small R0 excluded | Invalid |
|---|---|---|---|---|---|---|---|
| mock_always_abstain | A | 0% [0, 7] (n=48) | 0% [0, 10] (n=36) | 0% [0, 14] (n=24) | 100% [93, 100] (n=48) | 100% [92, 100] (n=45) | 0% [0, 5] (n=72) |
| mock_always_abstain | B | 0% [0, 5] (n=72) | 0% [0, 6] (n=60) | n/a | 100% [95, 100] (n=72) | 100% [95, 100] (n=69) | 0% [0, 5] (n=72) |
| mock_always_claim | A | 25% [15, 39] (n=48) | 33% [20, 50] (n=36) | 100% [86, 100] (n=24) | 0% [0, 7] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| mock_always_claim | B | 25% [15, 39] (n=48) | 33% [20, 50] (n=36) | 100% [86, 100] (n=24) | 0% [0, 7] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| mock_oracle | A | 100% [93, 100] (n=48) | 100% [90, 100] (n=36) | 0% [0, 14] (n=24) | 0% [0, 7] (n=48) | 0% [0, 8] (n=45) | 0% [0, 5] (n=72) |
| mock_oracle | B | 100% [95, 100] (n=72) | 100% [94, 100] (n=60) | n/a | 0% [0, 5] (n=72) | 0% [0, 5] (n=69) | 0% [0, 5] (n=72) |
| mock_random_experiment | A | 0% [0, 7] (n=48) | 0% [0, 10] (n=36) | 0% [0, 14] (n=24) | 100% [93, 100] (n=48) | 100% [92, 100] (n=45) | 0% [0, 5] (n=72) |
| mock_random_experiment | B | 0% [0, 5] (n=69) | 0% [0, 6] (n=57) | 0% [0, 56] (n=3) | 100% [95, 100] (n=69) | 100% [94, 100] (n=66) | 0% [0, 5] (n=72) |

- In condition B the oracle is recomputed on the data the agent collected. The overclaim rate in B is therefore taken over the scenarios that were still not identifiable after that model's own experiments: its denominator differs by model, so do not compare it between models. Use the resolved rate below.
- TB scenarios are easy (t_bias is 35 or 71 times SIGMA_T) and lift cause accuracy; CC small R0 is hard (separated only by self-heating in T_meas) and an abstention there counts as over-abstain. The two extra columns leave those strata out; grading is unchanged.

## Design-level intervals (identifiable scenarios)

The identifiable scenarios are a few designs (regime, cause, size) repeated with different noise. Here whole designs are resampled (bootstrap), so the interval does not treat the repeats of a design as independent. Quote these intervals for conclusions about the identifiable scenarios.

| Model | Cond. | Cause accuracy | Cause accuracy, TB excluded | Over-abstain rate | Over-abstain rate, CC small R0 excluded |
|---|---|---|---|---|---|
| mock_always_abstain | A | 0% [0, 0] (18 designs) | 0% [0, 0] (14 designs) | 100% [100, 100] (18 designs) | 100% [100, 100] (17 designs) |
| mock_always_abstain | B | 0% [0, 0] (22 designs) | 0% [0, 0] (18 designs) | 100% [100, 100] (22 designs) | 100% [100, 100] (21 designs) |
| mock_always_claim | A | 25% [6, 48] (18 designs) | 33% [8, 60] (14 designs) | 0% [0, 0] (18 designs) | 0% [0, 0] (17 designs) |
| mock_always_claim | B | 25% [6, 48] (18 designs) | 33% [8, 60] (14 designs) | 0% [0, 0] (18 designs) | 0% [0, 0] (17 designs) |
| mock_oracle | A | 100% [100, 100] (18 designs) | 100% [100, 100] (14 designs) | 0% [0, 0] (18 designs) | 0% [0, 0] (17 designs) |
| mock_oracle | B | 100% [100, 100] (22 designs) | 100% [100, 100] (18 designs) | 0% [0, 0] (22 designs) | 0% [0, 0] (21 designs) |
| mock_random_experiment | A | 0% [0, 0] (18 designs) | 0% [0, 0] (14 designs) | 100% [100, 100] (18 designs) | 100% [100, 100] (17 designs) |
| mock_random_experiment | B | 0% [0, 0] (22 designs) | 0% [0, 0] (18 designs) | 100% [100, 100] (22 designs) | 100% [100, 100] (21 designs) |

## Scenarios that start not identifiable

Both rates are over the scenarios that were not identifiable before any experiment, so the denominator is the same for every model. Resolved = the final answer is judged correct (only possible in condition B, after an experiment that leaves one cause).

| Model | Cond. | Resolved rate | Resolving experiment chosen (secondary) | Mean length of the resolving experiments chosen |
|---|---|---|---|---|
| mock_always_abstain | A | 0% [0, 14] (n=24) | 100% [86, 100] (n=24) | 5400 s (n=24) |
| mock_always_abstain | B | 0% [0, 14] (n=24) | 100% [86, 100] (n=24) | 5400 s (n=24) |
| mock_always_claim | A | 0% [0, 14] (n=24) | 0% [0, 14] (n=24) | n/a |
| mock_always_claim | B | 0% [0, 14] (n=24) | 0% [0, 14] (n=24) | n/a |
| mock_oracle | A | 0% [0, 14] (n=24) | 100% [86, 100] (n=24) | 390 s (n=24) |
| mock_oracle | B | 100% [86, 100] (n=24) | 100% [86, 100] (n=24) | 390 s (n=24) |
| mock_random_experiment | A | 0% [0, 14] (n=24) | 88% [69, 96] (n=24) | 1081 s (n=21) |
| mock_random_experiment | B | 0% [0, 14] (n=24) | 88% [69, 96] (n=24) | 1081 s (n=21) |

- Experiment choice is easy on this scenario set: a uniformly random pick among the 9 representative experiments is resolving in 87% of cases (expected value; `mock_random_experiment` is one draw of it). Read "resolving experiment chosen" against that baseline.
- The shortest experiment that resolves every scenario takes 390 s; compare the mean length column with it.
- These scenarios have target shifts spread over a continuous range (one per equal slice of the range for each cause), so scenario-level Wilson intervals are used for them.

## Not identifiable scenarios by cause and size

| Model | Cond. | Cause | Size | Scenarios | Overclaim rate | Resolved rate | Resolving experiment chosen |
|---|---|---|---|---|---|---|---|
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
| mock_oracle | A | SOC0 | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | A | SOC0 | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | A | ST | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | A | ST | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | B | SOC0 | 13-20mV | 6 | n/a | 100% [61, 100] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | B | SOC0 | 6-13mV | 6 | n/a | 100% [61, 100] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | B | ST | 13-20mV | 6 | n/a | 100% [61, 100] (n=6) | 100% [61, 100] (n=6) |
| mock_oracle | B | ST | 6-13mV | 6 | n/a | 100% [61, 100] (n=6) | 100% [61, 100] (n=6) |
| mock_random_experiment | A | SOC0 | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |
| mock_random_experiment | A | SOC0 | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_random_experiment | A | ST | 13-20mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |
| mock_random_experiment | A | ST | 6-13mV | 6 | 0% [0, 39] (n=6) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |
| mock_random_experiment | B | SOC0 | 13-20mV | 6 | 0% [0, 79] (n=1) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |
| mock_random_experiment | B | SOC0 | 6-13mV | 6 | n/a | 0% [0, 39] (n=6) | 100% [61, 100] (n=6) |
| mock_random_experiment | B | ST | 13-20mV | 6 | 0% [0, 79] (n=1) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |
| mock_random_experiment | B | ST | 6-13mV | 6 | 0% [0, 79] (n=1) | 0% [0, 39] (n=6) | 83% [44, 97] (n=6) |

## Abstention quality

For episodes judged correct_abstain: how the listed candidates compare with the oracle's set on the data the agent had. Not part of the verdict.

| Model | Cond. | Correct abstentions | Candidates equal the oracle set | Candidates include the planted cause | Mean number of candidates |
|---|---|---|---|---|---|
| mock_always_abstain | A | 24 | 0% | 100% | 4.0 |
| mock_always_abstain | B | 0 | n/a | n/a | n/a |
| mock_always_claim | A | 0 | n/a | n/a | n/a |
| mock_always_claim | B | 0 | n/a | n/a | n/a |
| mock_oracle | A | 24 | 100% | 100% | 2.0 |
| mock_oracle | B | 0 | n/a | n/a | n/a |
| mock_random_experiment | A | 24 | 0% | 100% | 4.0 |
| mock_random_experiment | B | 3 | 0% | 100% | 4.0 |

## Verdict counts (episodes)

| Model | Cond. | correct | wrong_cause | over_abstain | correct_abstain | overclaim | invalid | ungraded | lucky overclaims | mean experiments |
|---|---|---|---|---|---|---|---|---|---|---|
| mock_always_abstain | A | 0 | 0 | 48 | 24 | 0 | 0 | 0 | 0 | 0.00 |
| mock_always_abstain | B | 0 | 0 | 72 | 0 | 0 | 0 | 0 | 0 | 1.00 |
| mock_always_claim | A | 12 | 36 | 0 | 0 | 24 | 0 | 0 | 0 | 0.00 |
| mock_always_claim | B | 12 | 36 | 0 | 0 | 24 | 0 | 0 | 0 | 0.00 |
| mock_oracle | A | 48 | 0 | 0 | 24 | 0 | 0 | 0 | 0 | 0.00 |
| mock_oracle | B | 72 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.33 |
| mock_random_experiment | A | 0 | 0 | 48 | 24 | 0 | 0 | 0 | 0 | 0.00 |
| mock_random_experiment | B | 0 | 0 | 69 | 3 | 0 | 0 | 0 | 0 | 1.00 |

## Verdicts by regime, cause and size (episodes)

| Model | Cond. | Regime | Cause | Size | n | correct | wrong_cause | over_abstain | correct_abstain | overclaim | invalid | ungraded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mock_always_abstain | A | CC | H | - | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | N | large | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | N | small | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | ST | 13-20mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_always_abstain | A | CC | ST | 6-13mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | H | - | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | N | large | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | N | small | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | SOC0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | SOC0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | ST | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | A | DYN | ST | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | H | - | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | N | large | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | N | small | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | ST | 13-20mV | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | CC | ST | 6-13mV | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | H | - | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | N | large | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | N | small | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | SOC0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | SOC0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | ST | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_abstain | B | DYN | ST | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | H | - | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | N | large | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | N | small | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | A | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | A | CC | TB | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | TB | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | CC | ST | 13-20mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | A | CC | ST | 6-13mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | A | DYN | H | - | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | N | large | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | N | small | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | SOC0 | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | SOC0 | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | TB | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | TB | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | ST | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | A | DYN | ST | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | H | - | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | N | large | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | N | small | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | B | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | B | CC | TB | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | TB | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | CC | ST | 13-20mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | B | CC | ST | 6-13mV | 6 | 0 | 0 | 0 | 0 | 6 | 0 | 0 |
| mock_always_claim | B | DYN | H | - | 4 | 0 | 4 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | N | large | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | N | small | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | SOC0 | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | SOC0 | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | TB | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | TB | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | ST | large | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_always_claim | B | DYN | ST | small | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | H | - | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | N | large | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | N | small | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_oracle | A | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_oracle | A | CC | TB | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | TB | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | CC | ST | 13-20mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_oracle | A | CC | ST | 6-13mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_oracle | A | DYN | H | - | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | N | large | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | N | small | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | SOC0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | SOC0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | TB | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | TB | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | ST | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | A | DYN | ST | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | H | - | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | N | large | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | N | small | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | SOC0 | 13-20mV | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | SOC0 | 6-13mV | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | TB | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | TB | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | ST | 13-20mV | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | CC | ST | 6-13mV | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | H | - | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | N | large | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | N | small | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | R0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | SOC0 | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | SOC0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | TB | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | TB | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | ST | large | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_oracle | B | DYN | ST | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | H | - | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | N | large | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | N | small | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | ST | 13-20mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_random_experiment | A | CC | ST | 6-13mV | 6 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | H | - | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | N | large | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | N | small | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | SOC0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | SOC0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | ST | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | A | DYN | ST | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | H | - | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | N | large | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | N | small | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | SOC0 | 13-20mV | 6 | 0 | 0 | 5 | 1 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | SOC0 | 6-13mV | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | ST | 13-20mV | 6 | 0 | 0 | 5 | 1 | 0 | 0 | 0 |
| mock_random_experiment | B | CC | ST | 6-13mV | 6 | 0 | 0 | 5 | 1 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | H | - | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | N | large | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | N | small | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | R0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | R0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | SOC0 | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | SOC0 | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | TB | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | ST | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| mock_random_experiment | B | DYN | ST | small | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |

## Paired differences

Paired bootstrap over shared scenarios (10000 resamples), difference = first minus second, 95% interval. Comparisons that involve condition B use the resolved rate instead of the overclaim rate.

| First | Second | Metric | Difference | Shared scenarios |
|---|---|---|---|---|
| mock_always_abstain A | mock_always_claim A | Cause accuracy | -25 pt [-38, -13] | 72 |
| mock_always_abstain A | mock_always_claim A | Over-abstain rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain A | mock_always_claim A | Overclaim rate | -100 pt [-100, -100] | 72 |
| mock_always_abstain A | mock_oracle A | Cause accuracy | -100 pt [-100, -100] | 72 |
| mock_always_abstain A | mock_oracle A | Over-abstain rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain A | mock_oracle A | Overclaim rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_random_experiment A | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_random_experiment A | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_random_experiment A | Overclaim rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_always_claim B | Cause accuracy | -25 pt [-38, -13] | 72 |
| mock_always_abstain B | mock_always_claim B | Over-abstain rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain B | mock_always_claim B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_oracle B | Cause accuracy | -100 pt [-100, -100] | 72 |
| mock_always_abstain B | mock_oracle B | Over-abstain rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain B | mock_oracle B | Resolved rate | -100 pt [-100, -100] | 72 |
| mock_always_abstain B | mock_random_experiment B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_random_experiment B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain B | mock_random_experiment B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_oracle A | Cause accuracy | -75 pt [-87, -62] | 72 |
| mock_always_claim A | mock_oracle A | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_oracle A | Overclaim rate | +100 pt [+100, +100] | 72 |
| mock_always_claim A | mock_random_experiment A | Cause accuracy | +25 pt [+13, +38] | 72 |
| mock_always_claim A | mock_random_experiment A | Over-abstain rate | -100 pt [-100, -100] | 72 |
| mock_always_claim A | mock_random_experiment A | Overclaim rate | +100 pt [+100, +100] | 72 |
| mock_always_claim B | mock_oracle B | Cause accuracy | -75 pt [-87, -62] | 72 |
| mock_always_claim B | mock_oracle B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_claim B | mock_oracle B | Resolved rate | -100 pt [-100, -100] | 72 |
| mock_always_claim B | mock_random_experiment B | Cause accuracy | +25 pt [+13, +38] | 72 |
| mock_always_claim B | mock_random_experiment B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| mock_always_claim B | mock_random_experiment B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_oracle A | mock_random_experiment A | Cause accuracy | +100 pt [+100, +100] | 72 |
| mock_oracle A | mock_random_experiment A | Over-abstain rate | -100 pt [-100, -100] | 72 |
| mock_oracle A | mock_random_experiment A | Overclaim rate | +0 pt [+0, +0] | 72 |
| mock_oracle B | mock_random_experiment B | Cause accuracy | +100 pt [+100, +100] | 72 |
| mock_oracle B | mock_random_experiment B | Over-abstain rate | -100 pt [-100, -100] | 72 |
| mock_oracle B | mock_random_experiment B | Resolved rate | +100 pt [+100, +100] | 72 |
| mock_always_abstain A | mock_always_abstain B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_always_abstain B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_abstain A | mock_always_abstain B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_always_claim B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_always_claim B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_always_claim A | mock_always_claim B | Resolved rate | +0 pt [+0, +0] | 72 |
| mock_oracle A | mock_oracle B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_oracle A | mock_oracle B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_oracle A | mock_oracle B | Resolved rate | -100 pt [-100, -100] | 72 |
| mock_random_experiment A | mock_random_experiment B | Cause accuracy | +0 pt [+0, +0] | 72 |
| mock_random_experiment A | mock_random_experiment B | Over-abstain rate | +0 pt [+0, +0] | 72 |
| mock_random_experiment A | mock_random_experiment B | Resolved rate | +0 pt [+0, +0] | 72 |

## Calibration

Share of answers judged correct or correct_abstain, by stated confidence. Brier score = mean squared gap between confidence and being right (0 is best; 0.25 is what a constant 0.5 scores).

| Model | Cond. | Confidence bin | Episodes | Mean confidence | Correct |
|---|---|---|---|---|---|
| mock_always_abstain | A | 0.4-0.6 | 72 | 0.50 | 33% |
| mock_always_abstain | A | Brier score | | | 0.250 |
| mock_always_abstain | B | 0.4-0.6 | 72 | 0.50 | 0% |
| mock_always_abstain | B | Brier score | | | 0.250 |
| mock_always_claim | A | 0.8-1.0 | 72 | 1.00 | 17% |
| mock_always_claim | A | Brier score | | | 0.833 |
| mock_always_claim | B | 0.8-1.0 | 72 | 1.00 | 17% |
| mock_always_claim | B | Brier score | | | 0.833 |
| mock_oracle | A | 0.8-1.0 | 72 | 1.00 | 100% |
| mock_oracle | A | Brier score | | | 0.000 |
| mock_oracle | B | 0.8-1.0 | 72 | 1.00 | 100% |
| mock_oracle | B | Brier score | | | 0.000 |
| mock_random_experiment | A | 0.4-0.6 | 72 | 0.50 | 33% |
| mock_random_experiment | A | Brier score | | | 0.250 |
| mock_random_experiment | B | 0.4-0.6 | 72 | 0.50 | 4% |
| mock_random_experiment | B | Brier score | | | 0.250 |

## Tokens and cost

| Model | Cond. | Episodes | API calls | Retried calls (429/5xx) | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|---|---|---|
| mock_always_abstain | A | 72 | 72 | 0 | 0 | 0 | 0.0000 |
| mock_always_abstain | B | 72 | 144 | 0 | 0 | 0 | 0.0000 |
| mock_always_claim | A | 72 | 72 | 0 | 0 | 0 | 0.0000 |
| mock_always_claim | B | 72 | 72 | 0 | 0 | 0 | 0.0000 |
| mock_oracle | A | 72 | 72 | 0 | 0 | 0 | 0.0000 |
| mock_oracle | B | 72 | 96 | 0 | 0 | 0 | 0.0000 |
| mock_random_experiment | A | 72 | 72 | 0 | 0 | 0 | 0.0000 |
| mock_random_experiment | B | 72 | 144 | 0 | 0 | 0 | 0.0000 |
| total |  | 576 | 744 | 0 |  |  | 0.0000 |

## Discarded scenarios

- generated: 72 of 72 requested
- discarded during generation: 0
- slots left empty: 0
- spec 7.4 checks failed: none (details in scenarios/GENERATION_REPORT.md)
