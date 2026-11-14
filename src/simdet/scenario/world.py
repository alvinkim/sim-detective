"""The hidden side of a scenario: true system + twin, a baseline segment, a current
segment, and experiments appended to the current segment.

Everything is a deterministic function of (config, cause, magnitude, regime, seed and
the list of experiments), so a scenario can be re-run from its private file.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simdet.sim.cell import Fault, State, initial_state, measure, simulate
from simdet.sim.profiles import experiment_profile, regime_profile, validate_experiment
from simdet.sim.twin import TwinState, twin_initial, twin_predict


class ExperimentRejected(ValueError):
    """The request was refused. The message is safe to show to the agent."""


@dataclass
class Segment:
    """One continuous run starting at t = 0 from rest. Arrays cover the whole run;
    only samples at index >= visible_from may be shown to the agent."""

    current: np.ndarray
    v_meas: np.ndarray
    t_meas: np.ndarray
    v_pred: np.ndarray
    visible_from: int
    true_state: State
    twin_state: TwinState

    @property
    def n(self) -> int:
        return self.current.size

    @property
    def resid(self) -> np.ndarray:
        return self.v_meas - self.v_pred


class World:
    def __init__(self, cfg, fault: Fault, regime: str, seed: int):
        self.cfg = cfg
        self.p = cfg.cell
        self.fault = fault
        self.regime = regime
        self.seed = int(seed)
        self.experiments: list[dict] = []
        sim = cfg["sim"]
        self._limits = (float(sim["soc_min"]), float(sim["soc_max"]))
        self._soc_init = float(sim["soc_init"])
        current, visible_from = regime_profile(cfg, regime)
        self.baseline = self._start(Fault(), current, visible_from, self._rng(0))
        self.current = self._start(fault, current, visible_from, self._rng(1))

    def _rng(self, stream: int) -> np.random.Generator:
        return np.random.default_rng([self.seed, stream])

    def _start(self, fault: Fault, current, visible_from: int, rng) -> Segment:
        seg = Segment(
            current=np.empty(0), v_meas=np.empty(0), t_meas=np.empty(0), v_pred=np.empty(0),
            visible_from=visible_from,
            true_state=initial_state(self.p, fault, self._soc_init),
            twin_state=twin_initial(self._soc_init),
        )
        self._extend(seg, fault, current, rng)
        return seg

    def _extend(self, seg: Segment, fault: Fault, current: np.ndarray, rng) -> None:
        traj, seg.true_state = simulate(self.p, fault, seg.true_state, current, self._limits)
        v_meas, t_meas = measure(self.p, fault, traj, rng)
        v_pred, seg.twin_state = twin_predict(self.p, seg.twin_state, current, t_meas)
        seg.current = np.concatenate([seg.current, current])
        seg.v_meas = np.concatenate([seg.v_meas, v_meas])
        seg.t_meas = np.concatenate([seg.t_meas, t_meas])
        seg.v_pred = np.concatenate([seg.v_pred, v_pred])

    def run_experiment(self, name, args) -> tuple[int, int]:
        """Continue the true system from its present state. Returns the index range of
        the new samples in the current segment. Raises ExperimentRejected otherwise.

        The SOC guard uses the twin's coulomb-counted SOC with a margin, so whether a
        request is refused does not depend on the hidden state.
        """
        try:
            clean = validate_experiment(self.cfg, name, args)
        except ValueError as e:
            raise ExperimentRejected(str(e)) from None
        profile = experiment_profile(self.cfg, name, clean)
        margin = float(self.cfg["experiments"]["soc_margin"])
        soc_after = self.current.twin_state.soc - profile.sum() / (3600.0 * self.p.q_ah)
        floor = self._limits[0] + margin
        if soc_after < floor:
            raise ExperimentRejected(
                f"refused: coulomb-counted SOC would fall to {soc_after:.3f}, below the "
                f"allowed minimum {floor:.2f} (currently {self.current.twin_state.soc:.3f})."
            )
        start = self.current.n
        self._extend(self.current, self.fault, profile, self._rng(2 + len(self.experiments)))
        self.experiments.append({"name": name, "args": clean})
        return start, self.current.n

    def clone(self) -> "World":
        """Fresh copy with the same experiments replayed (same noise)."""
        other = World(self.cfg, self.fault, self.regime, self.seed)
        for e in self.experiments:
            other.run_experiment(e["name"], e["args"])
        return other


def world_from_private(cfg, private: dict) -> World:
    """Rebuild the world of a stored scenario and check it reproduces the stored state."""
    world = World(cfg, Fault(**private["fault"]), private["regime"], private["seed"])
    stored = private["true_state"]
    now = world.current.true_state
    for key in ("soc", "v1", "v2", "temp"):
        if abs(stored[key] - getattr(now, key)) > 1e-9:
            raise RuntimeError(
                f"scenario {private['id']} does not reproduce (state '{key}' differs). "
                "The config changed since generation; run `simdet gen` again."
            )
    return world
