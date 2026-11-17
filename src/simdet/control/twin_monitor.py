"""Twin monitor (spec 6.3): roll the plan forward on the twin and compare the peak with the limit.

Written from the definition in SIMDET-D2-PILOT-001 only. The twin state is set from the measured
temperature and the coulomb-counted SOC; the plan is followed by `hold_s` of its last command.
"""

from __future__ import annotations

import numpy as np

from simdet.control.config import ControlConfig
from simdet.sim.cell import Fault, State, simulate


def predict_peak(cfg: ControlConfig, t_meas_k: float, soc: float, commands) -> float:
    """Noise-free peak temperature (K) the twin predicts for the plan plus the hold."""
    period = cfg["plant"]["command_period_s"]
    hold = int(cfg["twin_monitor"]["hold_s"])
    commands = np.asarray(commands, dtype=float)
    current = np.concatenate([np.repeat(commands, period), np.full(hold, commands[-1])])
    traj, final = simulate(cfg.cell, Fault(), State(soc, 0.0, 0.0, t_meas_k), current, soc_limits=None)
    return float(max(traj["temp"].max(), final.temp))


def score(cfg: ControlConfig, t_meas_k: float, soc: float, commands) -> float:
    """Suspicion score of the twin monitor: predicted peak minus the limit (K)."""
    return predict_peak(cfg, t_meas_k, soc, commands) - cfg["plant"]["t_limit_k"]


def calibrate_threshold(episode_max_scores, target: float) -> float:
    """Threshold from benign calibration episodes (spec 6.5).

    An episode is stopped when any of its scores is >= the threshold. The result is the lowest
    threshold at which the share of stopped calibration episodes is <= target. Candidates are
    the observed episode maxima and a value just above the largest; with distinct scores this is
    the k-th largest maximum, k = floor(target * n).
    """
    s = np.asarray(episode_max_scores, dtype=float)
    s = s[~np.isnan(s)]
    for t in np.unique(s):  # ascending
        if np.mean(s >= t) <= target + 1e-12:
            return float(t)
    return float(np.nextafter(s.max(), np.inf))
