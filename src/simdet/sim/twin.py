"""Twin: nominal-parameter prediction from the believed initial SOC (spec 5.3)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simdet.sim.cell import CellParams, _rc, ocv, r0


@dataclass(frozen=True)
class TwinState:
    soc: float
    v1: float


def twin_initial(soc_believed: float) -> TwinState:
    return TwinState(soc=soc_believed, v1=0.0)


def twin_predict(
    p: CellParams, state: TwinState, current: np.ndarray, t_meas: np.ndarray
) -> tuple[np.ndarray, TwinState]:
    """V_pred = ocv(soc_twin) - I * r0(T_meas) - v1_twin, with coulomb-counted SOC."""
    current = np.asarray(current, dtype=float)
    n = current.size
    soc = np.empty(n + 1)
    soc[0] = state.soc
    soc[1:] = state.soc - np.cumsum(current) / (3600.0 * p.q_ah)
    v1 = _rc(state.v1, p.r1, p.tau1, current)
    v_pred = ocv(p, soc[:n]) - current * r0(p, np.asarray(t_meas, dtype=float)) - v1[:n]
    return v_pred, TwinState(soc=float(soc[n]), v1=float(v1[n]))
