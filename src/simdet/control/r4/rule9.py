"""R9: cell temperatures from the cell voltages, without a thermal model and without prediction.

1. Check pulse: R0 factor s_i of every cell, taking the cell temperature as the ambient one.
2. Operation: V_i = OCV(soc) - v1 - I r0_ref s_i (1 + alpha (t_ref - T_i)) is solved for T_i by
   least squares over the latest samples of the segment: as many as it takes for the sum of I^2
   to reach `r9_energy_a2s` (60 s at 30 A), at most `r9_max_window_s`. With less than
   `r9_min_energy_a2s` in that window the last estimate is kept.
3. Score: largest estimated cell temperature at the checkpoint, minus the limit.

It uses the same electrical quantities as the twin (alpha, r0_ref, OCV, v1, SOC) and nothing of
the thermal model (heat capacity, cooling, conduction).
"""

from __future__ import annotations

import numpy as np

from simdet.control.config import ControlConfig
from simdet.sim.cell import CellParams, ocv


class VoltTemp:
    def __init__(self, cfg: ControlConfig, cell: CellParams, n: int, t_amb: float):
        self.cell, self.t_amb = cell, float(t_amb)
        rules = cfg["rules"]
        self.energy, self.min_energy = float(rules["r9_energy_a2s"]), float(rules["r9_min_energy_a2s"])
        self.max_window = int(rules["r9_max_window_s"])
        self.s = np.ones(n)
        self.temp = np.full(n, float(t_amb))

    def _drop(self, v_meas, soc, v1) -> np.ndarray:
        return (ocv(self.cell, np.asarray(soc)) - np.asarray(v1))[:, None] - np.asarray(v_meas)   # I R0_i

    def fit_r0(self, current, v_meas, soc, v1) -> np.ndarray:
        p = self.cell
        current = np.asarray(current, dtype=float)
        on = np.abs(current) > 1e-9
        r_meas = (self._drop(v_meas, soc, v1)[on] / current[on, None]).mean(axis=0)
        self.s = r_meas / (p.r0_ref * (1.0 + p.alpha * (p.t_ref - self.t_amb)))
        return self.s

    def advance(self, current, v_meas, soc, v1) -> None:
        p = self.cell
        current = np.asarray(current, dtype=float)
        total = np.cumsum((current * current)[::-1])
        n = min(int(np.searchsorted(total, self.energy)) + 1, self.max_window, current.size)
        i = current[-n:]
        if (i * i).sum() < self.min_energy:
            return
        u = (i[:, None] * self._drop(v_meas, soc, v1)[-n:]).sum(axis=0) / (p.r0_ref * self.s * (i * i).sum())
        self.temp = p.t_ref - (u - 1.0) / p.alpha

    def score(self, t_limit_k: float) -> float:
        return float(self.temp.max()) - t_limit_k
