"""Oracle tests (spec 12).

Two rows of the spec table do not hold with the spec's own equations and default
parameters; they are kept as strict xfails next to the statement that does hold.
See scenarios/GENERATION_REPORT.md.
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


@pytest.mark.xfail(strict=True, reason="spec 12 expects R0 and SOC0 to alias in CC; the extra "
                   "self-heating of a larger R0 shows in T_meas and rejects SOC0")
@pytest.mark.parametrize("cause", ["R0", "SOC0"])
def test_cc_r0_and_soc0_are_jointly_consistent(cfg, cause):
    result = oracle_of(cfg, world(cfg, cause, "small", "CC"), cause)
    assert {"R0", "SOC0"} <= set(result.consistent_set)


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
    for duration in (60, 600, 900):
        out = experiment_outcome(cfg, w, "cc_run", {"current_a": 25, "duration_s": duration}, before, cause)
        assert out["class"] == "useless"


@pytest.mark.xfail(strict=True, reason="spec 12 expects cc_run never to resolve; at a current "
                   "other than the regime's 25 A it separates SOC0 (constant offset) from ST")
def test_cc_run_is_never_resolving_at_any_current(cfg):
    w = world(cfg, "SOC0", "large", "CC")
    before = oracle_of(cfg, w, "SOC0").consistent_set
    out = experiment_outcome(cfg, w, "cc_run", {"current_a": 5, "duration_s": 600}, before, "SOC0")
    assert out["class"] != "resolving"


def test_h_and_n_scenarios(cfg):
    assert oracle_of(cfg, world(cfg, "H", None, "DYN"), "H").consistent_set == ("H",)
    for size in ("small", "large"):
        assert oracle_of(cfg, world(cfg, "N", size, "CC"), "N").consistent_set == ("N",)


def test_generated_set_meets_checks_except_cc_aliasing(cfg, scenario_set):
    from simdet.scenario.generate import run_checks

    checks = {c["name"]: c["failures"] for c in run_checks(scenario_set["privates"])}
    cc = "CC scenarios of R0, SOC0, TB, ST have a consistent set of size >= 2"
    assert all(not failures for name, failures in checks.items() if name != cc)
    # the known gap: R0 and TB are identifiable in CC through the temperature channel
    assert {f["cause"] for f in checks[cc]} == {"R0", "TB"}
    assert not scenario_set["result"]["unfilled"]
