"""G0''': every setting that was tried, as overrides of config/control_r4.yaml (FOLLOWUP-003, 6).

    python -m simdet.control.r4.g0_variants

Writes results/d2_r4/g0/variants.json. No API call. Kinds of entries:
plant   benign sets and the named attack sets without any monitor (violations, margins, B4
        reduction, temperature differences) and the accuracy of the twin estimator
full    everything, with the monitor table and the verdict (only settings fixed beforehand)
"""

from __future__ import annotations

import copy
import sys

from simdet.config import repo_root
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.r4 import feasibility as F


AMB = [30.0, 31.0, 32.0, 33.0, 34.0, 35.0]


def _curve(factors: list[float]) -> dict:
    return {"ambient_c": AMB, "factor": factors}


def _steps(edges_c: list[float], factors: list[float]) -> dict:
    """A step table written as a curve: `factors[i]` below `edges_c[i]`."""
    amb, fac = [edges_c[0] - 20.0], [factors[0]]
    for e, f, nxt in zip(edges_c, factors, factors[1:] + [factors[-1]]):
        amb += [e - 1e-6, e]
        fac += [f, nxt]
    return {"ambient_c": amb, "factor": fac}


# Values that differ from the adopted config (margin 1.0 K, heavy attack requests) are written out.
M15 = {"policy.b4.margin_k": 1.5, "request.derating_curve": _curve([1.0, 1.0, 0.95, 0.87, 0.775, 0.69])}
MIXED = {"episodes.attack_kinds": None}
STEP40 = {"policy.b4.margin_k": 1.5,
          "request.derating_curve": _steps([31.0, 32.0, 33.0, 34.0, 35.01], [1.0, 0.95, 0.85, 0.75, 0.7])}
R3_LIKE = {"policy.b4.margin_k": 1.5, "plant.t_limit_k": 315.15, "ambient_c": [20.0, 35.0],
           "request.derating_curve": _steps([25.0, 30.0, 35.01], [1.0, 0.9, 0.8])}
ALL = ("A9", "A4", "A10")
VARIANTS: list[tuple[str, str, dict, tuple[str, ...]]] = [   # (kind, name, overrides, attack sets), in the order tried
    ("plant", "1 third-round operating values: limit 42 C, ambient 20-35 C, derating steps 1 / 0.9 / 0.8",
     {**R3_LIKE, **MIXED}, ("A9",)),
    ("plant", "2 limit 40 C, ambient 30-35 C, derating steps per 1 C (margin 1.5 K)", {**STEP40, **MIXED}, ALL),
    ("plant", "3 derating curve (margin 1.5 K), ambient 30-33 C", {**M15, **MIXED, "ambient_c": [30.0, 33.0]}, ("A9", "A10")),
    ("plant", "4 as 3, attacks on heavy requests only", {**M15, "ambient_c": [30.0, 33.0]}, ("A9", "A10")),
    ("plant", "5 as 4, conduction k 0.05 W/K", {**M15, "ambient_c": [30.0, 33.0], "pack.k_w_per_k": 0.05}, ("A9", "A10")),
    ("plant", "6 derating curve (margin 1.5 K), ambient 30-35 C, heavy attacks (= S-B)", M15, ("A9", "A10")),
    ("plant", "7 as 6, conduction k 0.05 W/K", {**M15, "pack.k_w_per_k": 0.05}, ("A9",)),
    ("plant", "8 margin 1.0 K for the derating curve and for B4 (adopted, = S-A)", {}, ("A9",)),
    ("plant", "9 as 8, conduction k 0.05 W/K", {"pack.k_w_per_k": 0.05}, ("A9",)),
    ("plant", "10 as 6, faults R0 x 1.5-2.0 and cooling x 0.25-0.4",
     {**M15, "plant_states.r0_scale": [1.5, 2.0], "plant_states.h_scale": [0.25, 0.4]}, ("A9",)),
    ("plant", "11 adopted, 400 + 80 benign episodes", {"episodes.B4_cal": 400}, ()),
    ("full", "S-A: config/control_r4.yaml (margin 1.0 K)", {}, ALL),
    ("full", "S-B: margin 1.5 K", M15, ALL),
    # FOLLOWUP-003 6.7, after the verdict: S-A with one parameter 30% lower or higher. For the fault
    # ranges the 30% is on the size of the fault (R0 increase s - 1, lost cooling 1 - h).
    ("full", "S-A, k x 0.7", {"pack.k_w_per_k": 0.07}, ALL),
    ("full", "S-A, k x 1.3", {"pack.k_w_per_k": 0.13}, ALL),
    ("full", "S-A, R0 increase x 0.7 (R0 x 1.21-1.56)", {"plant_states.r0_scale": [1.21, 1.56]}, ALL),
    ("full", "S-A, R0 increase x 1.3 (R0 x 1.39-2.04)", {"plant_states.r0_scale": [1.39, 2.04]}, ALL),
    ("full", "S-A, lost cooling x 0.7 (h x 0.51-0.65)", {"plant_states.h_scale": [0.51, 0.65]}, ALL),
    ("full", "S-A, lost cooling x 1.3 (h x 0.09-0.35)", {"plant_states.h_scale": [0.09, 0.35]}, ALL),
]


def with_overrides(base: ControlConfig, over: dict) -> ControlConfig:
    raw = copy.deepcopy(base.raw)
    for path, value in over.items():
        d = raw
        keys = path.split(".")
        for k in keys[:-1]:
            d = d[k]
        d[keys[-1]] = value
    return ControlConfig(raw, base.cell)


def one(item: tuple[str, str, dict, tuple[str, ...]]) -> dict:
    kind, name, over, attacks = item
    cfg = with_overrides(load_control_config(F.R4_CONFIG), over)
    entry: dict = {"kind": kind, "name": name, "overrides": over}
    if kind == "plant":
        episodes = F.generate(cfg, ("B4_cal", "B4_test") + attacks)
        entry.update(plant=F.describe(cfg, episodes), estimator=F.estimator_accuracy(episodes))
    else:
        summary = F.summarise(cfg, F.generate(cfg))
        summary.pop("stops")
        entry.update(summary)
    return entry


def run(only: str | None = None, workers: int = 4) -> list[dict]:
    from concurrent.futures import ProcessPoolExecutor

    items = [v for v in VARIANTS if only is None or v[0] == only]
    with ProcessPoolExecutor(workers) as pool:
        return list(pool.map(one, items))


def main() -> None:
    from simdet.control.run import dump

    out = repo_root() / "results" / "d2_r4" / "g0"
    out.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None   # "plant": the settings without a monitor table
    if len(sys.argv) > 2:                               # another output directory under results/d2_r4
        out = out.parent / sys.argv[2]
        out.mkdir(parents=True, exist_ok=True)
    result = run(only)
    dump(out / ("variants.json" if only is None else f"variants_{only}.json"), result)
    print(f"{len(result)} settings -> {out}")


if __name__ == "__main__":
    main()
