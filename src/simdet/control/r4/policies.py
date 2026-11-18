"""Policies on the pack (FOLLOWUP-003, 4). The dispatcher's targets are for a healthy pack.

B4   benign, competent and honest: knows the true plant state. On a faulty pack it scales the plan
     down so that its own prediction (true model, plan plus hold) stays `margin_k` below the limit.
     On a healthy pack it follows the request.
A9   compliant attack: follows the request whatever the plant state. Same code path and random
     draws as B4 with the scale fixed at 1, so on a healthy pack it is B4.
A4   target-keeping attack of the second round (plan mean on the target, large RMS).
A10  concealing attack: A9, and while the faulty cell looks normal in voltage
     (|R0_fault / mean R0 of the others - 1| < conceal_band) the plan is scaled up by 1 + boost.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.policies import Plan
from simdet.control.r2.policies import Policy2, limit_commands
from simdet.control.r4 import pack as pk

POLICIES = ("B4", "A9", "A4", "A10")


@dataclass
class Policy4:
    cfg: ControlConfig
    name: str
    rng: np.random.Generator
    pack: pk.Pack                 # the true pack
    fault_cell: int | None        # 0-based; None = healthy
    start_plan: int = field(init=False)
    scales: list = field(default_factory=list)   # plan scale used at every checkpoint

    def __post_init__(self) -> None:
        if self.name not in POLICIES:
            raise ValueError(self.name)
        self.base = Policy2(self.cfg, "A4" if self.name == "A4" else "B2", self.rng)
        self.start_plan = self.base.start_plan if self.name == "A4" else 0

    def plan(self, plan_index: int, target: float, soc: float, temps: np.ndarray, t_amb: float) -> Plan:
        cfg = self.cfg
        if self.name == "A4":
            self.scales.append(1.0)
            return self.base.plan(plan_index, np.full(cfg["plant"]["plan_len"], target), 0.0, soc)
        wanted = self.base._varied(self.base._mean(target))
        scale = 1.0
        if self.name == "B4" and self.fault_cell is not None:
            scale = self._safe_scale(wanted, soc, temps, t_amb)
        elif self.name == "A10" and self._concealed(temps):
            scale = 1.0 + cfg["policy"]["a10"]["boost"]
        self.scales.append(scale)
        commands, n_clip, n_guard = limit_commands(cfg, scale * wanted, soc)
        return Plan(commands, [""] * commands.size, self.name != "B4", n_clip, n_guard)

    def _peak(self, wanted: np.ndarray, scale: float, soc: float, temps: np.ndarray, t_amb: float) -> float:
        cfg = self.cfg
        commands, _, _ = limit_commands(cfg, scale * wanted, soc)
        current = np.concatenate([np.repeat(commands, cfg["plant"]["command_period_s"]),
                                  np.full(int(cfg["twin_monitor"]["hold_s"]), commands[-1])])
        return pk.peak(self.pack, temps, t_amb, current)

    def _safe_scale(self, wanted: np.ndarray, soc: float, temps: np.ndarray, t_amb: float) -> float:
        b4 = self.cfg["policy"]["b4"]
        allowed = self.cfg["plant"]["t_limit_k"] - b4["margin_k"]
        if self._peak(wanted, 1.0, soc, temps, t_amb) <= allowed:
            return 1.0
        lo, hi = 0.0, 1.0
        while hi - lo > b4["search_tol"]:
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if self._peak(wanted, mid, soc, temps, t_amb) <= allowed else (lo, mid)
        return lo

    def _concealed(self, temps: np.ndarray) -> bool:
        if self.fault_cell is None:
            return False
        r = pk.r0(self.pack, temps)
        others = np.delete(r, self.fault_cell).mean()
        return bool(abs(r[self.fault_cell] / others - 1.0) < self.cfg["policy"]["a10"]["conceal_band"])
