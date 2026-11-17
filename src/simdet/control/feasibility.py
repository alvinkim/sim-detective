"""G0 feasibility (spec 9): run B and A1-A3 without any monitor and tabulate what happens.

    python -m simdet.control.feasibility [--config PATH] [--out DIR]

Writes g0_episodes.json (one row per episode) and g0_summary.json. No API call is made.
The twin monitor score is computed along the way because A3 needs the T0 threshold; that
threshold is provisional until the configuration is fixed in G1.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from simdet.config import repo_root
from simdet.control import twin_monitor
from simdet.control.config import ControlConfig, load_control_config, load_templates
from simdet.control.plant import Episode, run_episode
from simdet.control.policies import Policy
from simdet.control.signals import request_signal
from simdet.sim.cell import Fault, State, simulate

SETS = ("B_cal", "B_test", "A1", "A2", "A3")


def episode_inputs(cfg: ControlConfig, set_name: str, index: int):
    """Request kind and the three random streams of one episode. They do not depend on the
    twin condition, so the same episode index is the same request in every condition."""
    n = cfg["episodes"][set_name]
    kind = (cfg["episodes"].get("kinds") or {}).get(set_name) or ("normal" if index < n // 2 else "heavy")
    seq = np.random.SeedSequence([cfg["episodes"]["seed"], SETS.index(set_name), index])
    r_req, r_pol, r_noise = (np.random.default_rng(s) for s in seq.spawn(3))
    return kind, request_signal(cfg, kind, r_req), r_pol, r_noise


def run_set(cfg: ControlConfig, condition: str, set_name: str, templates,
            known_threshold_k: float | None = None) -> list[tuple[str, Episode]]:
    policy_name = "B" if set_name.startswith("B") else set_name
    out = []
    for i in range(cfg["episodes"][set_name]):
        kind, request, r_pol, r_noise = episode_inputs(cfg, set_name, i)
        policy = Policy(cfg, policy_name, templates, r_pol, known_threshold_k)
        out.append((kind, run_episode(cfg, cfg.plant_cell(condition), policy, request, r_noise)))
    return out


def episode_row(cfg: ControlConfig, condition: str, set_name: str, index: int, kind: str,
                ep: Episode) -> dict:
    plant = cfg["plant"]
    lo, hi = plant["soc_guard"]
    t_viol = ep.violation_time_s(plant["t_limit_k"])
    return {
        "condition": condition, "set": set_name, "index": index, "kind": kind,
        "attack_start_plan": ep.attack_start_plan,
        "dT_max_k": float(ep.temp.max() - cfg.cell.t_amb),
        "dT_end_k": float(ep.temp[-1] - cfg.cell.t_amb),
        "violation": t_viol is not None,
        "violation_time_s": t_viol,
        "soc_min": float(ep.soc.min()), "soc_max": float(ep.soc.max()),
        "soc_guard_violated": bool(ep.soc.min() < lo - 1e-9 or ep.soc.max() > hi + 1e-9),
        "n_guard_limited": ep.n_guard_limited, "n_actuator_clipped": ep.n_actuator_clipped,
        "mean_abs_request_a": float(np.abs(ep.request).mean()),
        "mean_abs_command_a": float(np.abs(ep.commands).mean()),
        "max_abs_command_a": float(np.abs(ep.commands).max()),
        "tracking_rms_a": float(np.sqrt(np.mean((ep.commands - ep.request) ** 2))),
        "twin_score_max_k": float(ep.twin_scores.max()),
        "twin_scores_k": [round(float(s), 4) for s in ep.twin_scores],
    }


def precheck(cfg: ControlConfig) -> dict[str, float]:
    """dT_max of +/-I alternating every 60 s for 3600 s on the nominal cell (spec 4 table)."""
    out = {}
    for amp in (30, 40, 50, 60, 70, 80):
        current = np.tile(np.concatenate([np.full(60, float(amp)), np.full(60, -float(amp))]), 30)
        traj, final = simulate(cfg.cell, Fault(), State(0.5, 0.0, 0.0, cfg.cell.t_amb), current,
                               soc_limits=None)
        out[str(amp)] = float(max(traj["temp"].max(), final.temp) - cfg.cell.t_amb)
    return out


def run(cfg: ControlConfig) -> tuple[list[dict], dict]:
    templates = load_templates()
    target = cfg["threshold"]["false_stop_target"]
    rows: list[dict] = []
    thresholds: dict[str, float] = {}

    def add(condition: str, set_name: str, known: float | None = None) -> list[dict]:
        new = [episode_row(cfg, condition, set_name, i, kind, ep)
               for i, (kind, ep) in enumerate(run_set(cfg, condition, set_name, templates, known))]
        rows.extend(new)
        return new

    for condition in cfg["conditions"]:
        cal = add(condition, "B_cal")
        thresholds[condition] = twin_monitor.calibrate_threshold(
            [r["twin_score_max_k"] for r in cal], target)
    for condition in cfg["conditions"]:
        for set_name in ("B_test", "A1", "A2"):
            add(condition, set_name)
        known = cfg["policy"]["a3"]["known_threshold_condition"]  # spec 6.5: T0
        add(condition, "A3", thresholds[condition if known == "same" else known])

    for r in rows:  # what the provisional twin monitor would have done (not part of G0's question)
        thr = thresholds[r["condition"]]
        hits = [j for j, s in enumerate(r["twin_scores_k"]) if s >= thr]
        r["twin_stop_plan"] = hits[0] if hits else None
    summary = {"precheck_dT_max_k": precheck(cfg), "twin_threshold_k": thresholds,
               "config": cfg.raw}
    return rows, summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--out", default=str(repo_root() / "results" / "d2_g0"))
    args = ap.parse_args()
    cfg = load_control_config(args.config)
    rows, summary = run(cfg)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "g0_episodes.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    (out / "g0_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"{len(rows)} episodes -> {out}")


if __name__ == "__main__":
    main()
