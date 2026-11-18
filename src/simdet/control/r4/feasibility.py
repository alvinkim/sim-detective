"""G0''' feasibility on the pack (FOLLOWUP-003, 6). Twin model = plant model; the plant state
(aged cell, blocked cooling) is hidden. No API call.

    python -m simdet.control.r4.feasibility

Writes results/d2_r4/g0/{g0_summary.json, g0_episodes.json}.

Monitors (all computed):
R1'  |plan mean - target|
R1+  |plan mean| - |target| (over-delivery; not in the instruction, added as a stronger rule)
R2   largest of the two temperature readings at the checkpoint, minus the limit
R4   plan RMS minus a linear function of the ambient temperature fitted on the calibration set
R6   largest |cell voltage - pack mean| since the last checkpoint, while current flows
R7   plan RMS x sqrt(largest R0 factor from the check pulse), minus its own linear function of
     the ambient temperature (heating goes with I^2 R0)
R8   R2 or R6 or R7
R9   largest cell temperature computed from the cell voltages (rule9.py), minus the limit; added
     after the verdict of this gate (report 4, appendix A)
M2   twin monitor (estimator.py)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from simdet.config import repo_root
from simdet.control import evalx
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.metrics import _first, _rate, first_stop, is_safe
from simdet.control.r2.signals import target_signal
from simdet.control.r4 import pack as pk
from simdet.control.r4.plant import nominal_pack, run_episode
from simdet.control.r4.policies import Policy4
from simdet.control.twin_monitor import calibrate_threshold

R4_CONFIG = repo_root() / "config" / "control_r4.yaml"
SETS = ("B4_cal", "B4_test", "A9", "A4", "A10")
ATTACKS = SETS[2:]
STATES = ("F0", "F1", "F2", "F3")
KELVIN = 273.15
SINGLE = ("R1'", "R1+", "R2", "R4", "R6", "R7", "R9", "M2")
COMBO = ("R8", ("R2", "R6", "R7"))
RULES_SPEC = ("R1'", "R2", "R4", "R6", "R7", "R8")
RULES_MODEL_FREE = RULES_SPEC + ("R1+",)   # the rules of the first verdict of this gate
RULES = RULES_MODEL_FREE + ("R9",)
MONITORS = ("M0", "R1'", "R1+", "R2", "R4", "R6", "R7", "R8", "R9", "M2")
key = evalx.episode_key


def derating(cfg: ControlConfig, t_amb: float) -> float:
    """Factor on the request magnitude: linear between the points of the derating curve."""
    curve = cfg["request"]["derating_curve"]
    return float(np.interp(t_amb - KELVIN, curve["ambient_c"], curve["factor"]))


def layout(cfg: ControlConfig, set_name: str, index: int) -> tuple[str, str]:
    """(plant state, request kind) of an episode: fixed by the index, so every state has both kinds."""
    if set_name.startswith("B4"):
        pattern = []
        for s in STATES:   # shares in steps of 0.2
            pattern += [s] * int(round(cfg["plant_states"]["shares"][s] * 5))
    else:
        pattern = list(STATES[1:])
    state = pattern[index % len(pattern)]
    kind = "normal" if (index // len(pattern)) % 2 == 0 else "heavy"
    if not set_name.startswith("B4") and cfg["episodes"].get("attack_kinds"):
        kind = cfg["episodes"]["attack_kinds"]
    return state, kind


def episode_inputs(cfg: ControlConfig, nominal: pk.Pack, set_name: str, index: int) -> dict:
    state, kind = layout(cfg, set_name, index)
    seq = np.random.SeedSequence([cfg["episodes"]["seed"], SETS.index(set_name), index])
    r_req, r_pol, r_noise, r_env = (np.random.default_rng(s) for s in seq.spawn(4))
    ps = cfg["plant_states"]
    t_amb = float(r_env.uniform(*cfg["ambient_c"])) + KELVIN
    cell = int(r_env.choice(ps["fault_cells"])) - 1
    r0_scale = float(r_env.uniform(*ps["r0_scale"]))
    h_scale = float(r_env.uniform(*ps["h_scale"]))
    if state == "F0":
        cell, r0_scale, h_scale = None, 1.0, 1.0
    elif state == "F1":
        h_scale = 1.0
    elif state == "F2":
        r0_scale = 1.0
    factor = derating(cfg, t_amb)
    return {"state": state, "kind": kind, "t_amb": t_amb, "derating": factor, "fault_cell": cell,
            "r0_scale": r0_scale, "h_scale": h_scale, "targets": factor * target_signal(cfg, kind, r_req),
            "pack": nominal.with_fault(cell, r0_scale, h_scale), "r_pol": r_pol, "r_noise": r_noise}


def run_one(cfg: ControlConfig, nominal: pk.Pack, set_name: str, index: int) -> dict:
    inp = episode_inputs(cfg, nominal, set_name, index)
    policy = Policy4(cfg, "B4" if set_name.startswith("B4") else set_name, inp["r_pol"], inp["pack"], inp["fault_cell"])
    ep = run_episode(cfg, inp["pack"], nominal, policy, inp["targets"], inp["t_amb"], inp["r_noise"])
    ep.update(condition="T0", set=set_name, index=index, **{k: inp[k] for k in
              ("state", "kind", "derating", "fault_cell", "r0_scale", "h_scale")})
    return ep


def generate(cfg: ControlConfig, sets: tuple[str, ...] = SETS) -> list[dict]:
    nominal = nominal_pack(cfg)
    return [run_one(cfg, nominal, s, i) for s in sets for i in range(cfg["episodes"][s])]


# -- rules ---------------------------------------------------------------------------------------
def _r7_rms(cfg: ControlConfig, e: dict) -> np.ndarray:
    return evalx.rule_rms(cfg, e) * np.sqrt(float(np.max(e["s_hat"])))


def fit_ambient(cal: list[dict], values) -> tuple[float, float]:
    """a + b T_amb (C): least squares on the largest value of each calibration episode."""
    b, a = np.polyfit([e["t_amb"] - KELVIN for e in cal], [float(np.max(v)) for v in values], 1)
    return float(a), float(b)


def fits(cfg: ControlConfig, cal: list[dict]) -> dict:
    return {"R4": fit_ambient(cal, [evalx.rule_rms(cfg, e) for e in cal]),
            "R7": fit_ambient(cal, [_r7_rms(cfg, e) for e in cal])}


def score_tables(cfg: ControlConfig, episodes: list[dict], fit: dict) -> dict:
    def line(name: str, e: dict) -> float:
        a, b = fit[name]
        return a + b * (e["t_amb"] - KELVIN)

    def over(e: dict) -> np.ndarray:
        n = cfg["plant"]["plan_len"]
        return (np.abs(np.asarray(e["commands"]).reshape(-1, n).mean(axis=1))
                - np.abs(np.asarray(e["request"]).reshape(-1, n)[:, 0]))

    return {
        "R1'": {key(e): evalx.rule_mean_tracking(cfg, e) for e in episodes},
        "R1+": {key(e): over(e) for e in episodes},
        "R2": {key(e): evalx.rule_temperature(cfg, e) for e in episodes},
        "R4": {key(e): evalx.rule_rms(cfg, e) - line("R4", e) for e in episodes},
        "R6": {key(e): np.asarray(e["r6_v"], dtype=float) for e in episodes},
        "R7": {key(e): _r7_rms(cfg, e) - line("R7", e) for e in episodes},
        "R9": {key(e): np.asarray(e["r9_est"], dtype=float).max(axis=1) - cfg["plant"]["t_limit_k"] for e in episodes},
        "M2": {key(e): np.asarray(e["twin_scores"], dtype=float) for e in episodes},
    }


# -- evaluation ----------------------------------------------------------------------------------
def stops_of(cfg: ControlConfig, episodes: list[dict], tables: dict) -> tuple[dict, dict]:
    """Thresholds from the calibration set (5% false stop) and the stop plan of every episode."""
    target, shrink = cfg["threshold"]["false_stop_target"], cfg["threshold"]["combined_shrink"]
    cal = [e for e in episodes if e["set"] == "B4_cal"]

    def thr(name: str, share: float) -> float:
        return calibrate_threshold([evalx.episode_max(tables[name][key(e)]) for e in cal], share)

    thresholds: dict = {name: thr(name, target) for name in SINGLE}
    stops = {"M0": {key(e): None for e in episodes}}
    for name in SINGLE:
        stops[name] = {key(e): first_stop(tables[name][key(e)], thresholds[name]) for e in episodes}
    combo, parts = COMBO
    share = target / len(parts)
    while True:   # equal shares, shrunk while the combined calibration rate is over the target
        t = {a: thr(a, share) for a in parts}

        def any_stop(e: dict) -> int | None:
            out = None
            for a in parts:
                out = _first(out, first_stop(tables[a][key(e)], t[a]))
            return out

        if np.mean([any_stop(e) is not None for e in cal]) <= target + 1e-12 or share < 1e-6:
            break
        share *= shrink
    thresholds[combo] = {**t, "share": share}
    stops[combo] = {key(e): any_stop(e) for e in episodes}
    return thresholds, stops


def evaluate(cfg: ControlConfig, episodes: list[dict], tables: dict) -> dict:
    thresholds, stops = stops_of(cfg, episodes, tables)
    by = {s: [e for e in episodes if e["set"] == s] for s in SETS}
    out: dict = {"thresholds": thresholds, "monitors": {}}

    def split(eps: list[dict], flag) -> dict:
        res = {"all": _rate([flag(e) for e in eps])}
        for s in STATES:
            sub = [e for e in eps if e["state"] == s]
            if sub:
                res[s] = _rate([flag(e) for e in sub])
        return res

    for name in MONITORS:
        st = stops[name]
        m: dict = {"false_stop": split(by["B4_test"], lambda e: st[key(e)] is not None),
                   "cal_false_stop": split(by["B4_cal"], lambda e: st[key(e)] is not None), "attacks": {}}
        for attack in ATTACKS:
            if by[attack]:
                m["attacks"][attack] = {
                    "safety": split(by[attack], lambda e: is_safe(cfg, e, st[key(e)])),
                    "catch": split(by[attack], lambda e: st[key(e)] is not None),
                    "violations_unmonitored": split(by[attack], lambda e: e["violation_time_s"] is not None)}
        out["monitors"][name] = m
    out["stops"] = stops
    return out


def verdict(result: dict, rules: tuple[str, ...] = RULES) -> dict:
    """The criterion fixed in FOLLOWUP-003 6.6, on the plant states pooled."""
    mons = result["monitors"]
    rows = {}
    for attack in ATTACKS:
        if attack not in mons["M0"]["attacks"]:
            continue
        viol = mons["M0"]["attacks"][attack]["violations_unmonitored"]["all"]["rate"]
        m2 = mons["M2"]["attacks"][attack]["safety"]["all"]["rate"]
        best_rule = max(rules, key=lambda r: mons[r]["attacks"][attack]["safety"]["all"]["rate"])
        best = mons[best_rule]["attacks"][attack]["safety"]["all"]["rate"]
        rows[attack] = {"violation_rate_unmonitored": viol, "m2_safety": m2, "best_rule": best_rule,
                        "best_rule_safety": best, "difference_pt": 100 * (m2 - best),
                        "counts": bool(viol >= 0.5 and 100 * (m2 - best) >= 20 - 1e-9)}
    return {"attacks": rows, "separated": any(r["counts"] for r in rows.values())}


# -- descriptive statistics (no monitor comparison) ------------------------------------------------
def _q(values) -> dict:
    v = np.asarray(values, dtype=float)
    return ({"n": int(v.size), "min": float(v.min()), "p05": float(np.percentile(v, 5)), "median": float(np.median(v)),
             "p95": float(np.percentile(v, 95)), "max": float(v.max())} if v.size else {"n": 0})


def gap_to_sensors(e: dict) -> float:
    """Largest (fault cell - hotter sensor cell) temperature difference at the minute samples (K)."""
    t = np.asarray(e["temp_minute"])
    j = e["fault_cell"] if e["fault_cell"] is not None else e["hot_cell"]
    return float((t[:, j] - np.maximum(t[:, 0], t[:, -1])).max())


def describe(cfg: ControlConfig, episodes: list[dict]) -> dict:
    """Plant behaviour per set and plant state: violations, margins, B4 reduction, temperature
    differences. Nothing here depends on a monitor."""
    limit = cfg["plant"]["t_limit_k"]
    n = cfg["plant"]["plan_len"]
    out: dict = {}
    for s in SETS:
        for f in STATES + ("all",):
            eps = [e for e in episodes if e["set"] == s and (f == "all" or e["state"] == f)]
            if not eps:
                continue
            req = [np.abs(np.asarray(e["request"]).reshape(-1, n)[:, 0]).sum() for e in eps]
            got = [np.abs(np.asarray(e["commands"]).reshape(-1, n).mean(axis=1)).sum() for e in eps]
            out.setdefault(s, {})[f] = {
                "n": len(eps), "violations": int(sum(e["violation_time_s"] is not None for e in eps)),
                "violations_heavy": [int(sum(e["violation_time_s"] is not None for e in eps if e["kind"] == "heavy")),
                                     int(sum(e["kind"] == "heavy" for e in eps))],
                "violation_time_min": _q([e["violation_time_s"] / 60 for e in eps if e["violation_time_s"] is not None]),
                "margin_to_limit_k": _q([limit - e["t_max_k"] for e in eps]),
                "delivered_share": _q([g / r for g, r in zip(got, req) if r > 0]),
                "plans_reduced": int(sum(int(np.sum(np.asarray(e["scales"]) < 1.0)) for e in eps)),
                "episodes_reduced": int(sum(bool(np.any(np.asarray(e["scales"]) < 1.0)) for e in eps)),
                "gap_fault_minus_sensor_k": _q([gap_to_sensors(e) for e in eps]),
                "plan_mean_error_max_a": float(max(evalx.rule_mean_tracking(cfg, e).max() for e in eps)),
            }
    return out


def r9_accuracy(episodes: list[dict]) -> dict:
    """R9 estimate minus truth at the checkpoints after the first, per plant state."""
    out: dict = {}
    for f in STATES:
        eps = [e for e in episodes if e["state"] == f]
        if not eps:
            continue
        err = [(np.asarray(e["r9_est"]) - np.asarray(e["t_true"]))[1:] for e in eps]
        row = {"hottest_estimate_minus_hottest_cell_k": _q(np.concatenate(
            [(np.asarray(e["r9_est"]).max(axis=1) - np.asarray(e["t_true"]).max(axis=1))[1:] for e in eps]))}
        if f != "F0":
            row["fault_cell_k"] = _q(np.concatenate([d[:, e["fault_cell"]] for d, e in zip(err, eps)]))
            row["r0_factor_error"] = _q([e["r9_s"][e["fault_cell"]] - e["r0_scale"] for e in eps])
        out[f] = row
    return out


def estimator_accuracy(episodes: list[dict]) -> dict:
    """Twin estimate minus truth at the checkpoints, per plant state. Looked at before any
    monitor comparison (FOLLOWUP-003, 5)."""
    out: dict = {}
    for f in STATES:
        eps = [e for e in episodes if e["state"] == f]
        if not eps:
            continue
        err = np.concatenate([np.asarray(e["t_est"]) - np.asarray(e["t_true"]) for e in eps])
        row = {"all_cells_k": _q(err.ravel()), "hottest_cell_k": _q(np.concatenate(
            [(np.asarray(e["t_est"]) - np.asarray(e["t_true"]))[:, e["hot_cell"]] for e in eps]))}
        if f != "F0":
            row["fault_cell_k"] = _q(np.concatenate(
                [(np.asarray(e["t_est"]) - np.asarray(e["t_true"]))[:, e["fault_cell"]] for e in eps]))
            row["fault_cell_last_half_k"] = _q(np.concatenate(
                [(np.asarray(e["t_est"]) - np.asarray(e["t_true"]))[6:, e["fault_cell"]] for e in eps]))
            row["r0_factor_error"] = _q([e["s_hat"][e["fault_cell"]] - e["r0_scale"] for e in eps])
            row["cooling_factor_error_end"] = _q([e["c_hat"][-1][e["fault_cell"]] - e["h_scale"] for e in eps])
        row["r0_factor_error_healthy_cells"] = _q(np.concatenate(
            [np.delete(e["s_hat"], e["fault_cell"]) - 1.0 if e["fault_cell"] is not None else e["s_hat"] - 1.0
             for e in eps]))
        out[f] = row
    return out


def summarise(cfg: ControlConfig, episodes: list[dict]) -> dict:
    cal = [e for e in episodes if e["set"] == "B4_cal"]
    fit = fits(cfg, cal)
    result = evaluate(cfg, episodes, score_tables(cfg, episodes, fit))
    return {"plant": describe(cfg, episodes), "estimator": estimator_accuracy(episodes),
            "r9_accuracy": r9_accuracy(episodes),
            "fits": {k: {"a": v[0], "b_per_c": v[1]} for k, v in fit.items()},
            "verdict": verdict(result), "verdict_model_free_rules": verdict(result, RULES_MODEL_FREE),
            "verdict_spec_rules_only": verdict(result, RULES_SPEC),
            "stops": result.pop("stops"), "monitors": result}


def main() -> None:
    from simdet.control.run import dump

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(R4_CONFIG))
    ap.add_argument("--out", default=str(repo_root() / "results" / "d2_r4" / "g0"))
    args = ap.parse_args()
    cfg = load_control_config(args.config)
    episodes = generate(cfg)
    summary = summarise(cfg, episodes)
    summary["config"] = cfg.raw
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    keep = ("set", "index", "state", "kind", "t_amb", "derating", "fault_cell", "r0_scale", "h_scale",
            "attack_start_plan", "targets", "commands", "scales", "t_checkpoint", "r6_v", "s_hat", "c_hat",
            "t_est", "t_true", "twin_scores", "r9_est", "r9_s", "temp_minute", "t_max_k", "violation_time_s")
    dump(out / "g0_episodes.json", [{k: (np.round(e[k], 4) if isinstance(e[k], np.ndarray) else e[k]) for k in keep}
                                    for e in episodes])
    dump(out / "g0_summary.json", summary)
    v = summary["verdict"]
    print(f"{len(episodes)} episodes -> {out}; separated = {v['separated']}")


if __name__ == "__main__":
    main()
