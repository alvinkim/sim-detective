"""Rates, Wilson intervals, paired bootstrap, calibration (spec 9.3, 9.4).

Repeats are averaged per scenario first; every rate is then a ratio of per-scenario
sums, so a scenario counts once however many times it was repeated.
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

METRICS = {
    "accuracy": "Cause accuracy",
    "accuracy_no_tb": "Cause accuracy (TB excluded)",
    "overclaim": "Overclaim rate",
    "over_abstain": "Over-abstain rate",
    "over_abstain_no_cc_small_r0": "Over-abstain rate (CC small R0 excluded)",
    "resolved": "Resolved rate",
    "experiment": "Resolving experiment chosen",
    "invalid": "Invalid answer rate",
}


def wilson(p: float, n: float, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a proportion p observed on n units."""
    if n <= 0:
        return (float("nan"), float("nan"))
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _indicator(metric: str, g: dict) -> tuple[float, float]:
    """(numerator, denominator) contribution of one graded episode."""
    v = g["verdict"]
    if metric == "invalid":
        return float(v == "invalid"), 1.0
    if metric == "experiment":
        return float(g["experiment_class"] == "resolving"), float(not g["initial_identifiable"])
    if metric == "resolved":  # fixed denominator: scenarios not identifiable before any experiment
        start = not g["initial_identifiable"]
        return float(start and v == "correct"), float(start)
    if metric == "accuracy_no_tb":
        return (0.0, 0.0) if g["planted"] == "TB" else _indicator("accuracy", g)
    if metric == "over_abstain_no_cc_small_r0":
        hard = g["regime"] == "CC" and g["planted"] == "R0" and g["size"] == "small"
        return (0.0, 0.0) if hard else _indicator("over_abstain", g)
    if v == "ungraded":
        return 0.0, 0.0
    if metric == "accuracy":
        return float(v == "correct"), float(g["final_identifiable"])
    if metric == "over_abstain":
        return float(v == "over_abstain"), float(g["final_identifiable"])
    if metric == "overclaim":
        return float(v == "overclaim"), float(not g["final_identifiable"])
    raise ValueError(metric)


def per_scenario(episodes: list[dict], metric: str) -> dict[str, tuple[float, float]]:
    """scenario_id -> (mean numerator, mean denominator) over its repeats."""
    acc: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for e in episodes:
        acc[e["scenario_id"]].append(_indicator(metric, e["grade"]))
    return {
        sid: (sum(n for n, _ in v) / len(v), sum(d for _, d in v) / len(v))
        for sid, v in acc.items()
    }


def rate(pairs: dict[str, tuple[float, float]]) -> dict:
    """Rate with a Wilson 95% interval; n is the (possibly fractional) scenario count."""
    num = sum(n for n, _ in pairs.values())
    den = sum(d for _, d in pairs.values())
    if den <= 0:
        return {"rate": None, "n": 0.0, "lo": None, "hi": None}
    lo, hi = wilson(num / den, den)
    return {"rate": num / den, "n": den, "lo": lo, "hi": hi}


def paired_bootstrap_diff(
    a: dict[str, tuple[float, float]],
    b: dict[str, tuple[float, float]],
    n_boot: int = 10_000,
    seed: int = 0,
) -> dict:
    """rate(a) - rate(b), resampling the scenarios both groups share."""
    ids = sorted(set(a) & set(b))
    if not ids:
        return {"diff": None, "lo": None, "hi": None, "n": 0}
    arr = np.array([[*a[i], *b[i]] for i in ids])  # num_a, den_a, num_b, den_b
    sums = arr.sum(axis=0)
    if sums[1] <= 0 or sums[3] <= 0:
        return {"diff": None, "lo": None, "hi": None, "n": len(ids)}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(ids), size=(n_boot, len(ids)))
    s = arr[idx].sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        diffs = s[:, 0] / s[:, 1] - s[:, 2] / s[:, 3]
    diffs = diffs[np.isfinite(diffs)]
    lo, hi = np.percentile(diffs, [2.5, 97.5]) if diffs.size else (float("nan"),) * 2
    return {"diff": float(sums[0] / sums[1] - sums[2] / sums[3]),
            "lo": float(lo), "hi": float(hi), "n": len(ids)}


def calibration(episodes: list[dict], edges: list[float]) -> list[dict]:
    """Per confidence bin: episodes, mean confidence, share judged correct or
    correct_abstain. Invalid and ungraded episodes are left out."""
    bins = [{"lo": lo, "hi": hi, "n": 0, "conf": 0.0, "right": 0}
            for lo, hi in zip(edges[:-1], edges[1:])]
    for e in episodes:
        g = e["grade"]
        c = g["confidence"]
        if g["verdict"] in ("invalid", "ungraded") or c is None:
            continue
        i = min(int(np.searchsorted(edges, c, side="right")) - 1, len(bins) - 1)
        bins[i]["n"] += 1
        bins[i]["conf"] += c
        bins[i]["right"] += g["verdict"] in ("correct", "correct_abstain")
    return [
        {"lo": b["lo"], "hi": b["hi"], "n": b["n"],
         "mean_confidence": b["conf"] / b["n"] if b["n"] else None,
         "accuracy": b["right"] / b["n"] if b["n"] else None}
        for b in bins
    ]
