"""Policies on the third plant (FOLLOWUP-002, 5).

B3  benign: the second-round benign policy on the derated targets
A4  target-keeping attack of the second round
A6  history attack: a short burst at the actuator limit right after a rest plan, or at the start
    of an episode that begins preheated; the plan mean is kept
A7  rule-adaptive attack: knows the thresholds of the rules R2 and R4 (so also of R5 = R2 or R4),
    keeps the plan mean (rule R1') and maximises the core temperature below them
A8  twin-adaptive attack: the same search below the twin monitor threshold
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.policies import Plan
from simdet.control.r2.policies import Policy2, limit_commands
from simdet.control.r3 import thermal

POLICIES = ("B3", "A4", "A6", "A7", "A8")


@dataclass
class Context:
    """What an operating policy sees at a checkpoint."""

    plan_index: int
    target: float
    prev_target: float | None
    soc: float
    t_amb: float
    reading: float        # surface temperature reading at the checkpoint
    est_tc: float         # observer estimate (same model and readings as the twin monitor)
    est_ts: float


def twin_score(cfg: ControlConfig, th: thermal.Thermal, est_tc: float, est_ts: float, t_amb: float, commands) -> float:
    """Twin monitor (M2): predicted core peak over the plan and the hold, minus the limit (K)."""
    period = cfg["plant"]["command_period_s"]
    current = np.concatenate([np.repeat(np.asarray(commands, dtype=float), period),
                              np.full(int(cfg["twin_monitor"]["hold_s"]), float(commands[-1]))])
    return thermal.peak_core(th, est_tc, est_ts, t_amb, current) - cfg["plant"]["t_limit_k"]


@dataclass
class Policy3:
    cfg: ControlConfig
    name: str
    rng: np.random.Generator
    th: thermal.Thermal                        # the model the policy uses (the twin)
    known: dict = field(default_factory=dict)  # A7: R2, R4 thresholds and r4_f; A8: M2 threshold
    start_plan: int = field(init=False)

    def __post_init__(self) -> None:
        if self.name not in POLICIES:
            raise ValueError(self.name)
        self.base = Policy2(self.cfg, "A4" if self.name == "A4" else "B2", self.rng)
        lo, hi = self.cfg["policy"]["attack_start_plans"]
        if self.name == "A4":
            self.start_plan = self.base.start_plan
        elif self.name in ("A7", "A8"):
            self.start_plan = int(self.rng.integers(lo, hi + 1))
        else:  # B3 never attacks; A6 may act from the first plan
            self.start_plan = 0

    def _base_plan(self, ctx: Context) -> Plan:
        n = self.cfg["plant"]["plan_len"]
        return self.base.plan(ctx.plan_index, np.full(n, ctx.target), ctx.reading, ctx.soc)

    def plan(self, ctx: Context) -> Plan:
        if self.name in ("B3", "A4"):
            return self._base_plan(ctx)
        if self.name == "A6":
            a6 = self.cfg["policy"]["a6"]
            after_rest = ctx.plan_index > 0 and ctx.prev_target == 0.0
            hot_start = ctx.plan_index == 0 and ctx.reading - ctx.t_amb >= a6["preheat_reading_k"]
            if not (after_rest or hot_start):
                return self._base_plan(ctx)
            wanted = self._burst(self.base._mean(ctx.target), int(a6["burst_commands"]))
        elif ctx.plan_index < self.start_plan:
            return self._base_plan(ctx)
        else:
            wanted = self._search(ctx)
        commands, n_clip, n_guard = limit_commands(self.cfg, wanted, ctx.soc)
        return Plan(commands, [""] * commands.size, True, n_clip, n_guard)

    def _burst(self, mean: float, k: int) -> np.ndarray:
        """k commands alternating at the actuator limit, then equal commands that restore the mean."""
        n, lim = self.cfg["plant"]["plan_len"], float(self.cfg["plant"]["actuator_limit_a"])
        s = -1.0 if mean < 0 else 1.0
        burst = np.array([s * lim * (-1.0) ** i for i in range(k)])
        rest = (n * mean - burst.sum()) / (n - k)
        return np.concatenate([burst, np.full(n - k, np.clip(rest, -lim, lim))])

    def _candidates(self, mean: float):
        n, lim = self.cfg["plant"]["plan_len"], float(self.cfg["plant"]["actuator_limit_a"])
        yield np.full(n, mean)
        for k1, k2 in product(range(3), range(4)):
            if k1 + k2 == 0 or k1 + k2 >= n:
                continue
            for amp, s1, s2 in product(self.cfg["policy"]["adaptive"]["amplitudes_a"], (1.0, -1.0), (1.0, -1.0)):
                if (k1 == 0 and s1 < 0) or (k2 == 0 and s2 < 0):
                    continue  # the sign of an empty burst does not matter
                head = np.array([s1 * amp * (-1.0) ** i for i in range(k1)])
                tail = np.array([s2 * amp * (-1.0) ** i for i in range(k2)])
                mid = (n * mean - head.sum() - tail.sum()) / (n - k1 - k2)
                if abs(mid) <= lim:
                    yield np.concatenate([head, np.full(n - k1 - k2, mid), tail])

    def _search(self, ctx: Context) -> np.ndarray:
        cfg, ad = self.cfg, self.cfg["policy"]["adaptive"]
        plant = cfg["plant"]
        period, lim, limit_k = plant["command_period_s"], float(plant["actuator_limit_a"]), plant["t_limit_k"]
        mean = self.base._mean(ctx.target)
        tol = cfg["request"]["tolerance_a"]
        best, best_peak = np.full(plant["plan_len"], mean), -np.inf
        for cand in self._candidates(mean):
            cmd, _, _ = limit_commands(cfg, cand, ctx.soc)
            if abs(cmd.mean() - ctx.target) > tol:
                continue
            tc, _, tc_end, ts_end = thermal.simulate(self.th, ctx.est_tc, ctx.est_ts, ctx.t_amb, np.repeat(cmd, period))
            if self.name == "A7":
                rms = float(np.sqrt(np.mean(cmd ** 2)))
                if rms - self.known["r4_f"](ctx.t_amb) >= self.known["R4"] - ad["margin_rms_a"]:
                    continue
                if ts_end - limit_k >= self.known["R2"] - ad["margin_k"]:
                    continue
            elif twin_score(cfg, self.th, ctx.est_tc, ctx.est_ts, ctx.t_amb, cmd) >= self.known["M2"] - ad["margin_k"]:
                continue
            ahead = thermal.peak_core(self.th, tc_end, ts_end, ctx.t_amb, np.full(int(ad["lookahead_s"]), lim))
            peak = max(float(tc.max()), ahead)
            if peak > best_peak:
                best, best_peak = cand, peak
        return best
