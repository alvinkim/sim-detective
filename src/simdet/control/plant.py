"""Episode runner: a policy drives the plant plan by plan (spec 3, 5).

The plant is `simdet.sim.cell.simulate` with the plant parameters of the twin condition. Without
a monitor the episode always runs to the end; `stop_at` (plan index) ends it before that plan.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simdet.control import twin_monitor
from simdet.control.config import ControlConfig
from simdet.control.policies import Policy
from simdet.sim.cell import CellParams, Fault, State, measure, simulate


@dataclass
class Episode:
    request: np.ndarray            # per command
    commands: np.ndarray           # per command (executed plans only)
    explanations: list[str]
    temp: np.ndarray               # true temperature, 1 s samples, plus the final state
    t_meas: np.ndarray             # measured temperature, 1 s samples
    v_meas: np.ndarray
    soc: np.ndarray                # true SOC at the start of each command, plus the final value
    twin_scores: np.ndarray        # twin monitor score at each checkpoint
    attack_start_plan: int
    n_actuator_clipped: int
    n_guard_limited: int

    def violation_time_s(self, t_limit_k: float) -> int | None:
        over = np.flatnonzero(self.temp > t_limit_k)
        return int(over[0]) if over.size else None


def run_episode(cfg: ControlConfig, plant_cell: CellParams, policy: Policy, request: np.ndarray,
                noise_rng: np.random.Generator, stop_at: int | None = None) -> Episode:
    plant = cfg["plant"]
    n_cmd, period = plant["plan_len"], plant["command_period_s"]
    fault = Fault()
    state = State(plant["soc_init"], 0.0, 0.0, plant_cell.t_amb)
    t_meas_now = state.temp + noise_rng.normal(0.0, plant_cell.sigma_t)  # reading at the first checkpoint
    soc_cc = plant["soc_init"]  # coulomb counting; equal to the true SOC here (current is exact)

    commands, explanations, scores = [], [], []
    temp, t_meas, v_meas, soc = [], [], [], []
    n_clip = n_guard = 0
    for j in range(plant["plans_per_episode"]):
        if stop_at is not None and j >= stop_at:
            break
        req = request[j * n_cmd:(j + 1) * n_cmd]
        plan = policy.plan(j, req, t_meas_now, soc_cc)
        scores.append(twin_monitor.score(cfg, t_meas_now, soc_cc, plan.commands))
        traj, state = simulate(plant_cell, fault, state, np.repeat(plan.commands, period), soc_limits=None)
        v_m, t_m = measure(plant_cell, fault, traj, noise_rng)
        commands.append(plan.commands)
        explanations += plan.explanations
        temp.append(traj["temp"])
        t_meas.append(t_m)
        v_meas.append(v_m)
        soc.append(traj["soc"][::period])
        n_clip += plan.n_actuator_clipped
        n_guard += plan.n_guard_limited
        soc_cc = state.soc
        t_meas_now = state.temp + noise_rng.normal(0.0, plant_cell.sigma_t)
    return Episode(
        request=request, commands=np.concatenate(commands), explanations=explanations,
        temp=np.append(np.concatenate(temp), state.temp), t_meas=np.concatenate(t_meas),
        v_meas=np.concatenate(v_meas), soc=np.append(np.concatenate(soc), state.soc),
        twin_scores=np.array(scores), attack_start_plan=policy.start_plan,
        n_actuator_clipped=n_clip, n_guard_limited=n_guard,
    )
