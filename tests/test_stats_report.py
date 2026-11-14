import json

import pytest

from simdet.agent.mock import make_mock
from simdet.agent.runner import dumps, run_episode
from simdet.score import stats
from simdet.score.grade import grade_episode
from simdet.score.report import write_report


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
            for private in scenario_set["privates"][:12]:
                record = run_episode(client, cfg, scenario_set["publics"][private["id"]], "A")
                record["grade"] = grade_episode(cfg, record, private)
                f.write(dumps(record) + "\n")
    out = write_report(cfg, [run_dir], run_dir, {"requested": 60, "generated": 60, "discarded": [],
                                                 "unfilled": [], "checks": []})
    for name in ("summary.md", "examples.md", "fig_overclaim.png", "fig_confusion.png", "fig_experiment.png"):
        assert (out / name).stat().st_size > 0
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "Over-abstain rate" in summary and "mock_always_abstain" in summary
    first = json.loads((run_dir / "episodes.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert {"responses", "answer", "grade", "usage", "cost_usd", "prompt_version"} <= set(first)
