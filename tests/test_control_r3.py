"""SIMDET-D2-FOLLOWUP-002: two-node thermal plant, observer, rules and attacks (G0'')."""

import copy

import numpy as np
import pytest

from simdet.control import evalx
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.r3 import feasibility as F
from simdet.control.r3 import thermal
from simdet.control.r3.plant import thermal_of
from simdet.sim.cell import Fault, State, simulate


@pytest.fixture(scope="module")
def cfg3():
    return load_control_config(F.R3_CONFIG)


@pytest.fixture(scope="module")
def small(cfg3):
    """A reduced run: all benign episodes, a few of each attack."""
    raw = copy.deepcopy(cfg3.raw)
    raw["episodes"].update(A4=6, A6=6, A7=4, A8=4)
    cfg = ControlConfig(raw, cfg3.cell)
    episodes, known = F.generate(cfg)
    return cfg, episodes, known


def test_without_heat_both_nodes_return_to_ambient(cfg3):
    th = thermal_of(cfg3)
    amb = 300.0
    tc, ts, t_c, t_s = thermal.simulate(th, amb + 15.0, amb + 9.0, amb, np.zeros(8 * 3600))
    assert abs(t_c - amb) < 1e-3 and abs(t_s - amb) < 1e-3
    assert np.all(np.diff(tc) <= 1e-12)          # the core only cools
    assert tc.min() >= amb - 1e-9 and ts.min() >= amb - 1e-9


def test_energy_is_conserved_without_heat_and_cooling(cfg3):
    th = thermal.Thermal.from_cell(cfg3.cell, 700.0, 300.0, 0.3, h=0.0)
    tc, ts, t_c, t_s = thermal.simulate(th, 320.0, 300.0, 290.0, np.zeros(3600))
    energy = th.c_c * tc + th.c_s * ts
    assert np.allclose(energy, energy[0]) and np.isclose(th.c_c * t_c + th.c_s * t_s, energy[0])
    assert abs(t_c - t_s) < 1e-6                 # the two nodes meet


def test_single_node_limit_matches_the_cell_model(cfg3):
    """R_cs -> 0: core and surface move together and follow the lumped model of simdet.sim.cell."""
    cell = cfg3.cell
    th = thermal.Thermal.from_cell(cell, 700.0, 300.0, 0.005)
    rng = np.random.default_rng(0)
    current = np.repeat(rng.uniform(-80.0, 80.0, 60), 60)
    tc, ts, t_c, t_s = thermal.simulate(th, cell.t_amb, cell.t_amb, cell.t_amb, current)
    traj, final = simulate(cell, Fault(), State(0.5, 0.0, 0.0, cell.t_amb), current, soc_limits=None)
    assert np.abs(tc - traj["temp"]).max() < 0.1 and abs(t_c - final.temp) < 0.1
    assert np.abs(tc - ts).max() < 0.15


def test_observer_recovers_the_core_temperature(cfg3):
    th = thermal_of(cfg3)
    amb = 298.15
    rng = np.random.default_rng(1)
    current = np.repeat(rng.uniform(-70.0, 70.0, 20), 60)
    tc, ts, t_c, t_s = thermal.simulate(th, amb + 6.0, amb + 4.0, amb, current)   # unknown hot core at the start
    obs = thermal.Observer(th, amb, ts[0], cfg3["twin_monitor"]["observer_l_s"], cfg3["twin_monitor"]["observer_l_c"])
    assert abs(obs.t_c - tc[0]) > 1.5
    obs.advance(current, np.append(ts[1:], t_s) + rng.normal(0.0, cfg3.cell.sigma_t, current.size))
    assert abs(obs.t_c - t_c) < 0.3 and abs(obs.t_s - t_s) < 0.2


def test_benign_never_violates_and_limits_hold(small):
    cfg, episodes, _ = small
    tol = cfg["request"]["tolerance_a"]
    for e in episodes:
        if e["set"].startswith("B3"):
            assert e["violation_time_s"] is None, (e["set"], e["index"])
        assert evalx.rule_mean_tracking(cfg, e).max() <= tol + 1e-9, (e["set"], e["index"])  # every policy keeps the mean
        assert np.abs(e["commands"]).max() <= cfg["plant"]["actuator_limit_a"] + 1e-9
        assert cfg["plant"]["soc_guard"][0] - 1e-9 <= e["soc_end"] <= cfg["plant"]["soc_guard"][1] + 1e-9


def test_derating_follows_the_ambient_temperature(cfg3):
    rows = cfg3["request"]["derating"]
    factors = [F.derating(cfg3, c + F.KELVIN) for c in (20.0, 24.9, 25.0, 29.9, 30.0, 35.0)]
    assert factors == [rows[0]["factor"]] * 2 + [rows[1]["factor"]] * 2 + [rows[2]["factor"]] * 2
    assert all(a >= b for a, b in zip(factors, factors[1:]))


def test_rule_adaptive_attack_stays_below_the_rule_thresholds(small):
    """A7 plans are below the R4 threshold it knows; the twin-adaptive A8 below the M2 threshold,
    except where the reading noise makes even the flat plan too hot."""
    cfg, episodes, known = small
    tables = F.score_tables(cfg, episodes, known["r4_fit"])
    for e in episodes:
        k = evalx.episode_key(e)
        if e["set"] == "A7":
            attack = np.arange(12) >= e["attack_start_plan"]
            assert np.all(tables["R4"][k][attack] < known["R4"])
        if e["set"] == "A8":
            assert np.mean(tables["M2"][k] < known["M2"]) >= 0.9


def test_thresholds_come_from_calibration_and_r5_combines(small):
    cfg, episodes, known = small
    result = evalx.evaluate(cfg, episodes, F.score_tables(cfg, episodes, known["r4_fit"]), cal_set="B3_cal",
                            test_set="B3_test", attack_sets=F.ATTACKS, fixed_condition="T0", combos=F.COMBOS)
    cond = result["conditions"]["T0"]
    for name in ("R2", "R4", "M2"):
        assert cond["thresholds"][name] == known[name]
    for name in ("R1'", "R2", "R3", "R4", "R5", "M2"):
        assert cond["monitors"][name]["cal_false_stop"]["rate"] <= 0.05 + 1e-12
    stops = cond["stops"]
    for k, s in stops["R5"].items():   # R5 uses its own (higher) thresholds, so it never stops before both parts
        assert s is None or min(x for x in (stops["R2"][k], stops["R4"][k]) if x is not None) <= s
