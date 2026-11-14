"""Cause definitions and magnitude calibration (spec 5.4, 5.5)."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from simdet.sim.cell import CellParams, Fault, initial_state, simulate
from simdet.sim.twin import twin_initial, twin_predict

CAUSES = ("H", "N", "R0", "SOC0", "TB", "ST")
LABELS = {
    "H": "no_change",
    "N": "noise_growth",
    "R0": "r0_increase",
    "SOC0": "soc_offset",
    "TB": "temp_sensor_bias",
    "ST": "structural_change",
}
CAUSE_OF_LABEL = {v: k for k, v in LABELS.items()}
SHIFT_CAUSES = ("R0", "SOC0", "TB", "ST")  # calibrated to the same mean residual shift

# Search range of the magnitude each shift cause is parameterised by.
_MAG_RANGE = {"R0": 2.0, "SOC0": 0.1, "TB": 40.0, "ST": 0.02}


def make_fault(cause: str, value: float = 0.0) -> Fault:
    """Fault for a cause ID. `value` is: N -> sigma_v multiplier, R0 -> r0_scale - 1,
    SOC0 -> SOC deficit (actual is lower than believed), TB -> t_bias in K, ST -> R2 in ohm."""
    if cause == "H":
        return Fault()
    if cause == "N":
        return Fault(noise_mult=value)
    if cause == "R0":
        return Fault(r0_scale=1.0 + value)
    if cause == "SOC0":
        return Fault(soc_offset=-value)
    if cause == "TB":
        return Fault(t_bias=value)
    if cause == "ST":
        return Fault(r2=value)
    raise ValueError(f"unknown cause: {cause}")


def mean_cc_shift(
    p: CellParams, fault: Fault, i_cc: float, pre_s: int, observe_s: int, soc_init: float
) -> float:
    """Noise-free mean of V - V_pred over the logged window of a constant-current run."""
    current = np.full(pre_s + observe_s, float(i_cc))
    traj, _ = simulate(p, fault, initial_state(p, fault, soc_init), current, soc_limits=None)
    v_pred, _ = twin_predict(p, twin_initial(soc_init), current, traj["temp"] + fault.t_bias)
    return float(np.mean((traj["v"] - v_pred)[pre_s:]))


@lru_cache(maxsize=None)
def _calibrate(cause, target_shift_v, i_cc, p, pre_s, observe_s, soc_init) -> float:
    def gap(value: float) -> float:
        shift = mean_cc_shift(p, make_fault(cause, value), i_cc, pre_s, observe_s, soc_init)
        return abs(shift) - target_shift_v

    lo, hi = 0.0, _MAG_RANGE[cause]
    if gap(hi) < 0:
        raise ValueError(f"{cause}: target shift {target_shift_v} V is out of reach")
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if gap(mid) < 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def calibrate(cause: str, target_shift_v: float, i_cc: float, cfg) -> float:
    """Magnitude of `cause` whose mean residual shift in the CC regime is `target_shift_v`
    in absolute value (all four causes shift the residual downward). Bisection."""
    if cause not in SHIFT_CAUSES:
        raise ValueError(f"{cause} is not calibrated by residual shift")
    cc = cfg["regimes"]["CC"]
    return _calibrate(
        cause, float(target_shift_v), float(i_cc), cfg.cell,
        int(cc["pre_s"]), int(cc["observe_s"]), float(cfg["sim"]["soc_init"]),
    )


def magnitude(cause: str, size: str | None, cfg) -> float:
    """Planted magnitude for a cause and size ('small' | 'large')."""
    if cause == "H":
        return 0.0
    f = cfg["faults"]
    if cause == "N":
        return float(f["noise_mult"][size])
    return calibrate(cause, f["target_shift_v"][size], f["calibration_current_a"], cfg)
