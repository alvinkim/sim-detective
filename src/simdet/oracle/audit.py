"""Audit of aliasing with a likelihood-type statistic (SIMDET-DECISION-002, A1).

The oracle decides with RMS thresholds, which are blunt for a small persistent
difference over many samples. This module asks the sharper question for a pair the
oracle calls indistinguishable: how much better does the planted cause fit than the
other candidate? It never changes an oracle verdict.
"""

from __future__ import annotations

import numpy as np

from simdet.oracle.fit import OracleData, estimate_sigma, fit_hypothesis
from simdet.scenario.world import World
from simdet.sim.faults import magnitude, make_fault

PAIR = ("SOC0", "ST")
SEED_BASE = 1_000_000  # audit seeds; scenario seeds come from a different stream


def delta_chi2(cfg, world: World, planted: str, other: str) -> float:
    """Fit objective (both channels) of `other` minus that of `planted`, on the logged data."""
    data = OracleData.from_segment(world.current, float(cfg["sim"]["soc_init"]))
    sigma = estimate_sigma(data)
    n = 2 * (data.current.size - data.visible_from)
    chi2 = {h: fit_hypothesis(cfg.cell, data, h, sigma).normalized_rms ** 2 * n for h in (planted, other)}
    return chi2[other] - chi2[planted]


def alias_audit(cfg, designs: list[dict], regime: str = "CC") -> list[dict]:
    """For each design {'cause', 'label', 'target_v'}: delta chi2 over fresh seeds.

    A design passes if |mean| <= mean_abs_max and the share above exceed_level is at
    most exceed_share_max. With exact aliasing the statistic is close to 0 for every seed.
    """
    a = cfg["scenario"]["alias_audit"]
    rows = []
    for d in designs:
        other = PAIR[1] if d["cause"] == PAIR[0] else PAIR[0]
        fault = make_fault(d["cause"], magnitude(d["cause"], None, cfg, d["target_v"]))
        values = np.array([
            delta_chi2(cfg, World(cfg, fault, regime, SEED_BASE + s), d["cause"], other)
            for s in range(int(a["seeds"]))
        ])
        share = float(np.mean(values > a["exceed_level"]))
        rows.append({
            "cause": d["cause"], "label": d["label"], "target_mv": 1e3 * d["target_v"],
            "seeds": int(a["seeds"]), "mean": float(values.mean()), "max": float(values.max()),
            "share_above": share,
            "passed": bool(abs(values.mean()) <= a["mean_abs_max"] and share <= a["exceed_share_max"]),
        })
    return rows
