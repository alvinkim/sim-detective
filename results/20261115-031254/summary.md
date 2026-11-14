# sim-detective summary

- runs: 20261115-031254
- episodes: 360, scenarios: 60, prompt version: v1
- Rates are over scenarios (repeats averaged per scenario first), with Wilson 95% intervals.
- In condition B the oracle is recomputed on the data the agent collected, so the identifiable / not identifiable split differs by model.
- `mock_always_claim` and `mock_always_abstain` are baselines.

## Metrics

| Model | Cond. | Cause accuracy (identifiable) | Overclaim rate (not identifiable) | Over-abstain rate (identifiable) | Resolving experiment chosen (initially not identifiable) | Invalid |
|---|---|---|---|---|---|---|
| mock_always_abstain | A | 0% [0, 7] (n=48) | 0% [0, 24] (n=12) | 100% [93, 100] (n=48) | 100% [76, 100] (n=12) | 0% [0, 6] (n=60) |
| mock_always_abstain | B | 0% [0, 6] (n=60) | n/a | 100% [94, 100] (n=60) | 100% [76, 100] (n=12) | 0% [0, 6] (n=60) |
| mock_always_claim | A | 25% [15, 39] (n=48) | 100% [76, 100] (n=12) | 0% [0, 7] (n=48) | 0% [0, 24] (n=12) | 0% [0, 6] (n=60) |
| mock_always_claim | B | 25% [15, 39] (n=48) | 100% [76, 100] (n=12) | 0% [0, 7] (n=48) | 0% [0, 24] (n=12) | 0% [0, 6] (n=60) |
| mock_oracle | A | 100% [93, 100] (n=48) | 0% [0, 24] (n=12) | 0% [0, 7] (n=48) | 100% [76, 100] (n=12) | 0% [0, 6] (n=60) |
| mock_oracle | B | 100% [94, 100] (n=60) | n/a | 0% [0, 6] (n=60) | 100% [76, 100] (n=12) | 0% [0, 6] (n=60) |

## Verdict counts (episodes)

| Model | Cond. | correct | wrong_cause | over_abstain | correct_abstain | overclaim | invalid | ungraded | lucky overclaims | mean experiments |
|---|---|---|---|---|---|---|---|---|---|---|
| mock_always_abstain | A | 0 | 0 | 48 | 12 | 0 | 0 | 0 | 0 | 0.00 |
| mock_always_abstain | B | 0 | 0 | 60 | 0 | 0 | 0 | 0 | 0 | 1.00 |
| mock_always_claim | A | 12 | 36 | 0 | 0 | 12 | 0 | 0 | 0 | 0.00 |
| mock_always_claim | B | 12 | 36 | 0 | 0 | 12 | 0 | 0 | 0 | 0.00 |
| mock_oracle | A | 48 | 0 | 0 | 12 | 0 | 0 | 0 | 0 | 0.00 |
| mock_oracle | B | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.20 |

## Paired differences

Paired bootstrap over shared scenarios (10000 resamples), difference = first minus second, 95% interval.

| First | Second | Metric | Difference | Shared scenarios |
|---|---|---|---|---|
| mock_always_abstain A | mock_always_claim A | Cause accuracy | -25 pt [-38, -13] | 60 |
| mock_always_abstain A | mock_always_claim A | Overclaim rate | -100 pt [-100, -100] | 60 |
| mock_always_abstain A | mock_always_claim A | Over-abstain rate | +100 pt [+100, +100] | 60 |
| mock_always_abstain A | mock_oracle A | Cause accuracy | -100 pt [-100, -100] | 60 |
| mock_always_abstain A | mock_oracle A | Overclaim rate | +0 pt [+0, +0] | 60 |
| mock_always_abstain A | mock_oracle A | Over-abstain rate | +100 pt [+100, +100] | 60 |
| mock_always_abstain B | mock_always_claim B | Cause accuracy | -25 pt [-38, -13] | 60 |
| mock_always_abstain B | mock_always_claim B | Overclaim rate | n/a | 60 |
| mock_always_abstain B | mock_always_claim B | Over-abstain rate | +100 pt [+100, +100] | 60 |
| mock_always_abstain B | mock_oracle B | Cause accuracy | -100 pt [-100, -100] | 60 |
| mock_always_abstain B | mock_oracle B | Overclaim rate | n/a | 60 |
| mock_always_abstain B | mock_oracle B | Over-abstain rate | +100 pt [+100, +100] | 60 |
| mock_always_claim A | mock_oracle A | Cause accuracy | -75 pt [-87, -62] | 60 |
| mock_always_claim A | mock_oracle A | Overclaim rate | +100 pt [+100, +100] | 60 |
| mock_always_claim A | mock_oracle A | Over-abstain rate | +0 pt [+0, +0] | 60 |
| mock_always_claim B | mock_oracle B | Cause accuracy | -75 pt [-87, -62] | 60 |
| mock_always_claim B | mock_oracle B | Overclaim rate | n/a | 60 |
| mock_always_claim B | mock_oracle B | Over-abstain rate | +0 pt [+0, +0] | 60 |
| mock_always_abstain A | mock_always_abstain B | Cause accuracy | +0 pt [+0, +0] | 60 |
| mock_always_abstain A | mock_always_abstain B | Overclaim rate | n/a | 60 |
| mock_always_abstain A | mock_always_abstain B | Over-abstain rate | +0 pt [+0, +0] | 60 |
| mock_always_claim A | mock_always_claim B | Cause accuracy | +0 pt [+0, +0] | 60 |
| mock_always_claim A | mock_always_claim B | Overclaim rate | +0 pt [+0, +0] | 60 |
| mock_always_claim A | mock_always_claim B | Over-abstain rate | +0 pt [+0, +0] | 60 |
| mock_oracle A | mock_oracle B | Cause accuracy | +0 pt [+0, +0] | 60 |
| mock_oracle A | mock_oracle B | Overclaim rate | n/a | 60 |
| mock_oracle A | mock_oracle B | Over-abstain rate | +0 pt [+0, +0] | 60 |

## Calibration

Share of answers judged correct or correct_abstain, by stated confidence.

| Model | Cond. | Confidence bin | Episodes | Mean confidence | Correct |
|---|---|---|---|---|---|
| mock_always_abstain | A | 0.4-0.6 | 60 | 0.50 | 20% |
| mock_always_abstain | B | 0.4-0.6 | 60 | 0.50 | 0% |
| mock_always_claim | A | 0.8-1.0 | 60 | 1.00 | 20% |
| mock_always_claim | B | 0.8-1.0 | 60 | 1.00 | 20% |
| mock_oracle | A | 0.8-1.0 | 60 | 1.00 | 100% |
| mock_oracle | B | 0.8-1.0 | 60 | 1.00 | 100% |

## Tokens and cost

| Model | Cond. | Episodes | API calls | Input tokens | Output tokens | Cost (USD) |
|---|---|---|---|---|---|---|
| mock_always_abstain | A | 60 | 60 | 0 | 0 | 0.0000 |
| mock_always_abstain | B | 60 | 120 | 0 | 0 | 0.0000 |
| mock_always_claim | A | 60 | 60 | 0 | 0 | 0.0000 |
| mock_always_claim | B | 60 | 60 | 0 | 0 | 0.0000 |
| mock_oracle | A | 60 | 60 | 0 | 0 | 0.0000 |
| mock_oracle | B | 60 | 72 | 0 | 0 | 0.0000 |
| total |  | 360 | 432 |  |  | 0.0000 |

## Discarded scenarios

- generated: 60 of 60 requested
- discarded during generation: 0
- slots left empty: 0
- spec 7.4 checks failed: CC scenarios of R0, SOC0, TB, ST have a consistent set of size >= 2 (details in scenarios/GENERATION_REPORT.md)
