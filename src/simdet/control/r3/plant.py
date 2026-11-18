"""Episode runner of the third plant: the policy drives the two-node cell plan by plan."""

from __future__ import annotations

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.r3 import thermal
from simdet.control.r3.policies import Context, Policy3, twin_score
from simdet.control.signals import soc_step


def thermal_of(cfg: ControlConfig, **scale: float) -> thermal.Thermal:
    """Thermal parameters of the config; `scale` multiplies named ones (sensitivity checks)."""
    t = dict(cfg["thermal"])
    t["h"] = cfg.cell.h_th if t["h"] is None else t["h"]
    for k, f in scale.items():
        t[k] *= f
    return thermal.Thermal.from_cell(cfg.cell, t["c_c"], t["c_s"], t["r_cs"], t["h"])


def start_state(th: thermal.Thermal, t_amb: float, prior_current_a: float, prior_duration_s: float) -> tuple[float, float]:
    """(T_c, T_s) after the earlier operation; ambient equilibrium when there was none."""
    if prior_duration_s <= 0:
        return t_amb, t_amb
    _, _, t_c, t_s = thermal.simulate(th, t_amb, t_amb, t_amb, np.full(int(prior_duration_s), prior_current_a))
    return t_c, t_s


def run_episode(cfg: ControlConfig, plant_th: thermal.Thermal, twin_th: thermal.Thermal, policy: Policy3,
                targets: np.ndarray, t_amb: float, start: tuple[float, float], noise_rng: np.random.Generator) -> dict:
    plant = cfg["plant"]
    n, period = plant["plan_len"], plant["command_period_s"]
    sigma = cfg.cell.sigma_t
    tw = cfg["twin_monitor"]
    t_c, t_s = start
    soc = plant["soc_init"]
    reading = t_s + noise_rng.normal(0.0, sigma)
    obs = thermal.Observer(twin_th, t_amb, reading, tw["observer_l_s"], tw["observer_l_c"])

    commands, scores, readings, est, tc_all, ts_all = [], [], [], [], [], []
    n_clip = n_guard = 0
    for j in range(plant["plans_per_episode"]):
        ctx = Context(j, float(targets[j]), float(targets[j - 1]) if j else None, soc, t_amb, reading, obs.t_c, obs.t_s)
        plan = policy.plan(ctx)
        scores.append(twin_score(cfg, twin_th, obs.t_c, obs.t_s, t_amb, plan.commands))
        readings.append(reading)
        est.append((obs.t_c, t_c))
        current = np.repeat(plan.commands, period)
        tc, ts, t_c, t_s = thermal.simulate(plant_th, t_c, t_s, t_amb, current)
        meas = np.append(ts[1:], t_s) + noise_rng.normal(0.0, sigma, current.size)  # reading after each second
        obs.advance(current, meas)
        reading = float(meas[-1])
        commands.append(plan.commands)
        tc_all.append(tc)
        ts_all.append(ts)
        n_clip += plan.n_actuator_clipped
        n_guard += plan.n_guard_limited
        for c in plan.commands:
            soc += soc_step(cfg, float(c))
    tc_all, ts_all = np.append(np.concatenate(tc_all), t_c), np.append(np.concatenate(ts_all), t_s)
    over = np.flatnonzero(tc_all > plant["t_limit_k"])
    est = np.array(est)
    return {
        "request": np.repeat(targets, n), "targets": targets, "commands": np.concatenate(commands),
        "twin_scores": np.array(scores), "t_checkpoint": np.array(readings),
        "est_error_k": est[:, 0] - est[:, 1],               # observer T_c minus true T_c at each checkpoint
        "tc_minute": tc_all[::period], "ts_minute": ts_all[::period],
        "tc_max_k": float(tc_all.max()), "ts_max_k": float(ts_all.max()),
        "gap_max_k": float((tc_all - ts_all).max()),
        "gap_at_tc_max_k": float((tc_all - ts_all)[int(tc_all.argmax())]),
        "violation_time_s": int(over[0]) if over.size else None,
        "attack_start_plan": policy.start_plan, "t_amb": t_amb, "start": start,
        "n_actuator_clipped": n_clip, "n_guard_limited": n_guard, "soc_end": soc,
    }
