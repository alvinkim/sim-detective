"""Two-node thermal model and the observer of the twin monitor (FOLLOWUP-002, 3 and 4).

    C_c dT_c/dt = Q - (T_c - T_s) / R_cs
    C_s dT_s/dt = (T_c - T_s) / R_cs - h (T_s - T_amb)
    Q = I^2 R0(T_c),   R0 as in simdet.sim.cell

Forward Euler, 1 s step. Sample k is the state at t = k s; the current of sample k acts during
[k, k+1). Only the surface temperature T_s is measured.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simdet.sim.cell import CellParams


@dataclass(frozen=True)
class Thermal:
    c_c: float      # J/K, core
    c_s: float      # J/K, surface
    r_cs: float     # K/W, core to surface
    h: float        # W/K, surface to ambient
    r0_ref: float   # ohm at t_ref
    alpha: float    # 1/K
    t_ref: float    # K

    @classmethod
    def from_cell(cls, cell: CellParams, c_c: float, c_s: float, r_cs: float, h: float | None = None) -> "Thermal":
        return cls(c_c, c_s, r_cs, cell.h_th if h is None else h, cell.r0_ref, cell.alpha, cell.t_ref)


def simulate(th: Thermal, t_c: float, t_s: float, t_amb: float, current) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Core and surface temperature at every sample, and the state after the last one."""
    n = len(current)
    tc, ts = np.empty(n), np.empty(n)
    a, r0_ref, t_ref = th.alpha, th.r0_ref, th.t_ref
    kc, ks, g, h = 1.0 / th.c_c, 1.0 / th.c_s, 1.0 / th.r_cs, th.h
    for k in range(n):
        tc[k], ts[k] = t_c, t_s
        i = current[k]
        flow = (t_c - t_s) * g
        t_c, t_s = (t_c + kc * (i * i * r0_ref * (1.0 + a * (t_ref - t_c)) - flow),
                    t_s + ks * (flow - h * (t_s - t_amb)))
    return tc, ts, t_c, t_s


def peak_core(th: Thermal, t_c: float, t_s: float, t_amb: float, current) -> float:
    tc, _, t_end, _ = simulate(th, t_c, t_s, t_amb, current)
    return float(max(tc.max(), t_end)) if len(current) else t_c


class Observer:
    """Estimate of (T_c, T_s) from the commanded current and the surface readings.

    Each second: one model step, then a correction by the new reading y:
    T_s += l_s (y - T_s), T_c += l_c (y - T_s). The first reading sets both temperatures (the
    difference between core and surface is not known at the start).
    """

    def __init__(self, th: Thermal, t_amb: float, first_reading: float, l_s: float, l_c: float):
        self.th, self.t_amb, self.l_s, self.l_c = th, t_amb, l_s, l_c
        self.t_c = self.t_s = float(first_reading)

    def advance(self, current, readings) -> None:
        """`current[k]` acts for one second; `readings[k]` is the surface reading after it."""
        th = self.th
        a, r0_ref, t_ref = th.alpha, th.r0_ref, th.t_ref
        kc, ks, g, h, t_amb = 1.0 / th.c_c, 1.0 / th.c_s, 1.0 / th.r_cs, th.h, self.t_amb
        t_c, t_s, l_c, l_s = self.t_c, self.t_s, self.l_c, self.l_s
        for i, y in zip(current, readings):
            flow = (t_c - t_s) * g
            t_c, t_s = (t_c + kc * (i * i * r0_ref * (1.0 + a * (t_ref - t_c)) - flow),
                        t_s + ks * (flow - h * (t_s - t_amb)))
            e = y - t_s
            t_c, t_s = t_c + l_c * e, t_s + l_s * e
        self.t_c, self.t_s = t_c, t_s
