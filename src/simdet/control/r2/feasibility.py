"""G0' feasibility of the second round (FOLLOWUP 5): run every policy without a monitor.

    python -m simdet.control.r2.feasibility [--config PATH] [--out DIR]

Writes g0_episodes.json (one row per episode) and g0_summary.json to results/d2_r2/g0/.
No API call. Scores of the monitors that need no LLM (twin M2, rules R1', R2, R3) are computed
along the way: A3' and A5 need the T0 threshold of M2, and the rule baselines cost nothing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from simdet.config import repo_root
from simdet.control import evalx, twin_monitor
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.plant import run_episode
from simdet.control.r2.policies import Policy2
from simdet.control.r2.signals import target_signal

R2_CONFIG = repo_root() / "config" / "control_r2.yaml"
SETS = ("B2_cal", "B2_test", "A2p", "A4", "A4s", "A3p", "A5")
ATTACKS = SETS[2:]
RULES = {"R1'": evalx.rule_mean_tracking, "R2": evalx.rule_temperature, "R3": evalx.rule_rms}


def episode_inputs(cfg: ControlConfig, set_name: str, index: int):
    """Request kind, targets and the random streams of one episode; the same in every twin condition."""
    n = cfg["episodes"][set_name]
    kind = (cfg["episodes"].get("kinds") or {}).get(set_name) or ("normal" if index < n // 2 else "heavy")
    seq = np.random.SeedSequence([cfg["episodes"]["seed"], SETS.index(set_name), index])
    r_req, r_pol, r_noise, r_text = (np.random.default_rng(s) for s in seq.spawn(4))
    return kind, target_signal(cfg, kind, r_req), r_pol, r_noise, r_text


def run_one(cfg: ControlConfig, condition: str, set_name: str, index: int, known: float | None = None) -> dict:
    plant = cfg["plant"]
    n, period = plant["plan_len"], plant["command_period_s"]
    kind, targets, r_pol, r_noise, _ = episode_inputs(cfg, set_name, index)
    policy = Policy2(cfg, "B2" if set_name.startswith("B2") else set_name, r_pol, known)
    ep = run_episode(cfg, cfg.plant_cell(condition), policy, np.repeat(targets, n), r_noise)
    cmd = ep.commands.reshape(-1, n)
    lo, hi = plant["soc_guard"]
    return {
        "condition": condition, "set": set_name, "index": index, "kind": kind,
        "attack_start_plan": ep.attack_start_plan,
        "request": ep.request, "commands": ep.commands, "targets": targets,
        "twin_scores": ep.twin_scores, "t_checkpoint": ep.t_checkpoint,
        "temp_minute": ep.temp[::period],
        "dT_max_k": float(ep.temp.max() - cfg.cell.t_amb),
        "violation_time_s": ep.violation_time_s(plant["t_limit_k"]),
        "soc_min": float(ep.soc.min()), "soc_max": float(ep.soc.max()),
        "soc_guard_violated": bool(ep.soc.min() < lo - 1e-9 or ep.soc.max() > hi + 1e-9),
        "n_guard_limited": ep.n_guard_limited, "n_actuator_clipped": ep.n_actuator_clipped,
        "plan_mean_error_a": np.abs(cmd.mean(axis=1) - targets),
        "plan_rms_a": np.sqrt((cmd ** 2).mean(axis=1)),
        "n_over_rated": (np.abs(cmd) > plant["rated_continuous_a"] + 1e-9).sum(axis=1),
    }


def generate(cfg: ControlConfig) -> tuple[list[dict], float]:
    """All episodes and the M2 threshold of the calibration condition (known to A3' and A5)."""
    cal_cond = cfg["threshold"]["calibration_condition"]
    episodes = [run_one(cfg, cal_cond, "B2_cal", i) for i in range(cfg["episodes"]["B2_cal"])]
    thr = twin_monitor.calibrate_threshold([e["twin_scores"].max() for e in episodes],
                                           cfg["threshold"]["false_stop_target"])
    for condition in cfg["conditions"]:
        for set_name in SETS[1:]:
            known = thr if set_name in ("A3p", "A5") else None
            episodes += [run_one(cfg, condition, set_name, i, known) for i in range(cfg["episodes"].get(set_name, 0))]
    return episodes, thr


def score_tables(cfg: ControlConfig, episodes: list[dict]) -> dict:
    key = evalx.episode_key
    scores = {"M2": {key(e): np.asarray(e["twin_scores"], dtype=float) for e in episodes}}
    for name, rule in RULES.items():
        scores[name] = {key(e): rule(cfg, e) for e in episodes}
    return scores


def _q(values) -> dict:
    v = np.asarray(values, dtype=float)
    return {"min": float(v.min()), "median": float(np.median(v)), "max": float(v.max())} if v.size else {}


def summarise(cfg: ControlConfig, episodes: list[dict], thr: float) -> dict:
    out: dict = {"twin_threshold_k": thr, "sets": {}}
    for condition in cfg["conditions"]:
        for set_name in SETS:
            eps = [e for e in episodes if e["condition"] == condition and e["set"] == set_name]
            if not eps:
                continue
            attack = [np.arange(e["plan_rms_a"].size) >= e["attack_start_plan"] for e in eps] \
                if set_name in ATTACKS else [np.ones(e["plan_rms_a"].size, bool) for e in eps]
            rms = np.concatenate([e["plan_rms_a"][a] for e, a in zip(eps, attack)])
            means = np.concatenate([np.abs(e["commands"].reshape(-1, cfg["plant"]["plan_len"]).mean(axis=1))[a]
                                    for e, a in zip(eps, attack)])
            viol = [e["violation_time_s"] for e in eps if e["violation_time_s"] is not None]
            out["sets"][f"{condition}|{set_name}"] = {
                "n": len(eps), "violations": len(viol),
                "violation_time_min": _q(np.array(viol) / 60.0),
                "dT_max_k": _q([e["dT_max_k"] for e in eps]),
                "plan_rms_a": _q(rms),
                "episode_max_plan_rms_a": _q([e["plan_rms_a"].max() for e in eps]),
                "form_factor": _q(rms[means > 1.0] / means[means > 1.0]),
                "plan_mean_error_max_a": float(max(e["plan_mean_error_a"][a].max() for e, a in zip(eps, attack))),
                "n_over_rated_per_plan": _q(np.concatenate([e["n_over_rated"][a] for e, a in zip(eps, attack)])),
                "soc_guard_violated": int(sum(e["soc_guard_violated"] for e in eps)),
                "n_guard_limited": int(sum(e["n_guard_limited"] for e in eps)),
                "n_actuator_clipped": int(sum(e["n_actuator_clipped"] for e in eps)),
            }
    result = evalx.evaluate(cfg, episodes, score_tables(cfg, episodes), cal_set="B2_cal", test_set="B2_test",
                            attack_sets=ATTACKS, fixed_condition=cfg["threshold"]["calibration_condition"])
    for cond in result["conditions"].values():
        cond.pop("stops")
    out["no_llm_monitors"] = result
    return out


def main() -> None:
    from simdet.control.run import dump

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(R2_CONFIG))
    ap.add_argument("--out", default=str(repo_root() / "results" / "d2_r2" / "g0"))
    args = ap.parse_args()
    cfg = load_control_config(args.config)
    episodes, thr = generate(cfg)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    keep = ("condition", "set", "index", "kind", "attack_start_plan", "targets", "commands", "dT_max_k",
            "violation_time_s", "soc_min", "soc_max", "n_guard_limited", "plan_rms_a", "twin_scores")
    dump(out / "g0_episodes.json", [{k: e[k] for k in keep} for e in episodes])
    summary = summarise(cfg, episodes, thr)
    summary["config"] = cfg.raw
    dump(out / "g0_summary.json", summary)
    print(f"{len(episodes)} episodes -> {out}")


if __name__ == "__main__":
    main()
