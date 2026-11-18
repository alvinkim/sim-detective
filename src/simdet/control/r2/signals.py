"""Plan-level request (FOLLOWUP 4.1): one target per plan, the mean current of the next 5 minutes.

Magnitude and sign are made as in the first round (bounded random walk; the sign leans back
towards the starting SOC), per plan instead of per command. Some plans are rests (target 0 A).
The SOC that the targets alone would produce stays inside `soc_band`.
"""

from __future__ import annotations

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.signals import soc_step


def plan_soc_step(cfg: ControlConfig, mean_current_a: float) -> float:
    return soc_step(cfg, mean_current_a) * cfg["plant"]["plan_len"]


def target_signal(cfg: ControlConfig, kind: str, rng: np.random.Generator) -> np.ndarray:
    """Targets m_j (A), one per plan. Discharge is positive."""
    plant, req = cfg["plant"], cfg["request"]
    lo, hi = req["kinds"][kind]["mag_range_a"]
    step = req["kinds"][kind]["mag_step_a"]
    p_lo, p_hi = req["balance_p_range"]
    s_lo, s_hi = req["soc_band"]

    out = np.zeros(plant["plans_per_episode"])
    mag = rng.uniform(lo, hi)
    soc = plant["soc_init"]
    for j in range(out.size):
        rest = rng.random() < req["rest_probability"]
        lean = (soc - plant["soc_init"]) / req["balance_band_soc"]  # above start -> discharge
        sign = 1.0 if rng.random() < float(np.clip(0.5 + 0.5 * lean, p_lo, p_hi)) else -1.0
        if not rest:
            for m in (sign * mag, -sign * mag):  # flip the sign if the target would leave the band
                if s_lo <= soc + plan_soc_step(cfg, m) <= s_hi:
                    out[j] = m
                    break
        soc += plan_soc_step(cfg, out[j])
        mag = float(np.clip(mag + rng.normal(0.0, step), lo, hi))
    return out
