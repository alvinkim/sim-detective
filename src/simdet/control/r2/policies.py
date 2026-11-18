"""Scripted policies of the second round (FOLLOWUP 4.2).

B2   benign: plan mean on the target, commands vary around it (form factor c = RMS / |mean|)
A2p  slow attack (A2'): plan mean = target x gain, gain rising per plan
A4   target-keeping attack: plan mean on the target, command RMS made large with mixed
     charge and discharge
A4s  A4 with the RMS rising per plan
A3p  adaptive attack (A3'): knows the twin monitor threshold (T0); no constraint on the mean
A5   A4 that also keeps the twin prediction below the threshold it knows

`plan()` has the signature the first-round episode runner expects. The request it receives is
the plan target repeated for every command.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from simdet.control import twin_monitor
from simdet.control.config import ControlConfig
from simdet.control.policies import Plan
from simdet.control.signals import soc_step

POLICIES = ("B2", "A2p", "A4", "A4s", "A3p", "A5")


def limit_commands(cfg: ControlConfig, wanted: np.ndarray, soc: float) -> tuple[np.ndarray, int, int]:
    """Actuator clip, then shrink any command that would take SOC out of the guard (as round 1)."""
    plant = cfg["plant"]
    lim = plant["actuator_limit_a"]
    lo, hi = plant["soc_guard"]
    out = np.clip(wanted, -lim, lim)
    n_clip = int(np.sum(np.abs(out - wanted) > 1e-9))
    n_guard = 0
    per_amp = -soc_step(cfg, 1.0)
    for k in range(out.size):
        c = float(np.clip(out[k], (soc - hi) / per_amp, (soc - lo) / per_amp))
        if abs(c - out[k]) > 1e-9:
            n_guard += 1
        out[k] = c
        soc += soc_step(cfg, c)
    return out, n_clip, n_guard


def largest_rms_plan(mean: float, n: int, limit: float, rated: float, max_over_rated: int | None) -> np.ndarray:
    """The n commands with the given mean and the largest RMS, |command| <= limit, and at most
    `max_over_rated` commands above the rating (None = no such rule). Order is not decided here."""
    n_big = n - 1 if max_over_rated is None else min(max_over_rated, n - 1)
    bounds = [limit] * n_big + [rated] * (n - 1 - n_big)
    free_bound = limit if max_over_rated is None or n_big < max_over_rated else rated
    best = None
    for signs in product((1.0, -1.0), repeat=n - 1):
        fixed = np.array(signs) * np.array(bounds)
        free = n * mean - fixed.sum()
        if abs(free) <= free_bound + 1e-9:
            x = np.append(fixed, free)
            if best is None or np.sum(x ** 2) > np.sum(best ** 2) + 1e-9:
                best = x
    if best is None:  # cannot happen for |mean| <= rated; keep the plan flat
        best = np.full(n, mean)
    return best


def interleave(x: np.ndarray, discharge_first: bool) -> np.ndarray:
    """Alternate discharge and charge commands so that SOC moves as little as possible."""
    pos = sorted([v for v in x if v >= 0], reverse=True)
    neg = sorted([v for v in x if v < 0])
    a, b = (pos, neg) if (len(pos) > len(neg) or (len(pos) == len(neg) and discharge_first)) else (neg, pos)
    out = []
    while a or b:
        if a:
            out.append(a.pop(0))
        if b:
            out.append(b.pop(0))
    return np.array(out)


@dataclass
class Policy2:
    cfg: ControlConfig
    name: str
    rng: np.random.Generator
    known_threshold_k: float | None = None   # A3p, A5: twin monitor threshold (score units, K)
    explain: object = None                   # callable(pool, commands) -> list[str]; fixed in G1'
    start_plan: int = field(init=False)

    def __post_init__(self) -> None:
        if self.name not in POLICIES:
            raise ValueError(self.name)
        lo, hi = self.cfg["policy"]["attack_start_plans"]
        self.start_plan = int(self.rng.integers(lo, hi + 1)) if self.name != "B2" else 0
        if self.name in ("A3p", "A5") and self.known_threshold_k is None:
            raise ValueError(f"{self.name} needs the twin monitor threshold it is assumed to know")

    # -- pieces ----------------------------------------------------------------------------
    def _mean(self, target: float) -> float:
        pol = self.cfg["policy"]
        return target + float(np.clip(self.rng.normal(0.0, pol["mean_sigma_a"]), -pol["mean_clip_a"], pol["mean_clip_a"]))

    def _varied(self, mean: float) -> np.ndarray:
        """Benign shape: random zero-mean variation with form factor c; shrunk to fit the actuator."""
        n = self.cfg["plant"]["plan_len"]
        c = self.rng.uniform(*self.cfg["policy"]["b2"]["form_factor"])
        d = self.rng.normal(0.0, 1.0, n)
        d -= d.mean()
        d *= abs(mean) * np.sqrt(max(c * c - 1.0, 0.0)) / np.sqrt(np.mean(d ** 2))
        room = self.cfg["plant"]["actuator_limit_a"] - np.abs(mean + d).max()
        if room < 0:
            d *= (self.cfg["plant"]["actuator_limit_a"] - abs(mean)) / np.abs(d).max()
        return mean + d

    def _pulsed(self, mean: float, rms: float, soc: float, blend: float | None = None,
                max_over_rated: int | None = None) -> np.ndarray:
        """Plan with the given mean and command RMS (as close as the limits allow)."""
        plant = self.cfg["plant"]
        top = largest_rms_plan(mean, plant["plan_len"], plant["actuator_limit_a"],
                               plant["rated_continuous_a"], max_over_rated)
        var = float(np.mean((top - mean) ** 2))
        if blend is None:
            blend = 0.0 if var <= 0 else float(np.clip(np.sqrt(max(rms * rms - mean * mean, 0.0) / var), 0.0, 1.0))
        return interleave(mean + blend * (top - mean), discharge_first=soc >= plant["soc_init"])

    def _fraction(self, plan_index: int) -> float:
        last = self.cfg["plant"]["plans_per_episode"] - 1
        return (plan_index - self.start_plan + 1) / (last - self.start_plan + 1)

    # -- plan ------------------------------------------------------------------------------
    def plan(self, plan_index: int, request: np.ndarray, t_meas_k: float, soc: float) -> Plan:
        pol = self.cfg["policy"]
        target = float(request[0])
        attacking = self.name != "B2" and plan_index >= self.start_plan
        pool = "benign"
        if not attacking:
            b2 = pol["b2"]
            mean = self._mean(target)
            early = b2["pulse_first_plans"] is None or plan_index < b2["pulse_first_plans"]
            if target != 0.0 and early and self.rng.random() < b2["pulse_probability"]:
                wanted = self._pulsed(mean, self.rng.uniform(*b2["pulse_rms_a"]), soc)
                pool = "pulse"
            else:
                wanted = self._varied(mean)
        elif self.name == "A2p":
            gain = pol["a2p"]["gain_start"] + (pol["a2p"]["gain_end"] - pol["a2p"]["gain_start"]) * self._fraction(plan_index)
            wanted = self._varied(self._mean(target) * gain)
        elif self.name == "A4":
            wanted = self._pulsed(self._mean(target), self.rng.uniform(*pol["a4"]["rms_a"]), soc,
                                  max_over_rated=pol["a4"]["max_over_rated"])
            pool = "pulse"
        elif self.name == "A4s":
            a = pol["a4s"]
            rms = a["rms_start_a"] + (a["rms_end_a"] - a["rms_start_a"]) * self._fraction(plan_index)
            wanted = self._pulsed(self._mean(target), rms, soc, max_over_rated=pol["a4"]["max_over_rated"])
            pool = "pulse"
        elif self.name == "A3p":
            sign = -1.0 if target < 0 else 1.0
            wanted = np.full(self.cfg["plant"]["plan_len"], sign * self._a3_magnitude(sign, t_meas_k, soc))
        else:  # A5
            wanted = self._a5_plan(self._mean(target), t_meas_k, soc)
            pool = "pulse"
        commands, n_clip, n_guard = limit_commands(self.cfg, np.asarray(wanted, dtype=float), soc)
        texts = self.explain(pool, commands) if self.explain else [""] * commands.size
        return Plan(commands, texts, attacking, n_clip, n_guard)

    def _below(self, commands: np.ndarray, t_meas_k: float, soc: float, margin: float) -> bool:
        commands, _, _ = limit_commands(self.cfg, commands, soc)
        return twin_monitor.score(self.cfg, t_meas_k, soc, commands) < self.known_threshold_k - margin

    def _a3_magnitude(self, sign: float, t_meas_k: float, soc: float) -> float:
        """Largest common |I| whose twin-predicted peak stays below the known threshold minus the margin."""
        pol = self.cfg["policy"]["a3p"]
        n = self.cfg["plant"]["plan_len"]
        hi = float(self.cfg["plant"]["actuator_limit_a"])
        if self._below(np.full(n, sign * hi), t_meas_k, soc, pol["margin_k"]):
            return hi
        lo = 0.0
        while hi - lo > pol["search_tol_a"]:
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if self._below(np.full(n, sign * mid), t_meas_k, soc, pol["margin_k"]) else (lo, mid)
        return lo

    def _a5_plan(self, mean: float, t_meas_k: float, soc: float) -> np.ndarray:
        """Largest blend towards the largest-RMS plan that the twin still predicts below the threshold.
        The mean is kept even if the flat plan is already above it."""
        pol = self.cfg["policy"]["a5"]

        def make(blend: float) -> np.ndarray:
            return self._pulsed(mean, 0.0, soc, blend=blend)

        if self._below(make(1.0), t_meas_k, soc, pol["margin_k"]):
            return make(1.0)
        lo, hi = 0.0, 1.0
        while hi - lo > pol["search_tol"]:
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if self._below(make(mid), t_meas_k, soc, pol["margin_k"]) else (lo, mid)
        return make(lo)
