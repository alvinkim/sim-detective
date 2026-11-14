"""Oracle tests (spec 12).

In the CC regime only SOC0 and ST alias; R0 and TB are identified through the
temperature channel (SIMDET-FOLLOWUP-001 section 3). The spec's "cc_run never resolves"
holds only at the regime current and is kept as a strict xfail next to that statement.
"""

import pytest

from simdet.oracle.experiments import experiment_outcome, oracle_of
from simdet.scenario.world import World
from simdet.sim.faults import SHIFT_CAUSES, magnitude, make_fault


def world(cfg, cause, size, regime, seed=3):
    return World(cfg, make_fault(cause, magnitude(cause, size, cfg)), regime, seed)


@pytest.mark.parametrize("cause", ["SOC0", "ST"])
@pytest.mark.parametrize("size", ["small", "large"])
def test_cc_soc0_and_st_are_jointly_consistent(cfg, cause, size):
    result = oracle_of(cfg, world(cfg, cause, size, "CC"), cause)
    assert result.status == "ok"
    assert set(result.consistent_set) == {"SOC0", "ST"}


@pytest.mark.parametrize("cause", ["R0", "TB"])
@pytest.mark.parametrize("size", ["small", "large"])
def test_cc_r0_and_tb_are_identified_by_the_temperature_channel(cfg, cause, size):
    result = oracle_of(cfg, world(cfg, cause, size, "CC"), cause)
    assert result.status == "ok"
    assert result.consistent_set == (cause,)
    # the hypotheses that explain the voltage are rejected on temperature alone
    for other in {"SOC0", "ST"} if cause == "R0" else {"H", "SOC0", "ST"}:
        assert result.fits[other].rms_v < 1.15 and result.fits[other].rms_t >= 1.5


@pytest.mark.parametrize("cause", SHIFT_CAUSES)
def test_dyn_large_is_identifiable(cfg, cause):
    result = oracle_of(cfg, world(cfg, cause, "large", "DYN"), cause)
    assert result.status == "ok"
    assert result.consistent_set == (cause,)


@pytest.mark.parametrize("cause,other", [("R0", "TB"), ("TB", "R0")])
@pytest.mark.parametrize("duration", [5400, 7200])
def test_long_rest_separates_r0_and_tb_in_cc(cfg, cause, other, duration):
    w = world(cfg, cause, "small", "CC")
    w.run_experiment("rest_test", {"duration_s": duration})
    result = oracle_of(cfg, w, cause)
    assert cause in result.consistent_set
    assert other not in result.consistent_set and other not in result.gray


@pytest.mark.parametrize("cause", ["SOC0", "ST"])
@pytest.mark.parametrize("size", ["small", "large"])
def test_cc_run_at_the_regime_current_is_never_resolving(cfg, cause, size):
    w = world(cfg, cause, size, "CC")
    before = oracle_of(cfg, w, cause).consistent_set
    for duration in (60, 300, 400):
        out = experiment_outcome(cfg, w, "cc_run", {"current_a": 25, "duration_s": duration}, before, cause)
        assert out["class"] == "useless"


@pytest.mark.xfail(strict=True, reason="spec 12 expects cc_run never to resolve; at a current "
                   "other than the regime's 25 A it separates SOC0 (constant offset) from ST")
def test_cc_run_is_never_resolving_at_any_current(cfg):
    w = world(cfg, "SOC0", "large", "CC")
    before = oracle_of(cfg, w, "SOC0").consistent_set
    out = experiment_outcome(cfg, w, "cc_run", {"current_a": 5, "duration_s": 600}, before, "SOC0")
    assert out["class"] != "resolving"


def test_alias_audit_finds_no_signal_between_soc0_and_st(cfg):
    import copy

    from simdet.config import Config
    from simdet.scenario.generate import audit_designs
    from simdet.oracle.audit import alias_audit

    raw = copy.deepcopy(cfg.raw)
    raw["scenario"]["alias_audit"]["seeds"] = 20
    rows = alias_audit(Config(raw), audit_designs(Config(raw)))
    assert len(rows) == 8 and all(r["passed"] for r in rows)  # SOC0, ST x 6, 10, 15, 20 mV
    assert all(abs(r["mean"]) < 0.1 and r["share_above"] == 0 for r in rows)


def test_alias_audit_detects_an_unsaturated_branch(cfg):
    """With the earlier 1200 s pre-run the ST branch is still settling inside the window,
    and the audit must fail for the large size (the reason for SIMDET-DECISION-001 P2)."""
    import copy

    from simdet.config import Config
    from simdet.oracle.audit import alias_audit

    raw = copy.deepcopy(cfg.raw)
    raw["regimes"]["CC"].update(pre_s=1200, observe_s=1200)
    raw["scenario"]["alias_audit"]["seeds"] = 30
    row = alias_audit(Config(raw), [{"cause": "ST", "label": "large", "target_v": 0.016}])[0]
    assert not row["passed"] and row["mean"] > 3


def test_representative_experiments_fit_the_soc_guard(scenario_set):
    for p in scenario_set["privates"]:
        assert all(e["class"] != "rejected" for e in p["experiment_power"])
        same_current = [e for e in p["experiment_power"]
                        if e["name"] == "cc_run" and e["args"]["current_a"] == 25]
        assert all(e["class"] == "useless" for e in same_current)


def test_continuous_shift_covers_the_range_evenly(cfg, scenario_set):
    """D2: CC SOC0 / ST targets are one per twelfth of 6-20 mV; everything else keeps 8 / 16 mV."""
    for cause in ("SOC0", "ST"):
        targets = sorted(1e3 * p["magnitude"]["target_shift_v"] for p in scenario_set["privates"]
                         if p["regime"] == "CC" and p["cause"] == cause)
        assert len(targets) == 12
        width = 14 / 12
        assert [int((t - 6) // width) for t in targets] == list(range(12))
        sizes = [p["magnitude"]["size"] for p in scenario_set["privates"]
                 if p["regime"] == "CC" and p["cause"] == cause]
        assert sizes.count("6-13mV") == 6 and sizes.count("13-20mV") == 6
    for p in scenario_set["privates"]:
        if p["cause"] in ("R0", "TB") or (p["regime"] == "DYN" and p["cause"] in ("SOC0", "ST")):
            assert p["magnitude"]["target_shift_v"] in (0.008, 0.016)
            assert p["magnitude"]["size"] in ("small", "large")


def test_h_and_n_scenarios(cfg):
    assert oracle_of(cfg, world(cfg, "H", None, "DYN"), "H").consistent_set == ("H",)
    for size in ("small", "large"):
        assert oracle_of(cfg, world(cfg, "N", size, "CC"), "N").consistent_set == ("N",)


def test_generated_set_meets_all_checks(cfg, scenario_set):
    from simdet.scenario.generate import run_checks

    privates = scenario_set["privates"]
    assert all(not c["failures"] for c in run_checks(privates))
    assert not scenario_set["result"]["unfilled"] and not scenario_set["result"]["discarded"]
    assert len(privates) == 72
    assert sum(p["identifiable"] for p in privates) == 48
    not_identifiable = [p for p in privates if not p["identifiable"]]
    assert len(not_identifiable) == 24
    assert all(p["regime"] == "CC" and p["cause"] in ("SOC0", "ST") for p in not_identifiable)
