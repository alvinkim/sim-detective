"""Per-hypothesis least-squares fit (spec 6.1).

Each hypothesis simulates the spec 5.1 equations from the start of the segment with one
free parameter and is scored on the logged samples of V_meas and T_meas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares

from simdet.sim.cell import CellParams, Fault, State, simulate
from simdet.sim.profiles import constant_blocks

HYPOTHESES = ("H", "R0", "SOC0", "TB", "ST")

# Free parameter per hypothesis: (unit that makes it O(1), lower, upper, start), in scaled units.
_PARAM = {
    "R0": (0.1, -5.0, 30.0, 0.0),     # r0_scale - 1
    "SOC0": (0.01, -20.0, 20.0, 0.0), # actual - believed initial SOC
    "TB": (1.0, -40.0, 40.0, 0.0),    # t_bias, K
    "ST": (1e-3, 0.0, 20.0, 0.1),     # R2, ohm
}


@dataclass(frozen=True)
class OracleData:
    """A segment as the oracle sees it: full current history, measurements, and which
    samples were logged."""

    current: np.ndarray
    v_meas: np.ndarray
    t_meas: np.ndarray
    v_pred: np.ndarray
    visible_from: int
    soc_believed: float

    @classmethod
    def from_segment(cls, seg, soc_believed: float) -> "OracleData":
        return cls(seg.current, seg.v_meas, seg.t_meas, seg.v_pred, seg.visible_from, soc_believed)


@dataclass(frozen=True)
class FitResult:
    hypothesis: str
    param: float | None
    normalized_rms: float  # both channels pooled
    rms_v: float           # voltage channel alone, in units of sigma_hat
    rms_t: float           # temperature channel alone, in units of SIGMA_T


def estimate_sigma(data: OracleData) -> float:
    """sigma_hat = std(diff(resid)) / sqrt(2), using only steps inside constant-current blocks."""
    resid = data.v_meas - data.v_pred
    diffs = [
        np.diff(resid[a:b])
        for a, b in constant_blocks(data.current, data.visible_from)
        if b - a >= 2
    ]
    return float(np.std(np.concatenate(diffs)) / np.sqrt(2.0))


def _fault_for(hypothesis: str, value: float) -> Fault:
    if hypothesis == "R0":
        return Fault(r0_scale=1.0 + value)
    if hypothesis == "SOC0":
        return Fault(soc_offset=value)
    if hypothesis == "TB":
        return Fault(t_bias=value)
    if hypothesis == "ST":
        return Fault(r2=value)
    return Fault()


def _residuals(p: CellParams, data: OracleData, fault: Fault, sigma_hat: float) -> np.ndarray:
    state = State(soc=data.soc_believed + fault.soc_offset, v1=0.0, v2=0.0, temp=p.t_amb)
    traj, _ = simulate(p, fault, state, data.current, soc_limits=None)
    s = slice(data.visible_from, None)
    rv = (data.v_meas[s] - traj["v"][s]) / sigma_hat
    rt = (data.t_meas[s] - traj["temp"][s] - fault.t_bias) / p.sigma_t
    return np.concatenate([rv, rt])


def fit_hypothesis(p: CellParams, data: OracleData, hypothesis: str, sigma_hat: float) -> FitResult:
    """Best single-parameter explanation of the logged V_meas and T_meas under a hypothesis.

    normalized_rms pools both channels: voltage errors in units of sigma_hat and
    temperature errors in units of SIGMA_T.
    """
    def result(param: float | None, r: np.ndarray) -> FitResult:
        half = r.size // 2
        rms = lambda x: float(np.sqrt(np.mean(x**2)))
        return FitResult(hypothesis, param, rms(r), rms(r[:half]), rms(r[half:]))

    if hypothesis == "H":
        return result(None, _residuals(p, data, Fault(), sigma_hat))
    unit, lo, hi, start = _PARAM[hypothesis]
    sol = least_squares(
        lambda x: _residuals(p, data, _fault_for(hypothesis, x[0] * unit), sigma_hat),
        x0=[start], bounds=([lo], [hi]),
    )
    return result(float(sol.x[0] * unit), sol.fun)
