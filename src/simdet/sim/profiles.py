"""Current profiles: the two regimes (spec 5.6) and the experiment menu (spec 6.3)."""

from __future__ import annotations

from typing import Any

import numpy as np

REGIMES = ("CC", "DYN")
EXPERIMENT_NAMES = ("pulse_test", "rest_test", "cc_run")


def regime_profile(cfg, regime: str) -> tuple[np.ndarray, int]:
    """Return (current per second, index of the first sample shown to the agent)."""
    spec = cfg["regimes"][regime]
    if regime == "CC":
        n = int(spec["pre_s"]) + int(spec["observe_s"])
        return np.full(n, float(spec["current_a"])), int(spec["pre_s"])
    if regime == "DYN":
        parts = [np.full(int(dur), float(amp)) for amp, dur in spec["steps"]]
        return np.concatenate(parts), 0
    raise ValueError(f"unknown regime: {regime}")


def validate_experiment(cfg, name: Any, args: Any) -> dict[str, float]:
    """Check an experiment request against the menu. Raises ValueError with a message
    that is safe to show to the agent."""
    menu = cfg["experiments"]["menu"]
    if name not in menu:
        raise ValueError(f"unknown experiment '{name}'. Choose one of: {', '.join(menu)}.")
    if not isinstance(args, dict):
        raise ValueError("args must be an object.")
    spec = menu[name]
    unknown = sorted(set(args) - set(spec))
    if unknown:
        raise ValueError(f"unexpected argument(s) for {name}: {', '.join(unknown)}.")
    clean: dict[str, float] = {}
    for key, (lo, hi) in spec.items():
        value = args.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} needs a numeric '{key}' in [{lo}, {hi}].")
        if not (lo <= value <= hi):
            raise ValueError(f"{name}.{key}={value} is outside [{lo}, {hi}].")
        clean[key] = float(value)
    return clean


def experiment_profile(cfg, name: str, args: dict[str, float]) -> np.ndarray:
    """Current per second for a validated experiment request."""
    exp = cfg["experiments"]
    if name == "pulse_test":
        return np.concatenate(
            [
                np.zeros(int(exp["pulse_pre_rest_s"])),
                np.full(int(round(args["duration_s"])), args["amplitude_a"]),
                np.zeros(int(exp["pulse_post_rest_s"])),
            ]
        )
    if name == "rest_test":
        return np.zeros(int(round(args["duration_s"])))
    if name == "cc_run":
        return np.full(int(round(args["duration_s"])), args["current_a"])
    raise ValueError(f"unknown experiment: {name}")


def experiment_duration_s(cfg, name: str, args: dict[str, float]) -> int:
    """Total length of an experiment, including the rests of a pulse test."""
    return int(experiment_profile(cfg, name, args).size)


def constant_blocks(current: np.ndarray, start: int = 0, end: int | None = None) -> list[tuple[int, int]]:
    """Half-open index ranges [a, b) of constant current inside [start, end)."""
    end = current.size if end is None else end
    if end <= start:
        return []
    change = np.flatnonzero(np.diff(current[start:end]) != 0) + start + 1
    edges = [start, *change.tolist(), end]
    return list(zip(edges[:-1], edges[1:]))
