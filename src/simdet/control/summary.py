"""summary.md of a run: the tables of spec 10.1 item 3 and the numbers behind H1-H4."""

from __future__ import annotations

from pathlib import Path

from simdet.control import metrics
from simdet.control.config import ControlConfig


def _pct(r: dict) -> str:
    if r["rate"] is None:
        return "–"
    return f"{100 * r['rate']:.0f}% ({r['k']}/{r['n']}) [{100 * r['lo']:.0f}, {100 * r['hi']:.0f}]"


def _diff(d: dict) -> str:
    if d["diff"] is None:
        return "–"
    return f"{100 * d['diff']:+.0f} pt [{100 * d['lo']:+.0f}, {100 * d['hi']:+.0f}] (n={d['n']})"


def _thr(t) -> str:
    if isinstance(t, dict):
        return f"twin {t['twin']:.2f}, llm {t['llm']:.1f}"
    return f"{t:.2f}"


def write_summary(cfg: ControlConfig, result: dict, path: Path) -> None:
    lines = ["# Direction 2 pilot: run summary", "",
             "Rates are shown as percent (count/n) [Wilson 95% interval]. Episodes are the unit.", ""]
    for condition, cond in result["conditions"].items():
        lines += [f"## {condition}", "",
                  f"Violations with no attack: B_cal {_pct(cond['benign_violations']['B_cal'])}, "
                  f"B_test {_pct(cond['benign_violations']['B_test'])}", "",
                  "| Monitor | Threshold | False stop (cal) | False stop (test) | Tracking RMS (A) |",
                  "|---|---|---|---|---|"]
        for name, m in cond["monitors"].items():
            thr = "–" if name == "M0" else _thr(cond["thresholds"][name])
            lines.append(f"| {name} | {thr} | {_pct(m['cal_false_stop'])} | {_pct(m['false_stop'])} "
                         f"| {m['tracking_rms_a']:.1f} |")
        lines += ["", "| Monitor | Attack | Violations, no monitor | Safety | Catch rate | AUROC |",
                  "|---|---|---|---|---|---|"]
        for name, m in cond["monitors"].items():
            for attack, a in m["attacks"].items():
                auc = a.get("auroc")
                lines.append(f"| {name} | {attack} | {a['violations_unmonitored']}/{a['safety']['n']} "
                             f"| {_pct(a['safety'])} | {_pct(a['catch'])} "
                             f"| {'–' if auc is None else f'{auc:.2f}'} |")
        lines.append("")

    conditions = list(result["conditions"])
    lines += ["## Paired differences in safety (same episodes, bootstrap 10,000)", ""]
    for model in result["llm_models"]:
        m1, m3 = f"M1:{model}", f"M3:{model}"
        lines.append(f"- H1, {conditions[0]}, A2: M2 − {m1} = "
                     f"{_diff(metrics.safety_diff(result, conditions[0], 'A2', 'M2', m1))}")
        for c in conditions:
            lines.append(f"- H3, {c}, A3: {m3} − M2 = {_diff(metrics.safety_diff(result, c, 'A3', m3, 'M2'))}")
    lines += ["", "## LLM monitor calls", ""]
    for model, c in result["cost"].items():
        s = result["repeat_spread"][model]
        spread = (f"repeat SD mean {s['mean_sd']:.2f}, max range {s['max_range']:.0f}, "
                  f"identical in {100 * s['share_identical']:.0f}% of checkpoints") if s.get("n") else "no repeats"
        lines.append(f"- {model}: {c['calls']} calls ({c['cached']} from cache), ${c['usd']:.2f}, "
                     f"unreadable {c['unreadable']}; {spread}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
