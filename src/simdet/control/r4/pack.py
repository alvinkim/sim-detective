"""Series pack: n cells with the same current, one thermal node each (FOLLOWUP-003, 3).

    C dT_i/dt = I^2 R0_i(T_i) - h_i (T_i - T_amb) - k (T_i - T_{i-1}) - k (T_i - T_{i+1})
    R0_i(T) = r0_ref s_i (1 + alpha (t_ref - T))            as in simdet.sim.cell
    V_i = OCV(soc) - I R0_i(T_i) - v1                       1RC, the same for every cell

Forward Euler, 1 s step. Sample k is the state at t = k s; the current of sample k acts during
[k, k+1). With one cell and k = 0 this is the lumped model of simdet.sim.cell.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from simdet.sim.cell import CellParams, _rc, ocv


@dataclass(frozen=True)
class Pack:
    cell: CellParams
    k: float                 # W/K between neighbours
    r0_scale: np.ndarray     # per cell
    h: np.ndarray            # W/K per cell

    @property
    def n(self) -> int:
        return int(self.r0_scale.size)

    @classmethod
    def healthy(cls, cell: CellParams, n: int, k: float) -> "Pack":
        return cls(cell, float(k), np.ones(n), np.full(n, cell.h_th))

    def with_fault(self, cell_index: int | None, r0_scale: float = 1.0, h_scale: float = 1.0) -> "Pack":
        """`cell_index` is 0-based; None returns the pack unchanged."""
        if cell_index is None:
            return self
        s, h = self.r0_scale.copy(), self.h.copy()
        s[cell_index] *= r0_scale
        h[cell_index] *= h_scale
        return replace(self, r0_scale=s, h=h)

    def loss_matrix(self) -> np.ndarray:
        """(diag(h) + k Laplacian) / C: heat leaving each cell per kelvin above ambient, per second."""
        n = self.n
        lap = np.zeros((n, n))
        for i in range(n - 1):
            lap[i, i] += 1.0
            lap[i + 1, i + 1] += 1.0
            lap[i, i + 1] -= 1.0
            lap[i + 1, i] -= 1.0
        return (np.diag(self.h) + self.k * lap) / self.cell.c_th


def simulate(pack: Pack, temps, t_amb: float, current) -> tuple[np.ndarray, np.ndarray]:
    """Cell temperatures at every sample (len(current) x n) and after the last one."""
    p = pack.cell
    m = pack.loss_matrix()
    g = p.r0_ref * pack.r0_scale / p.c_th
    theta = np.asarray(temps, dtype=float) - t_amb
    base = 1.0 + p.alpha * (p.t_ref - t_amb)
    out = np.empty((len(current), pack.n))
    for k, i in enumerate(current):
        out[k] = theta
        theta = theta + i * i * g * (base - p.alpha * theta) - m @ theta
    return out + t_amb, theta + t_amb


def peak(pack: Pack, temps, t_amb: float, current) -> float:
    """Largest cell temperature during `current` and at its end."""
    traj, end = simulate(pack, temps, t_amb, current)
    return float(max(traj.max(), end.max())) if len(current) else float(np.max(temps))


def electrical(pack: Pack, soc0: float, v1_0: float, current) -> tuple[np.ndarray, np.ndarray, float, float]:
    """SOC and v1 at every sample and after the last one (the same for every cell)."""
    p = pack.cell
    current = np.asarray(current, dtype=float)
    soc = soc0 - np.concatenate([[0.0], np.cumsum(current)]) / (3600.0 * p.q_ah)
    v1 = _rc(v1_0, p.r1, p.tau1, current)
    return soc[:-1], v1[:-1], float(soc[-1]), float(v1[-1])


def r0(pack: Pack, temps) -> np.ndarray:
    p = pack.cell
    return p.r0_ref * pack.r0_scale * (1.0 + p.alpha * (p.t_ref - np.asarray(temps)))


def voltages(pack: Pack, soc, v1, temps, current) -> np.ndarray:
    """Noise-free cell voltages (samples x n)."""
    current = np.asarray(current, dtype=float)
    return (ocv(pack.cell, np.asarray(soc)) - np.asarray(v1))[:, None] - current[:, None] * r0(pack, temps)
