import json

import pytest

from simdet.agent.mock import make_mock
from simdet.agent.runner import dumps, run_episode
from simdet.score import stats
from simdet.score.grade import grade_episode
from simdet.scenario import generate as g
from simdet.score.report import projection_rows, write_report


def test_wilson_interval():
    lo, hi = stats.wilson(0.5, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3) and hi == pytest.approx(0.5962, abs=1e-3)
    assert stats.wilson(0.0, 12)[0] == 0.0 and stats.wilson(1.0, 12)[1] == 1.0


def test_repeats_are_averaged_per_scenario():
    def ep(sid, verdict):
        return {"scenario_id": sid, "grade": {"verdict": verdict, "final_identifiable": True,
                                              "initial_identifiable": True, "experiment_class": None}}
    episodes = [ep("a", "correct"), ep("a", "wrong_cause"), ep("a", "wrong_cause"), ep("b", "correct")]
    r = stats.rate(stats.per_scenario(episodes, "accuracy"))
    assert r["n"] == 2 and r["rate"] == pytest.approx((1 / 3 + 1) / 2)


def test_paired_bootstrap():
    a = {str(i): (1.0, 1.0) for i in range(40)}
    b = {str(i): (float(i % 2), 1.0) for i in range(40)}
    d = stats.paired_bootstrap_diff(a, b, n_boot=2000)
    assert d["diff"] == pytest.approx(0.5) and d["lo"] < 0.5 < d["hi"] and d["lo"] > 0.2
    same = stats.paired_bootstrap_diff(a, a, n_boot=200)
    assert same["diff"] == 0 and same["lo"] == 0 and same["hi"] == 0


def test_report_files(cfg, scenario_set, tmp_path):
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    with open(run_dir / "episodes.jsonl", "w", encoding="utf-8") as f:
        for name in ("mock_always_claim", "mock_always_abstain"):
            client = make_mock(name)
            for private in scenario_set["privates"]:
                record = run_episode(client, cfg, scenario_set["publics"][private["id"]], "A")
                record["grade"] = grade_episode(cfg, record, private)
                f.write(dumps(record) + "\n")
    log = {"requested": 72, "generated": 72, "discarded": [], "unfilled": [], "checks": [],
           "continuous_shift": True,
           "experiment_baseline": g.experiment_baseline(cfg, scenario_set["privates"])}
    out = write_report(cfg, [run_dir], run_dir, log)
    for name in ("summary.md", "examples.md", "fig_overclaim.png", "fig_confusion.png", "fig_experiment.png"):
        assert (out / name).stat().st_size > 0
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "Over-abstain rate" in summary and "mock_always_abstain" in summary
    # follow-up T4: two extra columns and the per-stratum table
    assert "Cause accuracy, TB excluded" in summary
    assert "Over-abstain rate, CC small R0 excluded" in summary
    assert "## Verdicts by regime, cause and size (episodes)" in summary
    assert "| mock_always_claim | A | CC | R0 | small | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |" in summary
    assert "| mock_always_abstain | A | DYN | TB | large | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |" in summary
    # follow-up T5: resolved rate, and the note on the condition-B overclaim denominator
    assert "| Model | Cond. | Resolved rate | Resolving experiment chosen (secondary) |" in summary
    assert "its denominator differs by model" in summary
    # DECISION-001/002: design-level intervals, abstention quality, experiment baseline, Brier
    assert "## Design-level intervals (identifiable scenarios)" in summary
    assert "(18 designs)" in summary and "(14 designs)" in summary  # all, and without TB
    assert "| mock_always_claim | A | 25% [6, 48] (18 designs) |" in summary  # wider than Wilson [15, 39]
    assert "## Not identifiable scenarios by cause and size" in summary
    assert "| mock_always_claim | A | SOC0 | 6-13mV | 6 | 100% [61, 100] (n=6) |" in summary
    assert "## Abstention quality" in summary
    assert "| mock_always_abstain | A | 24 | 0% | 100% | 4.0 |" in summary
    assert "is resolving in 87% of cases" in summary and "takes 390 s" in summary
    assert "scenario-level Wilson intervals are used" in summary
    assert "| mock_always_abstain | A | Brier score | | | 0.250 |" in summary
    assert "Main metrics: overclaim rate and over-abstain rate in condition A" in summary
    first = json.loads((run_dir / "episodes.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert {"responses", "answer", "grade", "usage", "cost_usd", "prompt_version"} <= set(first)


def test_cluster_bootstrap_is_wider_than_scenario_level():
    """Six scenarios per design that all agree: the design-level interval reflects 4 units."""
    pairs = {f"{d}{i}": (float(d < 2), 1.0) for d in range(4) for i in range(6)}
    cluster_of = {sid: (sid[0],) for sid in pairs}
    c = stats.cluster_bootstrap(pairs, cluster_of, n_boot=4000)
    lo, hi = stats.wilson(0.5, 24)
    assert c["clusters"] == 4 and c["lo"] < lo and c["hi"] > hi
    assert stats.cluster_bootstrap({"a": (1.0, 1.0)}, {"a": ("x",)})["lo"] is None


def test_brier_score():
    def ep(conf, verdict):
        return {"grade": {"confidence": conf, "verdict": verdict}}
    assert stats.brier([ep(1.0, "correct"), ep(1.0, "overclaim")]) == pytest.approx(0.5)
    assert stats.brier([ep(0.9, "invalid")]) is None


def test_projection_from_measured_episodes(cfg):
    usage = {"input_tokens": 10_000, "output_tokens": 2_000,
             "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    episode = {"model": "claude-haiku-5-5", "condition": "A", "usage": usage, "n_calls": 1,
               "responses": [{"elapsed_s": 20.0}]}
    rows = {r[0]: r for r in projection_rows(cfg, [episode], n_scenarios=72, repeats=3)}
    haiku, sonnet = rows["claude-haiku-5-5"], rows["claude-sonnet-5-5"]
    assert haiku[2] == "measured" and sonnet[2] == "tokens of other models"
    assert float(haiku[4]) == pytest.approx((10_000 * 0.10 + 2_000 * 0.50) / 1e6, abs=1e-4)
    assert float(sonnet[5]) == pytest.approx(216 * (10_000 * 2 + 2_000 * 10) / 1e6, abs=0.01)
    assert float(haiku[8]) == pytest.approx(216 * 20 / 3600, abs=0.05)
