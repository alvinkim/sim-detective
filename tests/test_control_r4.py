"""SIMDET-D2-FOLLOWUP-003: series pack, hidden plant state, estimator, rules (G0''')."""

import copy

import numpy as np
import pytest

from simdet.control import evalx
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.r4 import feasibility as F
from simdet.control.r4 import pack as pk
from simdet.control.r4.estimator import Twin
from simdet.control.r4.plant import nominal_pack, pulse_current, run_episode
from simdet.control.r4.policies import Policy4
from simdet.sim.cell import Fault, State, simulate


@pytest.fixture(scope="module")
def cfg4():
    return load_control_config(F.R4_CONFIG)


@pytest.fixture(scope="module")
def small(cfg4):
    """A reduced run: every plant state and request kind in the benign sets, a few attacks."""
    raw = copy.deepcopy(cfg4.raw)
    raw["episodes"].update(B4_cal=40, B4_test=20, A9=6, A4=3, A10=3)
    cfg = ControlConfig(raw, cfg4.cell)
    return cfg, F.generate(cfg)


def test_one_cell_without_conduction_is_the_single_cell_model(cfg4):
    cell = cfg4.cell
    one = pk.Pack.healthy(cell, 1, 0.0).with_fault(0, r0_scale=1.4)
    rng = np.random.default_rng(0)
    current = np.repeat(rng.uniform(-80.0, 80.0, 60), 60)
    temps, end = pk.simulate(one, [cell.t_amb], cell.t_amb, current)
    soc, v1, soc_end, v1_end = pk.electrical(one, 0.5, 0.0, current)
    v = pk.voltages(one, soc, v1, temps, current)
    traj, final = simulate(cell, Fault(r0_scale=1.4), State(0.5, 0.0, 0.0, cell.t_amb), current, soc_limits=None)
    assert np.abs(temps[:, 0] - traj["temp"]).max() < 1e-6 and abs(end[0] - final.temp) < 1e-6
    assert np.abs(v[:, 0] - traj["v"]).max() < 1e-9
    assert abs(soc_end - final.soc) < 1e-12 and abs(v1_end - final.v1) < 1e-12


def test_healthy_pack_is_symmetric_and_a_fault_breaks_it(cfg4):
    nominal = nominal_pack(cfg4)
    rng = np.random.default_rng(1)
    current = np.repeat(rng.uniform(-60.0, 60.0, 30), 60)
    temps, end = pk.simulate(nominal, np.full(6, 300.0), 300.0, current)
    assert np.abs(temps - temps[:, ::-1]).max() < 1e-9          # T_i = T_(7-i)
    assert np.ptp(temps, axis=1).max() < 1e-9                    # equal cooling: all six the same
    faulty, _ = pk.simulate(nominal.with_fault(2, h_scale=0.4), np.full(6, 300.0), 300.0, current)
    assert faulty[:, 2].max() > temps.max() + 0.5 and faulty[:, 2].max() == faulty.max()


def test_a_hot_cell_warms_its_neighbour_by_less_than_a_fifth(cfg4):
    """FOLLOWUP-003, 3: a cell 5 K hotter raises its neighbours by at most 1 K (steady state)."""
    nominal = nominal_pack(cfg4)
    for j in range(1, 5):
        q = np.zeros(6)
        q[j] = 1.0
        theta = np.linalg.solve(nominal.loss_matrix() * cfg4.cell.c_th, q)
        theta *= 5.0 / theta[j]
        assert np.delete(theta, j).max() <= 1.0


def test_check_pulse_gives_the_r0_factor_and_the_filter_follows_the_faulty_cell(cfg4):
    nominal = nominal_pack(cfg4)
    cell, amb = cfg4.cell, 305.15
    true = nominal.with_fault(3, r0_scale=1.6, h_scale=0.4)
    rng = np.random.default_rng(2)
    current = np.concatenate([pulse_current(cfg4), np.repeat(rng.uniform(25.0, 45.0, 40) * rng.choice([-1, 1], 40), 60)])
    temps, end = pk.simulate(true, np.full(6, amb), amb, current)
    soc, v1, _, _ = pk.electrical(true, 0.5, 0.0, current)
    v = pk.voltages(true, soc, v1, temps, current) + rng.normal(0.0, cell.sigma_v, temps.shape)
    t = temps[:, [0, 5]] + rng.normal(0.0, cell.sigma_t, (current.size, 2))
    twin = Twin(cfg4, nominal, amb)
    n0 = pulse_current(cfg4).size
    s = twin.fit_r0(current[:n0], v[:n0], soc[:n0], v1[:n0])
    assert abs(s[3] - 1.6) < 0.02 and np.abs(np.delete(s, 3) - 1.0).max() < 0.02
    twin.advance(current, v, t, soc, v1)
    assert end[3] - end[[0, 5]].max() > 3.0                       # the sensors do not show it
    assert np.abs(twin.temp - end).max() < 0.5
    assert abs(twin.c[3] - 0.4) < 0.15 and np.abs(np.delete(twin.c, 3) - 1.0).max() < 0.25


def test_benign_never_violates_and_follows_the_request_on_a_healthy_pack(small):
    cfg, episodes = small
    seen = set()
    for e in episodes:
        if not e["set"].startswith("B4"):
            continue
        seen.add((e["state"], e["kind"]))
        assert e["violation_time_s"] is None, (e["set"], e["index"])
        assert np.abs(e["commands"]).max() <= cfg["plant"]["actuator_limit_a"] + 1e-9
        if e["state"] == "F0":
            assert np.all(e["scales"] == 1.0)
            assert evalx.rule_mean_tracking(cfg, e).max() <= cfg["request"]["tolerance_a"] + 1e-9
    assert seen == {(s, k) for s in F.STATES for k in ("normal", "heavy")}


def test_compliant_attack_is_the_benign_policy_on_a_healthy_pack(cfg4):
    nominal = nominal_pack(cfg4)
    inp = F.episode_inputs(cfg4, nominal, "B4_cal", 0)
    assert inp["state"] == "F0"
    runs = []
    for name in ("B4", "A9"):
        inp = F.episode_inputs(cfg4, nominal, "B4_cal", 0)
        policy = Policy4(cfg4, name, inp["r_pol"], inp["pack"], inp["fault_cell"])
        runs.append(run_episode(cfg4, inp["pack"], nominal, policy, inp["targets"], inp["t_amb"], inp["r_noise"]))
    assert np.array_equal(runs[0]["commands"], runs[1]["commands"])
    assert np.array_equal(runs[0]["twin_scores"], runs[1]["twin_scores"])


def test_attacks_run_on_faulty_packs_only_and_a9_keeps_the_request(small):
    cfg, episodes = small
    for e in episodes:
        if e["set"] in F.ATTACKS:
            assert e["state"] != "F0" and e["fault_cell"] in (1, 2, 3, 4)   # 0-based: cells 2-5
        if e["set"] in ("A9", "A4"):
            assert evalx.rule_mean_tracking(cfg, e).max() <= cfg["request"]["tolerance_a"] + 1e-9


def test_thresholds_hold_the_false_stop_target_on_calibration(small):
    cfg, episodes = small
    cal = [e for e in episodes if e["set"] == "B4_cal"]
    result = F.evaluate(cfg, episodes, F.score_tables(cfg, episodes, F.fits(cfg, cal)))
    for name in F.MONITORS[1:]:
        assert result["monitors"][name]["cal_false_stop"]["all"]["rate"] <= 0.05 + 1e-12, name
    stops = result["stops"]
    for k, s in stops["R8"].items():   # R8 has its own (higher) thresholds: never before all of its parts
        parts = [stops[a][k] for a in ("R2", "R6", "R7") if stops[a][k] is not None]
        assert s is None or (parts and min(parts) <= s)
    assert set(F.verdict(result)["attacks"]) == set(F.ATTACKS)


def test_r9_gives_the_cell_temperatures_without_a_thermal_model(small):
    cfg, episodes = small
    for e in episodes:
        err = (e["r9_est"] - e["t_true"])[1:]
        assert err.min() > -0.6, (e["set"], e["index"])          # the low side decides whether it warns in time
        assert np.abs(e["r9_s"] - e["s_hat"]).max() < 0.02       # pulse R0 without and with the thermal model


def test_monitor_models_do_not_change_the_episode_and_no_error_is_the_baseline(cfg4):
    from simdet.control.r4 import confirm as C
    from simdet.control.r4.plant import MonitorModel

    nominal = nominal_pack(cfg4)
    plan = C.load_plan()
    models = [MonitorModel("same", nominal)] + C.monitor_models(plan, nominal)
    assert len(models) == 25 and len({m.name for m in models}) == 25
    runs = []
    for extra in (None, models):
        inp = F.episode_inputs(cfg4, nominal, "A9", 2)
        policy = Policy4(cfg4, "A9", inp["r_pol"], inp["pack"], inp["fault_cell"])
        runs.append(run_episode(cfg4, inp["pack"], nominal, policy, inp["targets"], inp["t_amb"], inp["r_noise"], extra))
    a, b = runs
    assert np.array_equal(a["commands"], b["commands"]) and np.array_equal(a["twin_scores"], b["twin_scores"])
    assert np.array_equal(a["r9_est"], b["r9_est"]) and a["violation_time_s"] == b["violation_time_s"]
    same = b["model_scores"]["same"]
    assert np.allclose(same["M2"], b["twin_scores"]) and np.allclose(same["R9"], b["r9_est"].max(axis=1) - cfg4["plant"]["t_limit_k"])
    assert not np.allclose(b["model_scores"]["alpha+0.3"]["M2"], b["twin_scores"])
    assert not np.allclose(b["model_scores"]["v_bias_mv+5"]["R9"], same["R9"])
    assert np.allclose(b["model_scores"]["k+0.3"]["R9"], same["R9"])      # R9 has no thermal parameter
    assert set(C.setting_config(plan, "S-B")["episodes"].items()) >= {("seed", 20261201), ("A10", 120)}
