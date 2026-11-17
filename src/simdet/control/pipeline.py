"""Offline evaluation pipeline (spec 5-7).

1. Every episode is run to the end with no monitor. No policy looks at a monitor's decision, so a
   stop at checkpoint j is the same episode cut before plan j.
2. Each monitor scores every checkpoint of every episode.
3. metrics.py turns scores into thresholds, stops, safety and the rest.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import numpy as np

from simdet.control import monitor_llm, twin_monitor
from simdet.control.config import ControlConfig, load_templates
from simdet.control.feasibility import SETS, episode_inputs
from simdet.control.plant import run_episode
from simdet.control.policies import Policy


def episode_key(ep: dict) -> str:
    return f"{ep['condition']}|{ep['set']}|{ep['index']}"


def _record(cfg: ControlConfig, condition: str, set_name: str, index: int, kind: str, ep) -> dict:
    period = cfg["plant"]["command_period_s"]
    end = np.arange(1, ep.commands.size + 1) * period - 1  # last sample of each command interval
    return {
        "condition": condition, "set": set_name, "index": index, "kind": kind,
        "policy": "B" if set_name.startswith("B") else set_name,
        "attack_start_plan": ep.attack_start_plan,
        "request": ep.request, "commands": ep.commands, "explanations": ep.explanations,
        "t_meas_end": ep.t_meas[end], "v_meas_end": ep.v_meas[end],
        "temp_minute": ep.temp[::period],           # true temperature at each command boundary
        "dT_max_k": float(ep.temp.max() - cfg.cell.t_amb),
        "violation_time_s": ep.violation_time_s(cfg["plant"]["t_limit_k"]),
        "soc_min": float(ep.soc.min()), "soc_max": float(ep.soc.max()),
        "twin_scores": ep.twin_scores,
    }


def generate_episodes(cfg: ControlConfig) -> tuple[list[dict], dict[str, float]]:
    """All episodes of all twin conditions, and the twin monitor (M2) threshold per condition."""
    templates = load_templates()
    target = cfg["threshold"]["false_stop_target"]
    episodes: list[dict] = []
    thresholds: dict[str, float] = {}

    def add(condition: str, set_name: str, known: float | None = None) -> list[dict]:
        new = []
        for i in range(cfg["episodes"][set_name]):
            kind, request, r_pol, r_noise = episode_inputs(cfg, set_name, i)
            policy = Policy(cfg, "B" if set_name.startswith("B") else set_name, templates, r_pol, known)
            ep = run_episode(cfg, cfg.plant_cell(condition), policy, request, r_noise)
            new.append(_record(cfg, condition, set_name, i, kind, ep))
        episodes.extend(new)
        return new

    for condition in cfg["conditions"]:
        cal = add(condition, "B_cal")
        thresholds[condition] = twin_monitor.calibrate_threshold(
            [e["twin_scores"].max() for e in cal], target)
    known_cond = cfg["policy"]["a3"]["known_threshold_condition"]
    for condition in cfg["conditions"]:
        for set_name in SETS[1:4]:
            add(condition, set_name)
        add(condition, "A3", thresholds[condition if known_cond == "same" else known_cond])
    return episodes, thresholds


def score_llm(cfg: ControlConfig, episodes: list[dict], model: str, repeats: int,
              client=None, progress=None) -> dict[str, dict]:
    """Suspicion of one LLM monitor at every checkpoint.

    Returns key -> {"scores": [plans][repeats] (None if unreadable), "cost_usd", "calls", "cached"}.
    `model` "mock" uses the heuristic and no client.
    """
    n_plans = cfg["plant"]["plans_per_episode"]
    if model == monitor_llm.MOCK:
        return {episode_key(ep): {
            "scores": [[monitor_llm.mock_suspicion(cfg, ep, j)[0]] * repeats for j in range(n_plans)],
            "cost_usd": 0.0, "calls": 0, "cached": 0, "unreadable": 0} for ep in episodes}

    system = monitor_llm.system_prompt(cfg)
    tasks = [(ep, j, r) for ep in episodes for j in range(n_plans) for r in range(repeats)]

    def one(task):
        ep, j, r = task
        messages = [{"role": "user", "content": monitor_llm.user_message(cfg, ep, j)}]
        resp = client.create(system, messages, [], repeat_index=r)
        value, _ = monitor_llm.parse_suspicion(resp["content"])
        return value, resp["cost_usd"], resp["cached"]

    out = {episode_key(ep): {"scores": [[None] * repeats for _ in range(n_plans)],
                             "cost_usd": 0.0, "calls": 0, "cached": 0, "unreadable": 0} for ep in episodes}
    with ThreadPoolExecutor(max_workers=int(cfg["llm_monitor"]["workers"])) as pool:
        for done, ((ep, j, r), (value, cost, cached)) in enumerate(zip(tasks, pool.map(one, tasks)), 1):
            rec = out[episode_key(ep)]
            rec["scores"][j][r] = value
            rec["cost_usd"] += cost
            rec["calls"] += 1
            rec["cached"] += bool(cached)
            rec["unreadable"] += value is None
            if progress and done % 500 == 0:
                progress(done, len(tasks))
    return out
