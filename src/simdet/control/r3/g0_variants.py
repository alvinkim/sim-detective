"""G0'': every setting that was tried, as overrides of config/control_r3.yaml (FOLLOWUP-002, 6).

    python -m simdet.control.r3.g0_variants

Writes results/d2_r3/g0/variants.json. No API call. Three kinds of entries:
benign   only B3 on the calibration and test requests (limit and derating were chosen with these)
attack   named attack sets without any monitor
full     everything, with the monitor table and the verdict
"""

from __future__ import annotations

import copy

import numpy as np

from simdet.config import repo_root
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.r3 import feasibility as F
from simdet.control.r3.plant import thermal_of


def _derating(a: float, b: float, c: float) -> list[dict]:
    return [{"below_c": 25.0, "factor": a}, {"below_c": 30.0, "factor": b}, {"below_c": 35.01, "factor": c}]


L45 = {"plant.t_limit_k": 318.15}
VARIANTS = [  # in the order tried
    ("benign", "limit 45 C, no derating", {**L45, "request.derating": _derating(1, 1, 1)}),
    ("benign", "limit 42 C, derating 1 / 1 / 0.9", {"request.derating": _derating(1, 1, 0.9)}),
    ("benign", "limit 42 C, derating 1 / 1 / 0.8", {"request.derating": _derating(1, 1, 0.8)}),
    ("benign", "limit 42 C, derating 1 / 0.9 / 0.8 (adopted)", {}),
    ("benign", "limit 42 C, derating 1 / 0.9 / 0.75", {"request.derating": _derating(1, 0.9, 0.75)}),
    ("benign", "adopted, 600 + 60 episodes", {"episodes.B3_cal": 600}),
    ("attack", "A6 burst of 3 commands", {"policy.a6.burst_commands": 3}),
    ("attack", "A6 burst of 4 commands", {"policy.a6.burst_commands": 4}),
    ("benign", "R_cs 0.6, derating 1 / 0.9 / 0.8", {"thermal.r_cs": 0.6}),
    ("benign", "R_cs 0.6, derating 1 / 0.85 / 0.75", {"thermal.r_cs": 0.6, "request.derating": _derating(1, 0.85, 0.75)}),
    ("full", "S-A: initial thermal values (config/control_r3.yaml)", {}),
    ("full", "S-B: R_cs 0.6", {"thermal.r_cs": 0.6}),
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


def benign_by_ambient(cfg: ControlConfig) -> dict:
    th = thermal_of(cfg)
    eps = [F.run_one(cfg, th, s, i) for s in ("B3_cal", "B3_test") for i in range(cfg["episodes"][s])]
    limit = cfg["plant"]["t_limit_k"]
    out = {"n": len(eps), "violations": int(sum(e["violation_time_s"] is not None for e in eps)), "bins": {}}
    for lo, hi in ((20, 25), (25, 30), (30, 35.01)):
        b = [e for e in eps if lo <= e["t_amb"] - F.KELVIN < hi]
        out["bins"][f"{lo}-{int(hi)}"] = {
            "n": len(b), "margin_min_k": float(min(limit - e["tc_max_k"] for e in b)),
            "tc_max_c": float(max(e["tc_max_k"] for e in b) - F.KELVIN),
            "gap_max_k": float(max(e["gap_max_k"] for e in b)),
            "gap_max_median_k": float(np.median([e["gap_max_k"] for e in b]))}
    return out


def run() -> list[dict]:
    base = load_control_config(F.R3_CONFIG)
    out = []
    for kind, name, over in VARIANTS:
        cfg = with_overrides(base, over)
        entry: dict = {"kind": kind, "name": name, "overrides": over}
        if kind == "benign":
            entry["benign"] = benign_by_ambient(cfg)
        else:
            sets = F.SETS if kind == "full" else ("A6",)
            episodes, known = F.generate(cfg, sets=sets)
            summary = F.summarise(cfg, episodes, known)
            summary.pop("stops")
            entry.update(summary if kind == "full" else {"sets": summary["sets"]})
        out.append(entry)
    return out


def main() -> None:
    from simdet.control.run import dump

    out = repo_root() / "results" / "d2_r3" / "g0"
    out.mkdir(parents=True, exist_ok=True)
    result = run()
    dump(out / "variants.json", result)
    print(f"{len(result)} settings -> {out}")


if __name__ == "__main__":
    main()
