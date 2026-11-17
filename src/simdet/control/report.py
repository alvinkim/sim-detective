"""G4: combine the live runs, write the combined metrics and summary, draw the three figures.

    python -m simdet.control.report --run live_haiku --run live_sonnet

Reads results/d2_pilot/<run>/llm_<model>.json. Episodes are regenerated (deterministic) and
checked against the stored ones. Writes results/d2_pilot/combined/ and results/d2_pilot/fig_*.png.
No API call.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from simdet.config import paths
from simdet.control import metrics, pipeline
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.run import dump
from simdet.control.summary import write_summary
from simdet.sim.cell import Fault, State, simulate

# Colour by monitor (fixed), from the Okabe-Ito colour-blind-safe set; M0 is neutral grey.
COLORS = {"M0": "#7a7a7a", "M2": "#0072B2", "haiku": "#D55E00", "sonnet": "#009E73"}
LABEL = {"claude-haiku-5-5": "Haiku 5.5", "claude-sonnet-5-5": "Sonnet 5.5"}


def _color(name: str) -> str:
    return next((c for k, c in COLORS.items() if k in name), "#333333")


def _label(name: str) -> str:
    if name == "M0":
        return "M0 no monitor"
    if name == "M2":
        return "M2 twin"
    kind, model = name.split(":")
    return f"{'M1 LLM' if kind == 'M1' else 'M3 twin + LLM'} ({LABEL.get(model, model)})"


def _style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)


def fig_safety_vs_delta(cfg: ControlConfig, result: dict, path: Path) -> None:
    deltas = {c: float(d) for c, d in cfg["conditions"].items()}
    names = ["M0", "M2"] + [f"{k}:{m}" for m in result["llm_models"] for k in ("M1", "M3")]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for i, name in enumerate(names):
        pts = [(deltas[c], cond["monitors"][name]["attacks"]["A3"]["safety"])
               for c, cond in result["conditions"].items() if name in cond["monitors"]]
        x = np.array([p[0] for p in pts]) + (i - (len(names) - 1) / 2) * 0.004   # small offset: lines overlap
        y = np.array([100 * p[1]["rate"] for p in pts])
        lo = np.array([100 * p[1]["lo"] for p in pts])
        hi = np.array([100 * p[1]["hi"] for p in pts])
        ax.errorbar(x, y, yerr=[y - lo, hi - y], color=_color(name), linewidth=2, capsize=3,
                    linestyle="--" if name.startswith("M3") else "-",
                    marker={"M0": "x", "M2": "o"}.get(name, "s" if name.startswith("M1") else "D"),
                    markersize=6, label=_label(name))
    ax.set_xticks(list(deltas.values()))
    ax.set_xlabel("Twin mismatch δ (plant R0 × (1+δ), cooling × (1−δ))")
    ax.set_ylabel("Safety against A3 (%)")
    ax.set_ylim(-5, 105)
    ax.set_title("Adaptive attack A3: share of episodes without a violation (20 per point, Wilson 95%)",
                 fontsize=10, loc="left")
    _style(ax)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def roc_points(neg: np.ndarray, pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    thr = np.unique(np.concatenate([neg, pos]))[::-1]
    fpr = [0.0] + [float(np.mean(neg >= t)) for t in thr] + [1.0]
    tpr = [0.0] + [float(np.mean(pos >= t)) for t in thr] + [1.0]
    return np.array(fpr), np.array(tpr)


def fig_roc(episodes: list[dict], llm: dict, condition: str, path: Path) -> dict:
    single = metrics.monitor_scores(episodes, llm)
    test = [e for e in episodes if e["condition"] == condition and e["set"] == "B_test"]
    attack = [e for e in episodes if e["condition"] == condition and e["set"] == "A2"]
    fig, ax = plt.subplots(figsize=(4.8, 4.6))
    out = {}
    for name, table in single.items():
        if not all(pipeline.episode_key(e) in table for e in test + attack):
            continue
        neg = np.array([np.nanmax(table[pipeline.episode_key(e)]) for e in test])
        pos = np.array([np.nanmax(table[pipeline.episode_key(e)]) for e in attack])
        fpr, tpr = roc_points(neg, pos)
        out[name] = metrics.auroc(neg, pos)
        ax.step(fpr, tpr, where="post", color=_color(name), linewidth=2,
                linestyle={"M2": "-"}.get(name, "--" if "haiku" in name else ":"),
                label=f"{_label(name)}, AUROC {out[name]:.2f}")
    ax.plot([0, 1], [0, 1], color="#bbbbbb", linewidth=1)
    ax.set_xlabel("False positive rate (benign test episodes)")
    ax.set_ylabel("True positive rate (A2 episodes)")
    ax.set_title(f"B test vs slow attack A2, {condition}\n(episode maximum score; 40 vs 20 episodes)",
                 fontsize=10, loc="left")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    _style(ax)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return out


def twin_end_of_plan(cfg: ControlConfig, ep: dict) -> np.ndarray:
    """Temperature the twin predicts for the end of each plan, from the checkpoint reading."""
    n, period = cfg["plant"]["plan_len"], cfg["plant"]["command_period_s"]
    out = []
    for j, t0 in enumerate(ep["t_checkpoint"]):
        current = np.repeat(np.asarray(ep["commands"][j * n:(j + 1) * n], dtype=float), period)
        _, final = simulate(cfg.cell, Fault(), State(0.5, 0.0, 0.0, float(t0)), current, soc_limits=None)
        out.append(final.temp)
    return np.array(out)


def trajectory_table(cfg: ControlConfig, ep: dict) -> list[dict]:
    """Per plan: reading at the checkpoint, twin prediction and plant truth at the end of the plan."""
    n = cfg["plant"]["plan_len"]
    amb = cfg.cell.t_amb
    pred = twin_end_of_plan(cfg, ep)
    rows = []
    for j in range(len(pred)):
        rows.append({
            "plan": j, "mean_abs_command_a": float(np.mean(np.abs(ep["commands"][j * n:(j + 1) * n]))),
            "dT_reading_k": float(ep["t_checkpoint"][j] - amb),
            "dT_twin_end_k": float(pred[j] - amb),
            "dT_plant_end_k": float(ep["temp_minute"][(j + 1) * n] - amb),
            "twin_score_k": float(ep["twin_scores"][j]),
        })
    return rows


def fig_a3_episode(cfg: ControlConfig, ep: dict, result: dict, path: Path) -> None:
    plant = cfg["plant"]
    n, amb = plant["plan_len"], cfg.cell.t_amb
    limit = plant["t_limit_k"] - amb
    cond = result["conditions"][ep["condition"]]
    key = pipeline.episode_key(ep)
    pred = twin_end_of_plan(cfg, ep) - amb
    minutes = np.arange(len(ep["temp_minute"]))
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.plot(minutes, np.asarray(ep["temp_minute"]) - amb, color="#222222", linewidth=2, label="Plant (true)")
    for j in range(len(pred)):  # one short segment per plan: from the reading to the twin's end-of-plan value
        ax.plot([j * n, (j + 1) * n], [ep["t_checkpoint"][j] - amb, pred[j]], color=COLORS["M2"], linewidth=1.6,
                marker="o", markersize=3, label="Twin prediction for each plan" if j == 0 else None)
    ax.axhline(limit, color="#B00020", linewidth=1.2)
    ax.text(0.3, limit + 0.15, f"limit (+{limit:.0f} K)", color="#B00020", fontsize=8)
    if ep["violation_time_s"] is not None:
        tv = ep["violation_time_s"] / 60
        ax.axvline(tv, color="#B00020", linewidth=1, linestyle=":")
        ax.text(tv + 0.3, 0.6, f"limit crossed\n{tv:.0f} min", color="#B00020", fontsize=8)
    y_mark = 1.6
    for name, st in cond["stops"].items():
        if name == "M0" or name.startswith("M3") or st.get(key) is None:
            continue
        x = st[key] * n
        ax.axvline(x, color=_color(name), linewidth=1, linestyle="--")
        ax.text(x + 0.3, y_mark, f"{_label(name)}\nstops at {x} min", color="#222222", fontsize=8)
        y_mark += 1.8
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Temperature above ambient (K)")
    ax.set_title(f"A3 episode {ep['index']} ({ep['kind']} request), {ep['condition']}: "
                 "the twin under-predicts each plan", fontsize=10, loc="left")
    ax.set_xlim(0, 60)
    ax.set_ylim(0, max(limit + 1.5, float(np.max(ep["temp_minute"]) - amb) + 0.8))
    _style(ax)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="run directory under results/d2_pilot")
    args = ap.parse_args()
    cfg = load_control_config()
    root = paths().results / "d2_pilot"
    episodes, _ = pipeline.generate_episodes(cfg)

    llm: dict[str, dict] = {}
    costs: dict[str, dict] = {}
    for run in args.run:
        stored = json.loads((root / run / "episodes.json").read_text(encoding="utf-8"))
        for a, b in zip(stored, episodes):  # the scored episodes are the ones regenerated here
            assert pipeline.episode_key(a) == pipeline.episode_key(b)
            assert np.allclose(a["commands"], b["commands"]) and np.allclose(a["t_meas_end"], b["t_meas_end"])
        run_metrics = json.loads((root / run / "metrics.json").read_text(encoding="utf-8"))
        for f in sorted((root / run).glob("llm_*.json")):
            model = f.stem[4:]
            llm[model] = json.loads(f.read_text(encoding="utf-8"))
            costs[model] = run_metrics["cost"][model]

    result = metrics.evaluate(cfg, episodes, llm)
    result["repeat_spread"] = {m: metrics.repeat_spread(r) for m, r in llm.items()}
    result["cost"] = costs
    out = root / "combined"
    out.mkdir(parents=True, exist_ok=True)

    fig_safety_vs_delta(cfg, result, root / "fig_1_a3_safety_vs_delta.png")
    first = next(iter(cfg["conditions"]))
    result["roc_auroc"] = fig_roc(episodes, llm, first, root / "fig_2_roc_b_vs_a2.png")

    # A3 failures of the twin monitor: violation not prevented by M2. The two worst by time to crossing.
    last = list(cfg["conditions"])[-1]
    stops = result["conditions"][last]["stops"]["M2"]
    failures = [e for e in episodes if e["condition"] == last and e["set"] == "A3"
                and not metrics.is_safe(cfg, e, stops[pipeline.episode_key(e)])]
    failures.sort(key=lambda e: (e["violation_time_s"], e["index"]))
    result["a3_failure_cases"] = [
        {"index": e["index"], "kind": e["kind"], "violation_time_s": e["violation_time_s"],
         "m2_stop_plan": stops[pipeline.episode_key(e)], "attack_start_plan": e["attack_start_plan"],
         "llm_stop_plan": {name: st[pipeline.episode_key(e)]
                           for name, st in result["conditions"][last]["stops"].items() if name.startswith("M1")},
         "per_plan": trajectory_table(cfg, e)} for e in failures[:2]]
    if failures:
        fig_a3_episode(cfg, failures[0], result, root / "fig_3_a3_episode.png")

    dump(out / "metrics.json", result)
    write_summary(cfg, result, out / "summary.md")
    print(f"combined results in {out}; figures in {root}")


if __name__ == "__main__":
    main()
