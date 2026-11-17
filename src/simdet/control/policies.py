"""Scripted operating policies (spec 5.2): benign B and the attacks A1 (blatant), A2 (slow), A3 (adaptive).

A policy turns the request for one plan into `plan_len` commands and their explanation sentences.
Every policy passes its commands through the same actuator clip and SOC guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from simdet.control import twin_monitor
from simdet.control.config import ControlConfig
from simdet.control.signals import soc_step

POLICIES = ("B", "A1", "A2", "A3")


@dataclass
class Plan:
    commands: np.ndarray
    explanations: list[str]
    attacking: bool
    n_actuator_clipped: int = 0
    n_guard_limited: int = 0


@dataclass
class Policy:
    cfg: ControlConfig
    name: str
    templates: dict[str, list[str]]
    rng: np.random.Generator
    known_threshold_k: float | None = None  # A3: twin monitor threshold (score units, K)
    start_plan: int = field(init=False)

    def __post_init__(self) -> None:
        lo, hi = self.cfg["policy"]["attack_start_plans"]
        self.start_plan = int(self.rng.integers(lo, hi + 1)) if self.name != "B" else 0
        if self.name == "A3" and self.known_threshold_k is None:
            raise ValueError("A3 needs the twin monitor threshold it is assumed to know")

    # -- shared limits -------------------------------------------------------------------
    def _limit(self, wanted: np.ndarray, soc: float) -> tuple[np.ndarray, int, int]:
        """Actuator clip, then shrink any command that would take SOC out of the guard."""
        plant = self.cfg["plant"]
        lim = plant["actuator_limit_a"]
        lo, hi = plant["soc_guard"]
        out = np.clip(wanted, -lim, lim)
        n_clip = int(np.sum(out != wanted))
        n_guard = 0
        per_amp = -soc_step(self.cfg, 1.0)  # SOC lost per ampere of discharge in one command
        for k in range(out.size):
            c_max = (soc - lo) / per_amp   # largest discharge current
            c_min = (soc - hi) / per_amp   # most negative (charge) current
            c = float(np.clip(out[k], c_min, c_max))
            if abs(c - out[k]) > 1e-9:
                n_guard += 1
            out[k] = c
            soc += soc_step(self.cfg, c)
        return out, n_clip, n_guard

    def _explain(self, pool: str, commands: np.ndarray) -> list[str]:
        texts = self.templates[pool]
        out = []
        for c in commands:
            mode = "discharge" if c > 0 else "charge" if c < 0 else "idle"
            text = texts[int(self.rng.integers(len(texts)))].format(mode=mode)
            out.append(text[0].upper() + text[1:])
        return out

    def _track(self, request: np.ndarray) -> np.ndarray:
        return request + self.rng.normal(0.0, self.cfg["policy"]["tracking_sigma_a"], request.size)

    # -- plan ----------------------------------------------------------------------------
    def plan(self, plan_index: int, request: np.ndarray, t_meas_k: float, soc: float) -> Plan:
        pol = self.cfg["policy"]
        attacking = self.name != "B" and plan_index >= self.start_plan
        sign = np.where(request < 0, -1.0, 1.0)
        pool = "benign"
        if not attacking:
            wanted = self._track(request)
        elif self.name == "A1":
            lo, hi = pol["a1"]["mag_range_a"]
            wanted = sign * self.rng.uniform(lo, hi, request.size)
            pool = "blatant"
        elif self.name == "A2":
            last = self.cfg["plant"]["plans_per_episode"] - 1
            frac = (plan_index - self.start_plan + 1) / (last - self.start_plan + 1)
            gain = pol["a2"]["gain_start"] + (pol["a2"]["gain_end"] - pol["a2"]["gain_start"]) * frac
            wanted = self._track(request) * gain
        else:
            wanted = sign * self._a3_magnitude(sign, t_meas_k, soc)
        commands, n_clip, n_guard = self._limit(np.asarray(wanted, dtype=float), soc)
        return Plan(commands, self._explain(pool, commands), attacking, n_clip, n_guard)

    def _a3_magnitude(self, sign: np.ndarray, t_meas_k: float, soc: float) -> float:
        """Largest common |I| whose twin-predicted peak stays below the known threshold minus the margin."""
        pol = self.cfg["policy"]["a3"]
        target = self.known_threshold_k - pol["margin_k"]

        def ok(mag: float) -> bool:
            commands, _, _ = self._limit(sign * mag, soc)
            return twin_monitor.score(self.cfg, t_meas_k, soc, commands) < target

        hi = float(self.cfg["plant"]["actuator_limit_a"])
        if ok(hi):
            return hi
        lo = 0.0  # zero current is used even if it is not below the target (cell already too warm)
        while hi - lo > pol["search_tol_a"]:
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        return lo
