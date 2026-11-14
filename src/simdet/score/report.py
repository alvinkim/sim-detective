"""Tables, figures and examples for a run (spec 10). Figures use matplotlib only."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from simdet.score import stats  # noqa: E402
from simdet.score.grade import EXPERIMENT_CLASSES, VERDICTS  # noqa: E402
from simdet.sim.faults import CAUSES, LABELS  # noqa: E402

# Light-surface palette: fixed categorical order, one sequential hue, neutral chrome.
SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SEQUENTIAL = LinearSegmentedColormap.from_list("blue", [SURFACE, "#9ec5f4", "#2a78d6", "#0d366b"])
FONT = ["Segoe UI", "DejaVu Sans"]


def load_episodes(run_dirs: list[Path]) -> list[dict]:
    episodes = []
    for d in run_dirs:
        with open(Path(d) / "episodes.jsonl", encoding="utf-8") as f:
            episodes += [json.loads(line) for line in f if line.strip()]
    return episodes


def group_episodes(episodes: list[dict]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in episodes:
        groups[(e["model"], e["condition"])].append(e)
    return dict(sorted(groups.items(), key=lambda kv: (kv[0][0].startswith("mock_"), kv[0])))


def metrics_of(episodes: list[dict]) -> dict[str, dict]:
    return {m: stats.rate(stats.per_scenario(episodes, m)) for m in stats.METRICS}


def _pct(r: dict) -> str:
    if r["rate"] is None:
        return "n/a"
    return f"{100 * r['rate']:.0f}% [{100 * r['lo']:.0f}, {100 * r['hi']:.0f}] (n={r['n']:g})"


def _comparisons(groups: dict) -> list[tuple[tuple, tuple]]:
    """Model pairs within a condition, then A vs B within a model."""
    keys = list(groups)
    pairs = [(a, b) for i, a in enumerate(keys) for b in keys[i + 1:]
             if a[1] == b[1] and a[0] != b[0]]
    pairs += [(a, b) for a in keys for b in keys if a[0] == b[0] and a[1] == "A" and b[1] == "B"]
    return pairs


def summary_markdown(cfg, episodes: list[dict], run_ids: list[str], generation_log: dict | None) -> str:
    groups = group_episodes(episodes)
    n_scen = len({e["scenario_id"] for e in episodes})
    versions = sorted({e["prompt_version"] for e in episodes})
    lines = [
        "# sim-detective summary",
        "",
        f"- runs: {', '.join(run_ids)}",
        f"- episodes: {len(episodes)}, scenarios: {n_scen}, prompt version: {', '.join(versions)}",
        "- Rates are over scenarios (repeats averaged per scenario first), with Wilson 95% intervals.",
        "- In condition B the oracle is recomputed on the data the agent collected, so the "
        "identifiable / not identifiable split differs by model.",
        "- `mock_always_claim` and `mock_always_abstain` are baselines.",
        "",
        "## Metrics",
        "",
        "| Model | Cond. | Cause accuracy (identifiable) | Overclaim rate (not identifiable) | "
        "Over-abstain rate (identifiable) | Resolving experiment chosen (initially not identifiable) | Invalid |",
        "|---|---|---|---|---|---|---|",
    ]
    for (model, cond), eps in groups.items():
        m = metrics_of(eps)
        lines.append(f"| {model} | {cond} | {_pct(m['accuracy'])} | {_pct(m['overclaim'])} | "
                     f"{_pct(m['over_abstain'])} | {_pct(m['experiment'])} | {_pct(m['invalid'])} |")

    lines += ["", "## Verdict counts (episodes)", "",
              "| Model | Cond. | " + " | ".join(VERDICTS) + " | lucky overclaims | mean experiments |",
              "|---|---|" + "---|" * (len(VERDICTS) + 2)]
    for (model, cond), eps in groups.items():
        c = Counter(e["grade"]["verdict"] for e in eps)
        lucky = sum(bool(e["grade"]["lucky"]) for e in eps)
        mean_exp = sum(e["grade"]["n_experiments"] for e in eps) / len(eps)
        lines.append(f"| {model} | {cond} | " + " | ".join(str(c.get(v, 0)) for v in VERDICTS)
                     + f" | {lucky} | {mean_exp:.2f} |")

    lines += ["", "## Paired differences", "",
              f"Paired bootstrap over shared scenarios ({cfg['stats']['bootstrap_n']} resamples), "
              "difference = first minus second, 95% interval.", "",
              "| First | Second | Metric | Difference | Shared scenarios |", "|---|---|---|---|---|"]
    for a, b in _comparisons(groups):
        for metric in ("accuracy", "overclaim", "over_abstain"):
            d = stats.paired_bootstrap_diff(
                stats.per_scenario(groups[a], metric), stats.per_scenario(groups[b], metric),
                int(cfg["stats"]["bootstrap_n"]), int(cfg["stats"]["seed"]))
            text = ("n/a" if d["diff"] is None else
                    f"{100 * d['diff']:+.0f} pt [{100 * d['lo']:+.0f}, {100 * d['hi']:+.0f}]")
            lines.append(f"| {a[0]} {a[1]} | {b[0]} {b[1]} | {stats.METRICS[metric]} | {text} | {d['n']} |")

    lines += ["", "## Calibration", "",
              "Share of answers judged correct or correct_abstain, by stated confidence.", "",
              "| Model | Cond. | Confidence bin | Episodes | Mean confidence | Correct |", "|---|---|---|---|---|---|"]
    for (model, cond), eps in groups.items():
        for b in stats.calibration(eps, list(cfg["stats"]["confidence_bins"])):
            if b["n"]:
                lines.append(f"| {model} | {cond} | {b['lo']:.1f}-{b['hi']:.1f} | {b['n']} | "
                             f"{b['mean_confidence']:.2f} | {100 * b['accuracy']:.0f}% |")

    lines += ["", "## Tokens and cost", "",
              "| Model | Cond. | Episodes | API calls | Input tokens | Output tokens | Cost (USD) |",
              "|---|---|---|---|---|---|---|"]
    for row in cost_rows(episodes):
        lines.append("| " + " | ".join(str(x) for x in row) + " |")

    lines += ["", "## Discarded scenarios", ""]
    if generation_log is None:
        lines.append("No generation log found.")
    else:
        reasons = Counter(d["reason"] for d in generation_log.get("discarded", []))
        lines.append(f"- generated: {generation_log.get('generated')} of {generation_log.get('requested')} requested")
        lines.append("- discarded during generation: "
                     + (", ".join(f"{k}: {v}" for k, v in sorted(reasons.items())) or "0"))
        lines.append(f"- slots left empty: {len(generation_log.get('unfilled', []))}")
        failed = [c["name"] for c in generation_log.get("checks", []) if c["failed"]]
        lines.append("- spec 7.4 checks failed: " + ("; ".join(failed) if failed else "none")
                     + " (details in scenarios/GENERATION_REPORT.md)")
    return "\n".join(lines) + "\n"


def cost_rows(episodes: list[dict]) -> list[list]:
    rows = []
    total = 0.0
    for (model, cond), eps in group_episodes(episodes).items():
        tin = sum(e["usage"]["input_tokens"] + e["usage"]["cache_creation_input_tokens"]
                  + e["usage"]["cache_read_input_tokens"] for e in eps)
        tout = sum(e["usage"]["output_tokens"] for e in eps)
        cost = sum(e["cost_usd"] for e in eps)
        total += cost
        rows.append([model, cond, len(eps), sum(e["n_calls"] for e in eps), tin, tout, f"{cost:.4f}"])
    rows.append(["total", "", len(episodes), sum(e["n_calls"] for e in episodes), "", "", f"{total:.4f}"])
    return rows


def examples_markdown(episodes: list[dict], k: int = 5) -> str:
    """Rationales as written by the model: k overclaims and k correct abstentions."""
    real_first = sorted(episodes, key=lambda e: (e["model"].startswith("mock_"), e["scenario_id"],
                                                 e["model"], e["condition"], e["repeat_index"]))
    lines = ["# Examples", ""]
    for verdict, title in (("overclaim", "Overclaim"), ("correct_abstain", "Correct abstention")):
        lines += [f"## {title}", ""]
        picked = [e for e in real_first if e["grade"]["verdict"] == verdict][:k]
        if not picked:
            lines += ["No episodes.", ""]
        for e in picked:
            a, g = e["answer"], e["grade"]
            lines += [
                f"### {e['scenario_id']} / {e['model']} / condition {e['condition']} / repeat {e['repeat_index']}",
                "",
                f"- planted: {LABELS[g['planted']]}; oracle set after the agent's data: "
                f"{{{', '.join(LABELS[c] for c in g['final_set'])}}}",
                f"- answer: verdict={a['verdict']}, cause={a.get('cause')}, "
                f"candidates={a.get('candidates')}, confidence={a['confidence']}, "
                f"next_experiment={json.dumps(a['next_experiment'])}",
                "",
                "> " + a["rationale"].replace("\n", "\n> "),
                "",
            ]
    return "\n".join(lines) + "\n"


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    for label in ax.get_yticklabels():
        label.set_color(INK_2)


def _labels(groups: dict) -> list[str]:
    return [f"{model}  ·  {cond}" for model, cond in groups]


def fig_overclaim(groups: dict, path: Path) -> None:
    """Overclaim and over-abstain rates per model and condition, with Wilson intervals."""
    series = [("overclaim", "Overclaim rate (not identifiable scenarios)", SERIES[0]),
              ("over_abstain", "Over-abstain rate (identifiable scenarios)", SERIES[1])]
    n = len(groups)
    fig, ax = plt.subplots(figsize=(8.5, 1.4 + 0.75 * n), facecolor=SURFACE)
    h = 0.34
    for j, (metric, label, color) in enumerate(series):
        for i, eps in enumerate(groups.values()):
            r = stats.rate(stats.per_scenario(eps, metric))
            y = i + (j - 0.5) * (h + 0.04)
            if r["rate"] is None:
                ax.text(1, y, "n/a", va="center", fontsize=8.5, color=MUTED)
                continue
            p = 100 * r["rate"]
            ax.barh(y, p, height=h, color=color, label=label if i == 0 else None, zorder=2)
            ax.errorbar(p, y, xerr=[[max(p - 100 * r["lo"], 0)], [max(100 * r["hi"] - p, 0)]], fmt="none",
                        ecolor=INK_2, elinewidth=1, capsize=2.5, zorder=3)
            ax.text(100 * r["hi"] + 1.5, y, f"{p:.0f}%", va="center", fontsize=8.5, color=INK)
    ax.set_yticks(range(n), _labels(groups))
    ax.invert_yaxis()
    ax.set_xlim(0, 112)
    ax.set_xticks(range(0, 101, 25), [f"{v}%" for v in range(0, 101, 25)])
    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    _style(ax)
    ax.set_title("Overclaim and over-abstain rates (bars: rate, whiskers: Wilson 95% interval)",
                 loc="left", fontsize=11, color=INK, pad=28)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in series]
    ax.legend(handles, [s[1] for s in series], loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2,
              frameon=False, fontsize=9, labelcolor=INK_2, handlelength=1, borderaxespad=0.2)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def fig_confusion(groups: dict, path: Path) -> None:
    """Planted cause (rows) against the answer (columns), one panel per model and condition."""
    cols = list(CAUSES) + ["abstain", "invalid"]
    col_labels = [LABELS[c] for c in CAUSES] + ["(abstained)", "(invalid)"]
    n = len(groups)
    ncols = min(n, 3)
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.6 * ncols, 3.9 * nrows), facecolor=SURFACE, squeeze=False)
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    for ax, ((model, cond), eps) in zip(axes.flat, groups.items()):
        counts = [[0] * len(cols) for _ in CAUSES]
        for e in eps:
            answered = e["grade"]["answered"] or "invalid"
            counts[CAUSES.index(e["grade"]["planted"])][cols.index(answered)] += 1
        peak = max(max(row) for row in counts) or 1
        ax.imshow(counts, cmap=SEQUENTIAL, vmin=0, vmax=peak, aspect="auto")
        for i, row in enumerate(counts):
            for j, v in enumerate(row):
                if v:
                    ax.text(j, i, str(v), ha="center", va="center", fontsize=8.5,
                            color="#ffffff" if v > 0.55 * peak else INK)
        ax.set_xticks(range(len(cols)), col_labels, rotation=40, ha="right", fontsize=8)
        ax.set_yticks(range(len(CAUSES)), [LABELS[c] for c in CAUSES], fontsize=8)
        ax.set_xticks([x - 0.5 for x in range(1, len(cols))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, len(CAUSES))], minor=True)
        ax.grid(which="minor", color=SURFACE, linewidth=2)
        ax.tick_params(which="both", length=0, colors=INK_2)
        for side in ax.spines.values():
            side.set_visible(False)
        ax.set_title(f"{model}  ·  {cond}", loc="left", fontsize=10, color=INK)
    fig.suptitle("Planted cause (rows) vs. answered cause (columns), episode counts",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def fig_experiment(groups: dict, path: Path) -> None:
    """How the chosen experiment was classified, on initially non-identifiable scenarios."""
    n = len(groups)
    fig, ax = plt.subplots(figsize=(8.5, 1.5 + 0.55 * n), facecolor=SURFACE)
    for i, eps in enumerate(groups.values()):
        c = Counter(e["grade"]["experiment_class"] for e in eps if not e["grade"]["initial_identifiable"])
        total = sum(c.values())
        left = 0.0
        if not total:
            ax.text(1, i, "n/a", va="center", fontsize=8.5, color=MUTED)
        for k, name in enumerate(EXPERIMENT_CLASSES):
            share = 100 * c.get(name, 0) / total if total else 0
            if share:
                ax.barh(i, share, left=left, height=0.56, color=SERIES[k], edgecolor=SURFACE,
                        linewidth=1.5, zorder=2)
                if share >= 9:
                    ax.text(left + share / 2, i, f"{share:.0f}%", ha="center", va="center", fontsize=8.5,
                            color=INK if name == "inconclusive" else "#ffffff")
            left += share
    ax.set_yticks(range(n), _labels(groups))
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 25), [f"{v}%" for v in range(0, 101, 25)])
    _style(ax)
    ax.set_title("Chosen experiment by class, initially non-identifiable scenarios (share of episodes)",
                 loc="left", fontsize=11, color=INK, pad=28)
    handles = [plt.Rectangle((0, 0), 1, 1, color=SERIES[k]) for k in range(len(EXPERIMENT_CLASSES))]
    ax.legend(handles, EXPERIMENT_CLASSES, loc="lower left", bbox_to_anchor=(0, 1.0),
              ncol=len(EXPERIMENT_CLASSES), frameon=False, fontsize=9, labelcolor=INK_2,
              handlelength=1, columnspacing=1.2, borderaxespad=0.2)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


def write_report(cfg, run_dirs: list[Path], out_dir: Path, generation_log: dict | None) -> Path:
    """Write summary.md, examples.md and the three figures into out_dir."""
    plt.rcParams["font.family"] = FONT
    episodes = load_episodes(run_dirs)
    if not episodes:
        raise ValueError("no episodes to report")
    groups = group_episodes(episodes)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.md").write_text(
        summary_markdown(cfg, episodes, [Path(d).name for d in run_dirs], generation_log), encoding="utf-8")
    (out_dir / "examples.md").write_text(examples_markdown(episodes), encoding="utf-8")
    fig_overclaim(groups, out_dir / "fig_overclaim.png")
    fig_confusion(groups, out_dir / "fig_confusion.png")
    fig_experiment(groups, out_dir / "fig_experiment.png")
    return out_dir
