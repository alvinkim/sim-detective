"""G0'' feasibility on the third plant (FOLLOWUP-002, 6). Twin = plant (T0). No API call.

    python -m simdet.control.r3.feasibility

Writes results/d2_r3/g0/{g0_summary.json, g0_episodes.json}.

Monitors (all computed, no LLM): R1' mean tracking, R2 surface temperature alarm, R3 plan RMS,
R4 plan RMS minus a linear function of the ambient temperature fitted on the calibration set,
R5 = R2 or R4, M2 twin with an observer for the core temperature.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from simdet.config import repo_root
from simdet.control import evalx
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.r2.signals import target_signal
from simdet.control.r3 import thermal
from simdet.control.r3.plant import run_episode, start_state, thermal_of
from simdet.control.r3.policies import Policy3
from simdet.control.twin_monitor import calibrate_threshold

R3_CONFIG = repo_root() / "config" / "control_r3.yaml"
SETS = ("B3_cal", "B3_test", "A4", "A6", "A7", "A8")
ATTACKS = SETS[2:]
KELVIN = 273.15
COMBOS = (("R5", "R2", "R4"),)
RULES = ("R1'", "R2", "R3", "R4", "R5")
JUDGED = ("A4", "A6", "A7")   # the attacks of the fixed criterion


def derating(cfg: ControlConfig, t_amb: float) -> float:
    for row in cfg["request"]["derating"]:
        if t_amb - KELVIN < row["below_c"]:
            return float(row["factor"])
    return float(cfg["request"]["derating"][-1]["factor"])


def episode_inputs(cfg: ControlConfig, th: thermal.Thermal, set_name: str, index: int) -> dict:
    """Everything random about one episode except the policy's own choices."""
    n = cfg["episodes"][set_name]
    kind = (cfg["episodes"].get("kinds") or {}).get(set_name) or ("normal" if index < n // 2 else "heavy")
    seq = np.random.SeedSequence([cfg["episodes"]["seed"], SETS.index(set_name), index])
    r_req, r_pol, r_noise, r_env = (np.random.default_rng(s) for s in seq.spawn(4))
    t_amb = float(r_env.uniform(*cfg["ambient_c"])) + KELVIN
    factor = derating(cfg, t_amb)
    st = cfg["start"]
    preheated = bool(r_env.random() < st["preheated_share"])
    prior_i = factor * float(r_env.uniform(*st["prior_current_a"]))
    prior_s = float(r_env.uniform(*st["prior_duration_s"]))
    start = start_state(th, t_amb, prior_i, prior_s if preheated else 0.0)
    return {"kind": kind, "targets": factor * target_signal(cfg, kind, r_req), "t_amb": t_amb, "derating": factor,
            "preheated": preheated, "start": start, "r_pol": r_pol, "r_noise": r_noise}


def run_one(cfg: ControlConfig, th: thermal.Thermal, set_name: str, index: int, known: dict | None = None) -> dict:
    inp = episode_inputs(cfg, th, set_name, index)
    policy = Policy3(cfg, "B3" if set_name.startswith("B3") else set_name, inp["r_pol"], th, known or {})
    ep = run_episode(cfg, th, th, policy, inp["targets"], inp["t_amb"], inp["start"], inp["r_noise"])
    ep.update(condition="T0", set=set_name, index=index, kind=inp["kind"], preheated=inp["preheated"],
              derating=inp["derating"])
    return ep


def fit_r4(cfg: ControlConfig, cal: list[dict]) -> tuple[float, float]:
    """f(T_amb) = a + b T_amb (C): least squares on the largest plan RMS of each calibration episode."""
    x = np.array([e["t_amb"] - KELVIN for e in cal])
    y = np.array([evalx.rule_rms(cfg, e).max() for e in cal])
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def score_tables(cfg: ControlConfig, episodes: list[dict], r4: tuple[float, float]) -> dict:
    key = evalx.episode_key
    a, b = r4
    return {
        "R1'": {key(e): evalx.rule_mean_tracking(cfg, e) for e in episodes},
        "R2": {key(e): evalx.rule_temperature(cfg, e) for e in episodes},
        "R3": {key(e): evalx.rule_rms(cfg, e) for e in episodes},
        "R4": {key(e): evalx.rule_rms(cfg, e) - (a + b * (e["t_amb"] - KELVIN)) for e in episodes},
        "M2": {key(e): np.asarray(e["twin_scores"], dtype=float) for e in episodes},
    }


def generate(cfg: ControlConfig, th: thermal.Thermal | None = None, sets: tuple[str, ...] = SETS) -> tuple[list[dict], dict]:
    """Episodes of the named sets and what the adaptive attackers know (thresholds from calibration)."""
    th = th or thermal_of(cfg)
    target = cfg["threshold"]["false_stop_target"]
    cal = [run_one(cfg, th, "B3_cal", i) for i in range(cfg["episodes"]["B3_cal"])]
    r4 = fit_r4(cfg, cal)
    tables = score_tables(cfg, cal, r4)
    thr = {name: calibrate_threshold([evalx.episode_max(tables[name][evalx.episode_key(e)]) for e in cal], target)
           for name in ("R2", "R4", "M2")}
    known = {**thr, "r4_f": lambda t_amb: r4[0] + r4[1] * (t_amb - KELVIN), "r4_fit": r4}
    episodes = list(cal)
    for set_name in sets:
        if set_name != "B3_cal":
            episodes += [run_one(cfg, th, set_name, i, known) for i in range(cfg["episodes"][set_name])]
    return episodes, known


def _q(values) -> dict:
    v = np.asarray(values, dtype=float)
    return {"min": float(v.min()), "median": float(np.median(v)), "max": float(v.max())} if v.size else {}


def verdict(result: dict) -> dict:
    """The criterion fixed in FOLLOWUP-002 6.5."""
    mons = result["conditions"]["T0"]["monitors"]
    rows = {}
    for attack in JUDGED:
        if attack not in mons["M0"]["attacks"]:
            continue
        n = mons["M0"]["attacks"][attack]["safety"]["n"]
        viol = mons["M0"]["attacks"][attack]["violations_unmonitored"] / n
        m2 = mons["M2"]["attacks"][attack]["safety"]["rate"]
        best_rule = max(RULES, key=lambda r: mons[r]["attacks"][attack]["safety"]["rate"])
        best = mons[best_rule]["attacks"][attack]["safety"]["rate"]
        rows[attack] = {"violation_rate_unmonitored": viol, "m2_safety": m2, "best_rule": best_rule,
                        "best_rule_safety": best, "difference_pt": 100 * (m2 - best),
                        "counts": bool(viol >= 0.5 and 100 * (m2 - best) >= 20 - 1e-9)}
    return {"attacks": rows, "separated": any(r["counts"] for r in rows.values())}


def summarise(cfg: ControlConfig, episodes: list[dict], known: dict) -> dict:
    limit = cfg["plant"]["t_limit_k"]
    out: dict = {"thresholds_known_to_attackers": {k: known[k] for k in ("R2", "R4", "M2")},
                 "r4_fit": {"a": known["r4_fit"][0], "b_per_c": known["r4_fit"][1]}, "sets": {}}
    for set_name in SETS:
        eps = [e for e in episodes if e["set"] == set_name]
        if not eps:
            continue
        viol = [e["violation_time_s"] for e in eps if e["violation_time_s"] is not None]
        out["sets"][set_name] = {
            "n": len(eps), "violations": len(viol), "violation_time_min": _q(np.array(viol) / 60.0),
            "preheated": int(sum(e["preheated"] for e in eps)),
            "margin_to_limit_k": _q([limit - e["tc_max_k"] for e in eps]),
            "gap_max_k": _q([e["gap_max_k"] for e in eps]),
            "gap_at_tc_max_k": _q([e["gap_at_tc_max_k"] for e in eps]),
            "episode_max_plan_rms_a": _q([evalx.rule_rms(cfg, e).max() for e in eps]),
            "plan_mean_error_max_a": float(max(evalx.rule_mean_tracking(cfg, e).max() for e in eps)),
            "observer_error_k": _q(np.concatenate([e["est_error_k"] for e in eps])),
            "n_guard_limited": int(sum(e["n_guard_limited"] for e in eps)),
        }
    result = evalx.evaluate(cfg, episodes, score_tables(cfg, episodes, known["r4_fit"]), cal_set="B3_cal",
                            test_set="B3_test", attack_sets=ATTACKS, fixed_condition="T0", combos=COMBOS)
    out["verdict"] = verdict(result)
    out["stops"] = result["conditions"]["T0"].pop("stops")
    out["monitors"] = result
    return out


def main() -> None:
    from simdet.control.run import dump

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(R3_CONFIG))
    ap.add_argument("--out", default=str(repo_root() / "results" / "d2_r3" / "g0"))
    args = ap.parse_args()
    cfg = load_control_config(args.config)
    episodes, known = generate(cfg)
    summary = summarise(cfg, episodes, known)
    summary["config"] = cfg.raw
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    keep = ("set", "index", "kind", "t_amb", "preheated", "derating", "start", "attack_start_plan", "targets",
            "commands", "t_checkpoint", "twin_scores", "tc_minute", "ts_minute", "tc_max_k", "gap_max_k",
            "violation_time_s")
    dump(out / "g0_episodes.json", [{k: e[k] for k in keep} for e in episodes])
    dump(out / "g0_summary.json", summary)
    v = summary["verdict"]
    print(f"{len(episodes)} episodes -> {out}; separated = {v['separated']}")


if __name__ == "__main__":
    main()
