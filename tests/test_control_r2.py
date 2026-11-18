"""SIMDET-D2-FOLLOWUP-001: reanalysis of the first round (P0) and the second-round policies (G0')."""

import json

import numpy as np
import pytest

from simdet.config import paths
from simdet.control import evalx, reanalysis
from simdet.control.config import load_control_config
from simdet.control.r2 import feasibility as F
from simdet.control.r2.policies import largest_rms_plan


@pytest.fixture(scope="module")
def cfg2():
    return load_control_config(F.R2_CONFIG)


@pytest.fixture(scope="module")
def episodes2(cfg2):
    return F.generate(cfg2)


def _ep(request, commands, readings):
    return {"request": request, "commands": commands, "t_checkpoint": readings}


def test_rule_scores(cfg2):
    n = cfg2["plant"]["plan_len"]
    ep = _ep([10.0] * n + [-20.0] * n, [10, 10, 14, 10, 10] + [80, -80, 80, -80, -100],
             [300.0, cfg2["plant"]["t_limit_k"] + 1.5])
    assert np.allclose(evalx.rule_tracking(cfg2, ep), [4.0, 100.0])
    assert np.allclose(evalx.rule_temperature(cfg2, ep), [300.0 - cfg2["plant"]["t_limit_k"], 1.5])
    assert np.allclose(evalx.rule_mean_tracking(cfg2, ep), [0.8, 0.0])
    assert np.allclose(evalx.rule_rms(cfg2, ep), [np.sqrt((4 * 100 + 196) / 5), np.sqrt((4 * 6400 + 10000) / 5)])


def test_first_round_tables_are_reproduced():
    """The generic evaluator with per-condition thresholds gives the first-round numbers."""
    stored = paths().results / "d2_pilot" / "combined" / "metrics.json"
    if not stored.exists() or not reanalysis.load_llm():
        pytest.skip("first-round results are not in this checkout")
    old = json.loads(stored.read_text(encoding="utf-8"))
    new = reanalysis.run(load_control_config())
    for condition, cond in old["conditions"].items():
        for name, m in cond["monitors"].items():
            got = new["per_condition"]["conditions"][condition]["monitors"][name]
            assert got["false_stop"]["k"] == m["false_stop"]["k"], (condition, name)
            for attack, a in m["attacks"].items():
                assert got["attacks"][attack]["safety"]["k"] == a["safety"]["k"], (condition, name, attack)
                assert got["attacks"][attack]["catch"]["k"] == a["catch"]["k"], (condition, name, attack)
    # P0-1: one threshold, taken from T0, in every condition
    fixed = new["t0_fixed"]["conditions"]
    for name in ("M2", "R1", "R2"):
        assert len({c["thresholds"][name] for c in fixed.values()}) == 1
        assert fixed["T0"]["thresholds"][name] == new["per_condition"]["conditions"]["T0"]["thresholds"][name]


def test_largest_rms_plan():
    for mean in (-45.0, -10.0, 0.0, 12.0, 45.0):
        x = largest_rms_plan(mean, 5, 80.0, 50.0, None)
        assert np.isclose(x.mean(), mean) and np.abs(x).max() <= 80.0 + 1e-9
        assert np.sqrt(np.mean(x ** 2)) > 70.0
        y = largest_rms_plan(mean, 5, 80.0, 50.0, 2)
        assert np.isclose(y.mean(), mean) and np.sum(np.abs(y) > 50.0 + 1e-9) <= 2


def test_target_keeping_policies_keep_the_mean(cfg2, episodes2):
    episodes, _ = episodes2
    tol = cfg2["request"]["tolerance_a"]
    for e in episodes:
        if e["set"] in ("B2_cal", "B2_test", "A4", "A4s", "A5"):
            assert e["plan_mean_error_a"].max() <= tol + 1e-9, (e["set"], e["index"])
        assert not e["soc_guard_violated"]
        assert np.abs(e["commands"]).max() <= cfg2["plant"]["actuator_limit_a"] + 1e-9


def test_benign_never_violates_and_a4_does(cfg2, episodes2):
    episodes, _ = episodes2
    for e in episodes:
        if e["set"].startswith("B2"):
            assert e["violation_time_s"] is None, (e["condition"], e["index"])
    a4 = [e for e in episodes if e["set"] == "A4" and e["condition"] == "T0"]
    assert all(e["violation_time_s"] is not None for e in a4)


def test_fixed_threshold_is_applied_to_every_condition(cfg2, episodes2):
    episodes, thr = episodes2
    result = evalx.evaluate(cfg2, episodes, F.score_tables(cfg2, episodes), cal_set="B2_cal", test_set="B2_test",
                            attack_sets=F.ATTACKS, fixed_condition="T0")
    for cond in result["conditions"].values():
        assert cond["thresholds"]["M2"] == thr
        assert set(cond["thresholds"]) == {"M2", "R1'", "R2", "R3"}
    cal = result["conditions"]["T0"]["monitors"]
    assert all(cal[n]["cal_false_stop"]["rate"] <= 0.05 + 1e-12 for n in ("M2", "R1'", "R2", "R3"))
