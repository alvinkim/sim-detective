"""True system: 1RC(+optional second RC) ECM with a lumped thermal model (spec 5.1).

Forward Euler with a 1 s step. Sample k holds the state at t = k s and the
voltage computed from that state and the current applied during [k, k+1).
The recurrences are linear in each state, so they are evaluated in closed
vectorised form; tests compare against a plain Euler loop.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import lfilter


@dataclass(frozen=True)
class CellParams:
    q_ah: float
    ocv0: float
    k_ocv: float
    r0_ref: float
    alpha: float
    t_ref: float
    r1: float
    tau1: float
    tau2: float
    c_th: float
    h_th: float
    t_amb: float
    sigma_v: float
    sigma_t: float


@dataclass(frozen=True)
class Fault:
    """What is planted in the true system. The default is the healthy cell."""

    r0_scale: float = 1.0
    r2: float = 0.0
    t_bias: float = 0.0
    soc_offset: float = 0.0  # actual initial SOC minus the SOC the twin believes
    noise_mult: float = 1.0  # multiplier on sigma_v


@dataclass(frozen=True)
class State:
    soc: float
    v1: float
    v2: float
    temp: float


class SocRangeError(ValueError):
    """The true SOC left the range where the linear OCV is valid."""


def initial_state(p: CellParams, fault: Fault, soc_believed: float) -> State:
    return State(soc=soc_believed + fault.soc_offset, v1=0.0, v2=0.0, temp=p.t_amb)


def ocv(p: CellParams, soc):
    return p.ocv0 + p.k_ocv * soc


def r0(p: CellParams, temp, r0_scale: float = 1.0):
    return p.r0_ref * r0_scale * (1.0 + p.alpha * (p.t_ref - temp))


def _rc(y0: float, gain: float, tau: float, current: np.ndarray) -> np.ndarray:
    """y[k+1] = y[k] * (1 - 1/tau) + current[k] * gain / tau, returned with length n+1."""
    a = 1.0 - 1.0 / tau
    out = np.empty(current.size + 1)
    out[0] = y0
    if current.size:
        out[1:], _ = lfilter([gain / tau], [1.0, -a], current, zi=[a * y0])
    return out


def simulate(
    p: CellParams,
    fault: Fault,
    state: State,
    current: np.ndarray,
    soc_limits: tuple[float, float] | None = (0.2, 0.8),
) -> tuple[dict[str, np.ndarray], State]:
    """Run the true system over `current` (A, discharge positive, one value per second).

    Returns noise-free trajectories (soc, v1, v2, temp, v; one row per sample) and the
    state after the last sample. Raises SocRangeError if SOC leaves `soc_limits`.
    """
    current = np.asarray(current, dtype=float)
    n = current.size

    soc = np.empty(n + 1)
    soc[0] = state.soc
    soc[1:] = state.soc - np.cumsum(current) / (3600.0 * p.q_ah)
    if soc_limits is not None:
        lo, hi = soc_limits
        if soc.min() < lo - 1e-12 or soc.max() > hi + 1e-12:
            raise SocRangeError(f"soc left [{lo}, {hi}]: min={soc.min():.4f} max={soc.max():.4f}")

    v1 = _rc(state.v1, p.r1, p.tau1, current)
    v2 = _rc(state.v2, fault.r2, p.tau2, current) if (fault.r2 or state.v2) else np.zeros(n + 1)

    # theta = temp - t_amb;  theta[k+1] = a[k] * theta[k] + q[k]
    heat = current**2 * p.r0_ref * fault.r0_scale
    a = 1.0 - (heat * p.alpha + p.h_th) / p.c_th
    q = heat * (1.0 + p.alpha * (p.t_ref - p.t_amb)) / p.c_th
    prod = np.empty(n + 1)
    prod[0] = 1.0
    np.cumprod(a, out=prod[1:])
    theta = np.empty(n + 1)
    theta[0] = state.temp - p.t_amb
    theta[1:] = prod[1:] * (theta[0] + np.cumsum(q / prod[1:]))
    temp = theta + p.t_amb

    v = ocv(p, soc[:n]) - current * r0(p, temp[:n], fault.r0_scale) - v1[:n] - v2[:n]
    traj = {"soc": soc[:n], "v1": v1[:n], "v2": v2[:n], "temp": temp[:n], "v": v}
    final = State(soc=float(soc[n]), v1=float(v1[n]), v2=float(v2[n]), temp=float(temp[n]))
    return traj, final


def measure(
    p: CellParams, fault: Fault, traj: dict[str, np.ndarray], rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Add sensor noise and the temperature bias. Current is measured exactly."""
    n = traj["v"].size
    v_meas = traj["v"] + rng.normal(0.0, p.sigma_v * fault.noise_mult, n)
    t_meas = traj["temp"] + fault.t_bias + rng.normal(0.0, p.sigma_t, n)
    return v_meas, t_meas
