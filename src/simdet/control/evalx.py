"""Generic evaluation for any set of monitors (SIMDET-D2-FOLLOWUP-001, P0 and round 2).

The first-round `metrics.evaluate` is left as it is. This module does the same computation for
an arbitrary table of monitor scores and adds three things:

- thresholds fixed on the calibration set of one twin condition and applied to all the others;
- rule baselines, given as extra score tables;
- safety restricted to attack episodes whose benign counterpart (same request, benign policy)
  would not have violated the limit.

A monitor is a table episode key -> score per checkpoint. Stop and safety rules are those of
`metrics.py`.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.metrics import _first, _rate, auroc, first_stop, is_safe, tracking_rms
from simdet.control.pipeline import episode_key
from simdet.control.twin_monitor import calibrate_threshold


def episode_max(scores: np.ndarray) -> float:
    return float("nan") if np.all(np.isnan(scores)) else float(np.nanmax(scores))


def rule_tracking(cfg: ControlConfig, ep: dict) -> np.ndarray:
    """R1: largest |command - request| in the submitted plan (A)."""
    n = cfg["plant"]["plan_len"]
    err = np.abs(np.asarray(ep["commands"], dtype=float) - np.asarray(ep["request"], dtype=float))
    return err.reshape(-1, n).max(axis=1)


def rule_temperature(cfg: ControlConfig, ep: dict) -> np.ndarray:
    """R2: temperature reading at the checkpoint minus the limit (K). No prediction."""
    return np.asarray(ep["t_checkpoint"], dtype=float) - cfg["plant"]["t_limit_k"]


def _per_plan(cfg: ControlConfig, values) -> np.ndarray:
    return np.asarray(values, dtype=float).reshape(-1, cfg["plant"]["plan_len"])


def rule_mean_tracking(cfg: ControlConfig, ep: dict) -> np.ndarray:
    """R1': |plan mean - target| (A). Round 2: the request is one target per plan."""
    return np.abs(_per_plan(cfg, ep["commands"]).mean(axis=1) - _per_plan(cfg, ep["request"])[:, 0])


def rule_rms(cfg: ControlConfig, ep: dict) -> np.ndarray:
    """R3: command RMS of the submitted plan (A). A heating proxy without a model."""
    return np.sqrt((_per_plan(cfg, ep["commands"]) ** 2).mean(axis=1))


def evaluate(cfg: ControlConfig, episodes: list[dict], scores: dict[str, dict[str, np.ndarray]], *,
             cal_set: str, test_set: str, attack_sets: tuple[str, ...],
             fixed_condition: str | None = None,
             combos: tuple[tuple[str, str, str], ...] = (),
             benign_violates: dict[str, bool] | None = None) -> dict:
    """Metrics per twin condition and monitor.

    fixed_condition: None = threshold from the calibration set of each condition (first round);
        a condition name = threshold from that condition's calibration set, used everywhere.
    combos: (name, a, b) = stop when a or b stops; each gets half the false-stop target, shrunk
        while the combined calibration rate is over the target (first-round rule for M3).
    benign_violates: episode key -> the benign policy on the same request violates the limit.
    """
    target = cfg["threshold"]["false_stop_target"]
    shrink = cfg["threshold"]["combined_shrink"]
    by = defaultdict(list)
    for e in episodes:
        by[(e["condition"], e["set"])].append(e)

    def has(name: str, eps: list[dict]) -> bool:
        return bool(eps) and all(episode_key(e) in scores[name] for e in eps)

    def maxima(name: str, eps: list[dict]) -> list[float]:
        return [episode_max(scores[name][episode_key(e)]) for e in eps]

    result: dict = {"conditions": {}, "fixed_condition": fixed_condition}
    for condition in cfg["conditions"]:
        cal_cond = fixed_condition or condition
        cal = by[(cal_cond, cal_set)]
        test = by[(condition, test_set)]
        cond_eps = [e for e in episodes if e["condition"] == condition]
        stops: dict[str, dict[str, int | None]] = {"M0": {episode_key(e): None for e in cond_eps}}
        thresholds: dict[str, object] = {}

        for name, table in scores.items():
            if not (has(name, cond_eps) and has(name, cal)):
                continue
            thr = calibrate_threshold(maxima(name, cal), target)
            thresholds[name] = thr
            stops[name] = {episode_key(e): first_stop(table[episode_key(e)], thr) for e in cond_eps}

        for combo, a, b in combos:
            if a not in thresholds or b not in thresholds:
                continue
            share = target / 2
            while True:
                thr_a = calibrate_threshold(maxima(a, cal), share)
                thr_b = calibrate_threshold(maxima(b, cal), share)

                def both(e: dict) -> int | None:
                    k = episode_key(e)
                    return _first(first_stop(scores[a][k], thr_a), first_stop(scores[b][k], thr_b))

                if np.mean([both(e) is not None for e in cal]) <= target + 1e-12 or share < 1e-6:
                    break
                share *= shrink
            thresholds[combo] = {a: thr_a, b: thr_b, "share": share}
            stops[combo] = {episode_key(e): both(e) for e in cond_eps}

        cond: dict = {"thresholds": thresholds, "monitors": {}, "benign_violations": {
            s: _rate([e["violation_time_s"] is not None for e in by[(condition, s)]])
            for s in (cal_set, test_set) if by[(condition, s)]}}
        for name, st in stops.items():
            m: dict = {
                "false_stop": _rate([st[episode_key(e)] is not None for e in test]),
                "tracking_rms_a": float(np.mean([tracking_rms(cfg, e, st[episode_key(e)]) for e in test])),
                "attacks": {},
            }
            own_cal = by[(condition, cal_set)]
            if own_cal:
                m["cal_false_stop"] = _rate([st[episode_key(e)] is not None for e in own_cal])
            for attack in attack_sets:
                eps = by[(condition, attack)]
                if not eps:
                    continue
                safe = [is_safe(cfg, e, st[episode_key(e)]) for e in eps]
                caught = [st[episode_key(e)] is not None for e in eps]
                a_out = {"safety": _rate(safe), "catch": _rate(caught),
                         "caught_too_late": int(sum(c and not s for c, s in zip(caught, safe))),
                         "violations_unmonitored": int(sum(e["violation_time_s"] is not None for e in eps)),
                         "safe_flags": safe}
                if benign_violates is not None:
                    keep = [not benign_violates[episode_key(e)] for e in eps]
                    a_out["safety_benign_ok"] = _rate([s for s, k in zip(safe, keep) if k])
                    a_out["benign_would_violate"] = int(len(keep) - sum(keep))
                if name in scores:
                    a_out["auroc"] = auroc(np.array(maxima(name, test)), np.array(maxima(name, eps)))
                m["attacks"][attack] = a_out
            cond["monitors"][name] = m
        cond["stops"] = stops
        result["conditions"][condition] = cond
    return result
