"""Requested current signal (spec 5.1): one value per command, within +/- the rated current.

The magnitude is a bounded random walk. The sign is held for a random number of commands and,
when it is redrawn, leans towards the direction that brings the coulomb-counted SOC of the
request itself back to its start. Charge and discharge therefore roughly balance.
"""

from __future__ import annotations

import numpy as np

from simdet.control.config import ControlConfig


def soc_step(cfg: ControlConfig, current_a: float) -> float:
    """SOC change of one command (discharge positive lowers SOC)."""
    return -current_a * cfg["plant"]["command_period_s"] / (3600.0 * cfg.cell.q_ah)


def request_signal(cfg: ControlConfig, kind: str, rng: np.random.Generator) -> np.ndarray:
    plant, req = cfg["plant"], cfg["request"]
    n = plant["plan_len"] * plant["plans_per_episode"]
    lo, hi = req["kinds"][kind]["mag_range_a"]
    step = req["kinds"][kind]["mag_step_a"]
    d_lo, d_hi = req["dwell_commands"]
    p_lo, p_hi = req["balance_p_range"]

    out = np.empty(n)
    mag = rng.uniform(lo, hi)
    soc = plant["soc_init"]
    sign, left = 1.0, 0
    for k in range(n):
        if left == 0:
            lean = (soc - plant["soc_init"]) / req["balance_band_soc"]  # above start -> discharge
            p_discharge = float(np.clip(0.5 + 0.5 * lean, p_lo, p_hi))
            sign = 1.0 if rng.random() < p_discharge else -1.0
            left = int(rng.integers(d_lo, d_hi + 1))
        out[k] = sign * mag
        soc += soc_step(cfg, out[k])
        left -= 1
        mag = float(np.clip(mag + rng.normal(0.0, step), lo, hi))
    return out
