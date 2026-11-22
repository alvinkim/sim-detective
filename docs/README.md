# Documents

## Start here

Two English summaries cover the results and one English note describes the model. Everything else in this folder is in Korean.

- [RESULTS_DIRECTION1.md](RESULTS_DIRECTION1.md): Direction 1, cause identification and abstention. Design, results for three models, case classification, limits.
- [RESULTS_DIRECTION2.md](RESULTS_DIRECTION2.md): Direction 2, twin monitor against rules and an LLM monitor, rounds 1–4. Conclusion, results by round, limits.
- [MODEL.md](MODEL.md): the battery model, with diagrams. The single cell, and what rounds 3 and 4 of Direction 2 add.

Where an English summary and a Korean original differ, the original holds.

## Korean documents

The documents were written as the work went on. They are kept as written, except for the wording changes recorded in [SIMDET_PUBLIC_AUDIT.md](SIMDET_PUBLIC_AUDIT.md).

### Instructions

Task specifications given to the coding agent.

| File | Content |
|---|---|
| [SIM_DETECTIVE_CODING_AGENT_SPEC.md](SIM_DETECTIVE_CODING_AGENT_SPEC.md) | Direction 1: the original specification of the benchmark (system, planted causes, oracle, conditions, grading) |
| [SIMDET_FOLLOWUP_001.md](SIMDET_FOLLOWUP_001.md) | Direction 1: follow-up tasks after the first mock runs, and the rules for the real runs |
| [SIMDET_D2_PILOT_SPEC.md](SIMDET_D2_PILOT_SPEC.md) | Direction 2, round 1: specification of the monitor comparison pilot |
| [SIMDET_D2_FOLLOWUP_001.md](SIMDET_D2_FOLLOWUP_001.md) | Direction 2, round 2: reanalysis of round 1 and an attack that keeps the requested mean current |
| [SIMDET_D2_FOLLOWUP_002.md](SIMDET_D2_FOLLOWUP_002.md) | Direction 2, round 3: a plant with an unmeasured core temperature, up to the feasibility check |
| [SIMDET_D2_FOLLOWUP_003.md](SIMDET_D2_FOLLOWUP_003.md) | Direction 2, round 4: a six-cell pack with hidden faults, up to the feasibility check |

### Pre-registrations

Fixed and committed before the runs they cover.

| File | Content |
|---|---|
| [SIMDET_D2_PREREG.md](SIMDET_D2_PREREG.md) | Direction 2, round 1: hypotheses, metrics and settings of the pilot |
| [SIMDET_D2_PREREG_4.md](SIMDET_D2_PREREG_4.md) | Direction 2, round 4: hypotheses and settings of the confirmation run on a new seed |

Direction 1 has no separate pre-registration document; its thresholds, scenarios, grading rules and prompt were fixed before the real runs (see RESULTS_DIRECTION1.md, section 1).

### Reports

| File | Content |
|---|---|
| [SIMDET_RESULTS_001.md](SIMDET_RESULTS_001.md) | Direction 1: results and conclusions of the real runs (Haiku, Sonnet, Opus) |
| [SIMDET_D2_G0_REPORT.md](SIMDET_D2_G0_REPORT.md) | Direction 2, round 1: feasibility check of 520 unmonitored episodes |
| [SIMDET_D2_RESULTS_001.md](SIMDET_D2_RESULTS_001.md) | Direction 2, round 1: detailed results, with gate reports and deviations |
| [SIMDET_D2_EXPERIMENT_REPORT.md](SIMDET_D2_EXPERIMENT_REPORT.md) | Direction 2, round 1: the experiment report (method, results, interpretation) |
| [SIMDET_D2_REANALYSIS_001.md](SIMDET_D2_REANALYSIS_001.md) | Direction 2, round 1 data reanalysed with simple rules as extra baselines |
| [SIMDET_D2_G0_REPORT_2.md](SIMDET_D2_G0_REPORT_2.md) | Direction 2, round 2: feasibility check; the round stopped here |
| [SIMDET_D2_G0_REPORT_3.md](SIMDET_D2_G0_REPORT_3.md) | Direction 2, round 3: feasibility check; the round stopped here |
| [SIMDET_D2_G0_REPORT_4.md](SIMDET_D2_G0_REPORT_4.md) | Direction 2, round 4: feasibility check, with the appendix that adds rule R9 |
| [SIMDET_D2_RESULTS_004.md](SIMDET_D2_RESULTS_004.md) | Direction 2, round 4: results of the pre-registered confirmation run |
| [SIMDET_D2_EXPERIMENT_REPORT_FINAL.md](SIMDET_D2_EXPERIMENT_REPORT_FINAL.md) | Direction 2: final report over rounds 1–4 (the original of RESULTS_DIRECTION2.md) |

### Reviews and decision records

| File | Content |
|---|---|
| [SIMDET_IMPROVEMENT_PROPOSAL_001.md](SIMDET_IMPROVEMENT_PROPOSAL_001.md) | Direction 1: the coding agent's proposal of fixes to make before the pilot |
| [SIMDET_DECISION_001.md](SIMDET_DECISION_001.md) | Direction 1: the user's review of that proposal and the decisions taken |
| [SIMDET_DECISION_002.md](SIMDET_DECISION_002.md) | Direction 1: amendments to the first decision after the agent's reply |
| [SIMDET_CASE_REVIEW_001.md](SIMDET_CASE_REVIEW_001.md) | Direction 1: post-hoc reading and classification of the overclaim episodes |
| [SIMDET_PUBLIC_AUDIT.md](SIMDET_PUBLIC_AUDIT.md) | Audit before public release: secrets and history check, changes made, number cross-check, reproduction |
