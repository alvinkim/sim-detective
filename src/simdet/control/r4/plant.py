"""Episode runner of the pack: check pulse, then the policy drives the pack plan by plan.

Time zero of an episode is the first checkpoint (after the check pulse and its rest).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simdet.control.config import ControlConfig
from simdet.control.r4 import pack as pk
from simdet.control.r4.estimator import Twin
from simdet.control.r4.policies import Policy4
from simdet.control.r4.rule9 import VoltTemp
from simdet.control.signals import soc_step


def nominal_pack(cfg: ControlConfig) -> pk.Pack:
    return pk.Pack.healthy(cfg.cell, int(cfg["pack"]["n_cells"]), float(cfg["pack"]["k_w_per_k"]))


def pulse_current(cfg: ControlConfig) -> np.ndarray:
    cp = cfg["pack"]["check_pulse"]
    return np.concatenate([np.full(int(cp["on_s"]), float(cp["current_a"])), np.zeros(int(cp["rest_s"]))])


@dataclass(frozen=True)
class MonitorModel:
    """What a model-based monitor (twin, R9) believes and reads: its model of the healthy pack and
    a bias on every cell voltage reading it gets."""
    name: str
    nominal: pk.Pack
    v_bias: float = 0.0


def run_episode(cfg: ControlConfig, true_pack: pk.Pack, nominal: pk.Pack, policy: Policy4, targets: np.ndarray,
                t_amb: float, noise_rng: np.random.Generator, models: list[MonitorModel] | None = None) -> dict:
    """`models`: extra monitor models (model-error conditions). The plant, the policy and the noise
    do not depend on them; their scores are returned under "model_scores"."""
    plant, p = cfg["plant"], cfg.cell
    n_plan, period = plant["plan_len"], plant["command_period_s"]
    sens = np.array(cfg["pack"]["sensor_cells"]) - 1
    i_min = float(cfg["rules"]["r6_min_current_a"])
    temps = np.full(true_pack.n, float(t_amb))
    soc, v1 = float(plant["soc_init"]), 0.0
    twin = Twin(cfg, nominal, t_amb)
    r9 = VoltTemp(cfg, p, true_pack.n, t_amb)
    extra = [(m, Twin(cfg, m.nominal, t_amb), VoltTemp(cfg, m.nominal.cell, true_pack.n, t_amb)) for m in models or []]
    state = {"reading": float("nan"), "r6": 0.0}

    def execute(current: np.ndarray) -> np.ndarray:
        """Run the pack, give the readings to the twin, update what the rules see. Returns the
        true temperatures of the segment."""
        nonlocal temps, soc, v1
        traj, temps = pk.simulate(true_pack, temps, t_amb, current)
        s, v, soc_end, v1_end = pk.electrical(true_pack, soc, v1, current)
        v_meas = pk.voltages(true_pack, s, v, traj, current) + noise_rng.normal(0.0, p.sigma_v, traj.shape)
        t_meas = traj[:, sens] + noise_rng.normal(0.0, p.sigma_t, (current.size, sens.size))
        first = "fitted" not in state   # the first segment is the check pulse
        state["fitted"] = True
        for tw, rule, seen in [(twin, r9, v_meas)] + [(t, r, v_meas + m.v_bias) for m, t, r in extra]:
            if first:
                tw.fit_r0(current, seen, s, v)
                rule.fit_r0(current, seen, s, v)
            else:
                rule.advance(current, seen, s, v)
            tw.advance(current, seen, t_meas, s, v)
        soc, v1 = soc_end, v1_end
        active = np.abs(current) >= i_min
        dev = np.abs(v_meas - v_meas.mean(axis=1, keepdims=True)).max(axis=1)
        state["r6"] = float(dev[active].max()) if active.any() else 0.0
        state["reading"] = float(t_meas[-1].max())
        return traj

    execute(pulse_current(cfg))
    soc_seen = soc   # coulomb-counted SOC the policy plans with

    commands, scores, readings, r6, est, true, c_hat, tr, r9_est = [], [], [], [], [], [], [], [], []
    model_scores = {m.name: {"M2": [], "R9": []} for m in models or []}
    n_clip = n_guard = 0
    for j in range(plant["plans_per_episode"]):
        plan = policy.plan(j, float(targets[j]), soc_seen, temps.copy(), t_amb)
        scores.append(twin.score(plan.commands))
        r9_est.append(r9.temp.copy())
        for m, tw, rule in extra:
            model_scores[m.name]["M2"].append(tw.score(plan.commands))
            model_scores[m.name]["R9"].append(rule.score(plant["t_limit_k"]))
        readings.append(state["reading"])
        r6.append(state["r6"])
        est.append(twin.temp.copy())
        true.append(temps.copy())
        c_hat.append(twin.c.copy())
        tr.append(execute(np.repeat(plan.commands, period)))
        commands.append(plan.commands)
        n_clip += plan.n_actuator_clipped
        n_guard += plan.n_guard_limited
        for c in plan.commands:
            soc_seen += soc_step(cfg, float(c))
    traj = np.vstack(tr + [temps[None, :]])
    hottest = traj.max(axis=1)
    over = np.flatnonzero(hottest > plant["t_limit_k"])
    est, true = np.array(est), np.array(true)
    return {
        "request": np.repeat(targets, n_plan), "targets": targets, "commands": np.concatenate(commands),
        "twin_scores": np.array(scores), "t_checkpoint": np.array(readings), "r6_v": np.array(r6),
        "s_hat": twin.s.copy(), "c_hat": np.array(c_hat), "t_est": est, "t_true": true,
        "r9_est": np.array(r9_est), "r9_s": r9.s.copy(),
        "model_scores": {k: {a: np.array(b) for a, b in v.items()} for k, v in model_scores.items()},
        "scales": np.array(policy.scales),
        "temp_minute": traj[::period], "t_max_k": float(hottest.max()),
        "sensor_max_k": float(traj[:, sens].max()),
        "hot_cell": int(traj.max(axis=0).argmax()),
        "violation_time_s": int(over[0]) if over.size else None,
        "attack_start_plan": policy.start_plan, "t_amb": t_amb,
        "n_actuator_clipped": n_clip, "n_guard_limited": n_guard, "soc_end": soc_seen,
    }
