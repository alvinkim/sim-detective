import numpy as np
import pytest

from simdet.scenario.world import World
from simdet.sim.cell import Fault, SocRangeError, State, initial_state, simulate
from simdet.sim.faults import SHIFT_CAUSES, magnitude, make_fault
from simdet.sim.profiles import regime_profile


def euler_reference(p, fault, state, current):
    """Spec 5.1 written as a plain loop."""
    soc, v1, v2, temp = state.soc, state.v1, state.v2, state.temp
    out = []
    for i in current:
        r0 = p.r0_ref * fault.r0_scale * (1 + p.alpha * (p.t_ref - temp))
        out.append((p.ocv0 + p.k_ocv * soc - i * r0 - v1 - v2, temp))
        dsoc = -i / (3600 * p.q_ah)
        dv1 = -v1 / p.tau1 + i * p.r1 / p.tau1
        dv2 = -v2 / p.tau2 + i * fault.r2 / p.tau2
        dtemp = (i * i * r0 - p.h_th * (temp - p.t_amb)) / p.c_th
        soc, v1, v2, temp = soc + dsoc, v1 + dv1, v2 + dv2, temp + dtemp
    return np.array(out), State(soc, v1, v2, temp)


def test_vectorised_simulation_matches_euler_loop(cfg):
    p = cfg.cell
    fault = Fault(r0_scale=1.2, r2=5e-4, soc_offset=-0.01)
    current, _ = regime_profile(cfg, "DYN")
    start = initial_state(p, fault, 0.75)
    traj, final = simulate(p, fault, start, current)
    ref, ref_final = euler_reference(p, fault, start, current)
    assert np.allclose(traj["v"], ref[:, 0], atol=1e-10)
    assert np.allclose(traj["temp"], ref[:, 1], atol=1e-9)
    for key in ("soc", "v1", "v2", "temp"):
        assert getattr(final, key) == pytest.approx(getattr(ref_final, key), abs=1e-9)


def test_soc_outside_range_raises(cfg):
    p = cfg.cell
    with pytest.raises(SocRangeError):
        simulate(p, Fault(), initial_state(p, Fault(), 0.75), np.full(8000, 50.0))


@pytest.mark.parametrize("regime", ["CC", "DYN"])
def test_healthy_residual_is_zero_mean_with_sensor_noise(cfg, regime):
    seg = World(cfg, Fault(), regime, seed=5).current
    resid = seg.resid[seg.visible_from:]
    sigma = cfg.cell.sigma_v
    assert abs(resid.mean()) < 0.15 * sigma
    # T_meas noise enters V_pred through r0(T_meas), so allow a little above SIGMA_V
    assert 0.95 * sigma < resid.std() < 1.10 * sigma


@pytest.mark.parametrize("cause", SHIFT_CAUSES)
@pytest.mark.parametrize("size", ["small", "large"])
def test_cause_makes_target_shift_in_cc(cfg, cause, size):
    target = cfg["faults"]["target_shift_v"][size]
    seg = World(cfg, make_fault(cause, magnitude(cause, size, cfg)), "CC", seed=11).current
    shift = seg.resid[seg.visible_from:].mean()
    assert shift < 0
    assert abs(shift) == pytest.approx(target, rel=0.10)
