"""Confirmation run of the fourth plant on a new seed (docs/SIMDET_D2_PREREG_4.md). No API call.

    python -m simdet.control.r4.confirm            # both settings, all model-error conditions
    python -m simdet.control.r4.confirm --dry 12   # 12 episodes per set, no file written

Writes results/d2_r4/confirm/{summary.json, episodes_<setting>.json}.

Condition "T0" is the monitor model equal to the plant. In a model-error condition only the
scores of the twin (M2) and of R9 change; everything else, including the episodes, is the same.
Thresholds: "recalibrated" = from the calibration set scored with the same model error (the
pre-registered main reading); "fixed" = the T0 thresholds kept.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import replace
from pathlib import Path

import numpy as np
import yaml

from simdet.config import repo_root
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.metrics import _rate, first_stop, is_safe, paired_diff
from simdet.control.r4 import feasibility as F
from simdet.control.r4 import pack as pk
from simdet.control.r4.g0_variants import with_overrides
from simdet.control.r4.plant import MonitorModel, nominal_pack, run_episode
from simdet.control.r4.policies import Policy4

CONFIRM_CONFIG = repo_root() / "config" / "control_r4_confirm.yaml"
MODEL_BASED = ("R9", "M2")
key = F.key


def load_plan(path: str | Path = CONFIRM_CONFIG) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def setting_config(plan: dict, setting: str, per_set: int | None = None) -> ControlConfig:
    base = load_control_config(repo_root() / "config" / plan["base"])
    raw = copy.deepcopy(base.raw)
    raw["episodes"].update(plan["episodes"])
    if per_set is not None:
        raw["episodes"].update({s: per_set for s in F.SETS})
    return with_overrides(ControlConfig(raw, base.cell), plan["settings"][setting])


def condition_name(param: str, value: float) -> str:
    return f"{param}{value:+g}"


def monitor_models(plan: dict, nominal: pk.Pack) -> list[MonitorModel]:
    out = []
    for param, values in plan["model_errors"].items():
        for e in values:
            name = condition_name(param, e)
            if param == "alpha":
                out.append(MonitorModel(name, replace(nominal, cell=replace(nominal.cell, alpha=nominal.cell.alpha * (1 + e)))))
            elif param == "k":
                out.append(MonitorModel(name, replace(nominal, k=nominal.k * (1 + e))))
            elif param == "h":
                out.append(MonitorModel(name, replace(nominal, h=nominal.h * (1 + e))))
            elif param == "v_bias_mv":
                out.append(MonitorModel(name, nominal, v_bias=1e-3 * e))
            else:
                raise ValueError(param)
    return out


def _run(job: tuple[dict, str, int | None, str, int]) -> dict:
    plan, setting, per_set, set_name, index = job
    cfg = setting_config(plan, setting, per_set)
    nominal = nominal_pack(cfg)
    inp = F.episode_inputs(cfg, nominal, set_name, index)
    policy = Policy4(cfg, "B4" if set_name.startswith("B4") else set_name, inp["r_pol"], inp["pack"], inp["fault_cell"])
    ep = run_episode(cfg, inp["pack"], nominal, policy, inp["targets"], inp["t_amb"], inp["r_noise"],
                     models=monitor_models(plan, nominal))
    ep.update(condition="T0", set=set_name, index=index, **{k: inp[k] for k in
              ("state", "kind", "derating", "fault_cell", "r0_scale", "h_scale")})
    return ep


def generate(plan: dict, setting: str, per_set: int | None = None) -> list[dict]:
    from concurrent.futures import ProcessPoolExecutor

    cfg = setting_config(plan, setting, per_set)
    jobs = [(plan, setting, per_set, s, i) for s in F.SETS for i in range(cfg["episodes"][s])]
    with ProcessPoolExecutor(int(plan["workers"])) as pool:
        return list(pool.map(_run, jobs, chunksize=8))


# -- evaluation ----------------------------------------------------------------------------------
def _rows(result: dict) -> dict:
    """Safety (pooled and per state), false stop and thresholds of every monitor, compactly."""
    out = {}
    for name, m in result["monitors"].items():
        out[name] = {"false_stop": m["false_stop"], "cal_false_stop": m["cal_false_stop"]["all"],
                     "safety": {a: v["safety"] for a, v in m["attacks"].items()},
                     "catch": {a: v["catch"]["all"] for a, v in m["attacks"].items()}}
    return out


def _fixed(cfg: ControlConfig, episodes: list[dict], tables: dict, thresholds: dict) -> dict:
    """M2 and R9 with given thresholds (the T0 ones) on the scores of a model-error condition."""
    by = {s: [e for e in episodes if e["set"] == s] for s in F.SETS}
    out = {}
    for name in MODEL_BASED:
        stop = {key(e): first_stop(tables[name][key(e)], thresholds[name]) for e in episodes}
        out[name] = {"false_stop": _rate([stop[key(e)] is not None for e in by["B4_test"]]),
                     "safety": {a: _rate([is_safe(cfg, e, stop[key(e)]) for e in by[a]]) for a in F.ATTACKS}}
    return out


def _safe_flags(cfg: ControlConfig, episodes: list[dict], stops: dict, name: str, attack: str) -> list[bool]:
    return [is_safe(cfg, e, stops[name][key(e)]) for e in episodes if e["set"] == attack]


def _best(result: dict, rules: tuple[str, ...], attack: str) -> str:
    return max(rules, key=lambda r: result["monitors"][r]["attacks"][attack]["safety"]["all"]["rate"])


def analyse(plan: dict, cfg: ControlConfig, episodes: list[dict]) -> dict:
    crit = plan["criteria"]
    primary = crit["primary_attack"]
    cal = [e for e in episodes if e["set"] == "B4_cal"]
    fit = F.fits(cfg, cal)
    base_tables = F.score_tables(cfg, episodes, fit)

    t0 = F.evaluate(cfg, episodes, base_tables)
    stops0 = t0.pop("stops")
    out: dict = {"plant": F.describe(cfg, episodes), "estimator": F.estimator_accuracy(episodes),
                 "r9_accuracy": F.r9_accuracy(episodes),
                 "fits": {k: {"a": v[0], "b_per_c": v[1]} for k, v in fit.items()},
                 "T0": {"thresholds": t0["thresholds"], "monitors": _rows(t0),
                        "verdict": F.verdict(t0), "verdict_model_free_rules": F.verdict(t0, F.RULES_MODEL_FREE)}}

    # paired differences at T0 on every attack
    diffs = {}
    for attack in F.ATTACKS:
        mf, anyr = _best(t0, F.RULES_MODEL_FREE, attack), _best(t0, F.RULES, attack)
        m2 = _safe_flags(cfg, episodes, stops0, "M2", attack)
        r9 = _safe_flags(cfg, episodes, stops0, "R9", attack)
        diffs[attack] = {
            "best_model_free_rule": mf, "best_rule": anyr,
            "M2_minus_best_model_free": paired_diff(m2, _safe_flags(cfg, episodes, stops0, mf, attack)),
            "M2_minus_best_rule": paired_diff(m2, _safe_flags(cfg, episodes, stops0, anyr, attack)),
            "M2_minus_R9": paired_diff(m2, r9),
            "R9_minus_best_model_free": paired_diff(r9, _safe_flags(cfg, episodes, stops0, mf, attack))}
    out["T0"]["paired"] = diffs

    # lead time of the stop before the violation, and stops of episodes that would not violate
    plan_s = cfg["plant"]["plan_len"] * cfg["plant"]["command_period_s"]
    timing = {}
    for attack in F.ATTACKS:
        eps = [e for e in episodes if e["set"] == attack]
        timing[attack] = {}
        for name in MODEL_BASED + ("R4", "R7"):
            lead = [(e["violation_time_s"] - stops0[name][key(e)] * plan_s) / 60 for e in eps
                    if e["violation_time_s"] is not None and is_safe(cfg, e, stops0[name][key(e)])]
            quiet = [e for e in eps if e["violation_time_s"] is None]
            timing[attack][name] = {"lead_min": F._q(lead), "stopped_without_violation":
                                    [int(sum(stops0[name][key(e)] is not None for e in quiet)), len(quiet)]}
    out["T0"]["timing"] = timing

    # model-error conditions
    errors: dict = {}
    for param, values in plan["model_errors"].items():
        for e_val in values:
            name = condition_name(param, e_val)
            tables = dict(base_tables)
            tables["M2"] = {key(e): np.asarray(e["model_scores"][name]["M2"], dtype=float) for e in episodes}
            tables["R9"] = {key(e): np.asarray(e["model_scores"][name]["R9"], dtype=float) for e in episodes}
            res = F.evaluate(cfg, episodes, tables)
            res.pop("stops")
            rows = _rows(res)
            errors[name] = {"parameter": param, "error": e_val,
                            "recalibrated": {"thresholds": {m: res["thresholds"][m] for m in MODEL_BASED},
                                             "monitors": {m: rows[m] for m in MODEL_BASED},
                                             "verdict": F.verdict(res)},
                            "fixed": _fixed(cfg, episodes, tables, t0["thresholds"])}
    out["model_errors"] = errors

    # hypotheses
    def rate(res_rows: dict, name: str, attack: str) -> float:
        return res_rows[name]["safety"][attack]["all"]["rate"]

    rows0 = out["T0"]["monitors"]
    viol = rows0["M0"]["safety"][primary]["all"]
    viol_rate = 1.0 - viol["rate"]
    mf = diffs[primary]["best_model_free_rule"]
    m2, r9, mfs = rate(rows0, "M2", primary), rate(rows0, "R9", primary), rate(rows0, mf, primary)
    hyp_c = {}
    for param, values in plan["model_errors"].items():
        worst = min(rate(errors[condition_name(param, v)]["recalibrated"]["monitors"], "M2", primary)
                    for v in values if abs(v) == max(abs(x) for x in values))
        hyp_c[param] = {"m2_safety_T0": m2, "m2_safety_largest_error_worse_sign": worst,
                        "drop_pt": 100 * (m2 - worst), "holds": bool(100 * (m2 - worst) >= crit["error_drop_pt"] - 1e-9)}
    out["hypotheses"] = {
        "primary_attack": primary, "violation_rate_unmonitored": viol_rate,
        "main_verdict_separated": bool(out["T0"]["verdict"]["attacks"][primary]["counts"]),
        "a": {"m2": m2, "best_model_free_rule": mf, "best_model_free_safety": mfs, "difference_pt": 100 * (m2 - mfs),
              "holds": bool(viol_rate >= crit["min_violation_rate"] and 100 * (m2 - mfs) >= crit["min_difference_pt"] - 1e-9)},
        "b": {"m2": m2, "r9": r9, "best_model_free_safety": mfs,
              "share_of_gap_closed_by_r9": (r9 - mfs) / (m2 - mfs) if m2 > mfs else None,
              "holds": bool(mfs < r9 <= m2)},
        "c": hyp_c}
    return out


KEEP = ("set", "index", "state", "kind", "t_amb", "derating", "fault_cell", "r0_scale", "h_scale", "attack_start_plan",
        "targets", "commands", "scales", "t_checkpoint", "r6_v", "s_hat", "t_est", "t_true", "twin_scores", "r9_est",
        "r9_s", "t_max_k", "violation_time_s", "model_scores")


def _round(v):
    if isinstance(v, np.ndarray):
        return np.round(v, 4)
    if isinstance(v, dict):
        return {k: _round(x) for k, x in v.items()}
    return v


def main() -> None:
    from simdet.control.run import dump

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(CONFIRM_CONFIG))
    ap.add_argument("--out", default=str(repo_root() / "results" / "d2_r4" / "confirm"))
    ap.add_argument("--dry", type=int, default=None, help="episodes per set; nothing is written")
    args = ap.parse_args()
    plan = load_plan(args.config)
    summary: dict = {"plan": plan, "settings": {}}
    out = Path(args.out)
    for setting in plan["settings"]:
        cfg = setting_config(plan, setting, args.dry)
        episodes = generate(plan, setting, args.dry)
        summary["settings"][setting] = analyse(plan, cfg, episodes)
        summary["settings"][setting]["config"] = cfg.raw
        h = summary["settings"][setting]["hypotheses"]
        print(f"{setting}: {len(episodes)} episodes; separated = {h['main_verdict_separated']}, "
              f"(a) {h['a']['holds']}, (b) {h['b']['holds']}, (c) { {k: v['holds'] for k, v in h['c'].items()} }")
        if args.dry is None:
            out.mkdir(parents=True, exist_ok=True)
            dump(out / f"episodes_{setting}.json", [{k: _round(e[k]) for k in KEEP} for e in episodes])
    if args.dry is None:
        dump(out / "summary.json", summary)
        print(f"-> {out}")


if __name__ == "__main__":
    main()
