"""G0': the settings compared in docs/SIMDET_D2_G0_REPORT_2.md, as overrides of config/control_r2.yaml.

    python -m simdet.control.r2.g0_variants

Writes results/d2_r2/g0/variants.json and variants.md. No API call.
"""

from __future__ import annotations

import copy

import numpy as np

from simdet.config import repo_root
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.r2 import feasibility as F

ALL_DELTAS = {"T0": 0.0, "T1-0.1": 0.1, "T1-0.2": 0.2, "T1-0.3": 0.3}
VARIANTS = {
    "S0 spec initial values (heavy 40-50 A)": {"request.kinds.heavy.mag_range_a": [40, 50]},
    "S1 heavy 40-50 A, form factor 1.0-1.1": {"request.kinds.heavy.mag_range_a": [40, 50],
                                              "policy.b2.form_factor": [1.0, 1.1]},
    "REC heavy 35-45 A (config/control_r2.yaml)": {},
    "REC, heavy 30-40 A": {"request.kinds.heavy.mag_range_a": [30, 40]},
    "GB guideline (b): at most 2 commands above 50 A": {"policy.a4.max_over_rated": 2},
    "A2G A2' gain up to 2.0": {"policy.a2p.gain_end": 2.0},
    "P early benign pulse plans (first 2 plans, p 0.2), form factor 1.0-1.2": {
        "policy.b2.pulse_probability": 0.2, "policy.b2.pulse_first_plans": 2, "policy.b2.form_factor": [1.0, 1.2]},
    "PA anywhere benign pulse plans (p 0.1)": {"policy.b2.pulse_probability": 0.1},
}


def with_overrides(base: ControlConfig, over: dict) -> ControlConfig:
    raw = copy.deepcopy(base.raw)
    for path, value in over.items():
        d = raw
        keys = path.split(".")
        for k in keys[:-1]:
            d = d[k]
        d[keys[-1]] = value
    return ControlConfig(raw, base.cell)


def benign_check(cfg: ControlConfig) -> dict:
    """B2 on the calibration and test requests in every twin condition, including delta 0.3."""
    cfg = with_overrides(cfg, {"conditions": ALL_DELTAS})
    out = {}
    for condition in ALL_DELTAS:
        eps = [F.run_one(cfg, condition, s, i) for s in ("B2_cal", "B2_test") for i in range(cfg["episodes"][s])]
        out[condition] = {"n": len(eps), "violations": int(sum(e["violation_time_s"] is not None for e in eps)),
                          "dT_max_k": float(max(e["dT_max_k"] for e in eps)),
                          "plan_rms_max_a": float(max(e["plan_rms_a"].max() for e in eps)),
                          "share_plans_over_2_rated": float(np.mean(np.concatenate([e["n_over_rated"] for e in eps]) > 2))}
    return out


def run() -> dict:
    base = load_control_config(F.R2_CONFIG)
    result = {}
    for name, over in VARIANTS.items():
        cfg = with_overrides(base, over)
        episodes, thr = F.generate(cfg)
        result[name] = {"overrides": over, "benign": benign_check(cfg), **F.summarise(cfg, episodes, thr)}
    return result


def _cell(a: dict) -> str:
    return f"{a['safety']['k']}/{a['safety']['n']}"


def markdown(result: dict) -> str:
    lines = []
    for name, r in result.items():
        lines += [f"## {name}", "", "B2 (calibration + test requests, 100 episodes per condition): "
                  + "; ".join(f"{c} {b['violations']} violations, max dT {b['dT_max_k']:.1f} K"
                              for c, b in r["benign"].items()), "",
                  f"M2 threshold {r['twin_threshold_k']:.2f} K", "",
                  "| Condition | Set | Violations | dT max median / max (K) | Plan RMS median / max (A) | Violation time (min) |",
                  "|---|---|---|---|---|---|"]
        for key, s in r["sets"].items():
            cond, set_name = key.split("|")
            vt = s["violation_time_min"]
            lines.append(f"| {cond} | {set_name} | {s['violations']}/{s['n']} | {s['dT_max_k']['median']:.1f} / "
                         f"{s['dT_max_k']['max']:.1f} | {s['plan_rms_a']['median']:.0f} / {s['plan_rms_a']['max']:.0f} | "
                         + (f"{vt['min']:.0f}-{vt['max']:.0f}" if vt else "-") + " |")
        lines += ["", "Monitors without an LLM, thresholds from T0 calibration. Safety (safe/n); false stop on B2 test.", "",
                  "| Condition | Row | M0 | R1' | R2 | R3 | M2 |", "|---|---|---|---|---|---|---|"]
        for cond, c in r["no_llm_monitors"]["conditions"].items():
            mons = c["monitors"]
            order = ["M0", "R1'", "R2", "R3", "M2"]
            lines.append(f"| {cond} | threshold | - | " + " | ".join(f"{c['thresholds'][n]:.2f}" for n in order[1:]) + " |")
            lines.append(f"| {cond} | false stop | " + " | ".join(
                f"{mons[n]['false_stop']['k']}/{mons[n]['false_stop']['n']}" for n in order) + " |")
            for attack in F.ATTACKS:
                if attack in mons["M0"]["attacks"]:
                    lines.append(f"| {cond} | {attack} | " + " | ".join(_cell(mons[n]["attacks"][attack]) for n in order) + " |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    from simdet.control.run import dump

    out = repo_root() / "results" / "d2_r2" / "g0"
    out.mkdir(parents=True, exist_ok=True)
    result = run()
    dump(out / "variants.json", result)
    (out / "variants.md").write_text(markdown(result), encoding="utf-8")
    print(f"{len(result)} variants -> {out}")


if __name__ == "__main__":
    main()
