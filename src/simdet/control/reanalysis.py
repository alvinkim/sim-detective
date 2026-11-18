"""P0 of SIMDET-D2-FOLLOWUP-001: reanalysis of the first-round data. No API call.

    python -m simdet.control.reanalysis

Reads the stored LLM scores of results/d2_pilot/live_*/ and regenerates the (deterministic)
episodes. Writes results/d2_r2/reanalysis/{metrics.json, tables.md}. Nothing under
results/d2_pilot/ is changed.

P0-1  thresholds fixed on the T0 calibration set and applied to every twin condition
P0-2  rule baselines R1 (tracking) and R2 (temperature alarm)
P0-3  safety over attack episodes whose benign counterpart would not have violated
"""

from __future__ import annotations

import json

import numpy as np

from simdet.config import paths
from simdet.control import evalx, metrics, pipeline
from simdet.control.config import ControlConfig, load_control_config, load_templates
from simdet.control.feasibility import episode_inputs
from simdet.control.plant import run_episode
from simdet.control.policies import Policy
from simdet.control.run import dump

RUNS = ("live_haiku", "live_sonnet")
ATTACKS = ("A1", "A2", "A3")
SHORT = {"claude-haiku-5-5": "Haiku", "claude-sonnet-5-5": "Sonnet"}


def benign_counterpart_violates(cfg: ControlConfig, episodes: list[dict]) -> dict[str, bool]:
    """For every attack episode: does the benign policy on the same request, in the same plant
    and with the same random streams, cross the temperature limit?"""
    templates = load_templates()
    out = {}
    for e in episodes:
        if e["set"] not in ATTACKS:
            continue
        _, request, r_pol, r_noise = episode_inputs(cfg, e["set"], e["index"])
        ep = run_episode(cfg, cfg.plant_cell(e["condition"]), Policy(cfg, "B", templates, r_pol), request, r_noise)
        out[pipeline.episode_key(e)] = ep.violation_time_s(cfg["plant"]["t_limit_k"]) is not None
    return out


def load_llm() -> dict[str, dict]:
    root = paths().results / "d2_pilot"
    llm = {}
    for run in RUNS:
        for f in sorted((root / run).glob("llm_*.json")):
            llm[f.stem[4:]] = json.loads(f.read_text(encoding="utf-8"))
    return llm


def score_tables(cfg: ControlConfig, episodes: list[dict], llm: dict[str, dict]) -> dict:
    scores = metrics.monitor_scores(episodes, llm)  # M2 and M1:<model>
    scores["R1"] = {pipeline.episode_key(e): evalx.rule_tracking(cfg, e) for e in episodes}
    scores["R2"] = {pipeline.episode_key(e): evalx.rule_temperature(cfg, e) for e in episodes}
    return scores


def run(cfg: ControlConfig) -> dict:
    episodes, _ = pipeline.generate_episodes(cfg)
    llm = load_llm()
    scores = score_tables(cfg, episodes, llm)
    combos = tuple((f"M3:{m}", "M2", f"M1:{m}") for m in llm)
    benign = benign_counterpart_violates(cfg, episodes)
    kw = dict(cal_set="B_cal", test_set="B_test", attack_sets=ATTACKS, combos=combos, benign_violates=benign)
    first = next(iter(cfg["conditions"]))
    return {"per_condition": evalx.evaluate(cfg, episodes, scores, **kw),
            "t0_fixed": evalx.evaluate(cfg, episodes, scores, fixed_condition=first, **kw),
            "llm_models": list(llm)}


# -- tables ------------------------------------------------------------------------------------
def _names(result: dict) -> list[str]:
    order = ["M0", "R1", "R2", "M2"]
    for m in result["llm_models"]:
        order += [f"M1:{m}", f"M3:{m}"]
    return order


def _head(name: str) -> str:
    if ":" not in name:
        return {"M0": "M0 없음", "R1": "R1 추종", "R2": "R2 온도", "M2": "M2 twin"}[name]
    kind, model = name.split(":")
    return f"{kind} {SHORT.get(model, model)}"


def _pct(r: dict | None) -> str:
    if r is None or r["n"] == 0:
        return "–"
    return f"{100 * r['rate']:.0f}% ({r['k']}/{r['n']})"


def _table(result: dict, mode: str, cell) -> list[str]:
    names = _names(result)
    lines = ["| 조건 | 공격 | " + " | ".join(_head(n) for n in names) + " |",
             "|---|---|" + "---|" * len(names)]
    for condition, cond in result[mode]["conditions"].items():
        for attack in ATTACKS:
            row = [cell(cond["monitors"][n]["attacks"][attack]) if n in cond["monitors"] else "–" for n in names]
            lines.append(f"| {condition} | {attack} | " + " | ".join(row) + " |")
    return lines


def tables(result: dict) -> str:
    names = _names(result)
    out: list[str] = []
    for mode, title in (("per_condition", "조건별 threshold (1차 방식)"), ("t0_fixed", "T0 고정 threshold")):
        conds = result[mode]["conditions"]
        out += [f"## {title}", "", "### Threshold", "",
                "| 조건 | " + " | ".join(_head(n) for n in names[1:]) + " |", "|---|" + "---|" * (len(names) - 1)]
        for condition, cond in conds.items():
            cells = []
            for n in names[1:]:
                t = cond["thresholds"].get(n)
                cells.append("–" if t is None else f"{t:.2f}" if not isinstance(t, dict)
                             else " / ".join(f"{v:.2f}" for k, v in t.items() if k != "share"))
            out.append(f"| {condition} | " + " | ".join(cells) + " |")
        out += ["", "### Safety", ""] + _table(result, mode, lambda a: _pct(a["safety"]))
        out += ["", "### Safety, 정상 운전이면 위반하지 않았을 episode만", ""]
        out += _table(result, mode, lambda a: _pct(a["safety_benign_ok"]))
        out += ["", "### Catch rate (괄호 뒤 숫자는 위반 뒤에 정지시킨 건수)", ""]
        out += _table(result, mode, lambda a: _pct(a["catch"]) + (f", 늦음 {a['caught_too_late']}"
                                                                 if a["caught_too_late"] else ""))
        out += ["", "### False stop (B test 40건)", "",
                "| 조건 | " + " | ".join(_head(n) for n in names[1:]) + " |", "|---|" + "---|" * (len(names) - 1)]
        for condition, cond in conds.items():
            out.append(f"| {condition} | " + " | ".join(
                _pct(cond["monitors"][n]["false_stop"]) if n in cond["monitors"] else "–" for n in names[1:]) + " |")
        if mode == "t0_fixed":
            out += ["", "### False stop (그 조건의 B calibration 40건, T0 밖에서는 threshold 결정에 쓰이지 않음)", "",
                    "| 조건 | " + " | ".join(_head(n) for n in names[1:]) + " |", "|---|" + "---|" * (len(names) - 1)]
            for condition, cond in conds.items():
                out.append(f"| {condition} | " + " | ".join(
                    _pct(cond["monitors"][n]["cal_false_stop"]) if n in cond["monitors"] else "–"
                    for n in names[1:]) + " |")
        out.append("")
    conds = result["per_condition"]["conditions"]
    out += ["## 정상 정책으로 운전해도 위반하는 공격 episode 수", "", "| 조건 | A1 | A2 | A3 |", "|---|---|---|---|"]
    for condition, cond in conds.items():
        a = cond["monitors"]["M0"]["attacks"]
        out.append(f"| {condition} | " + " | ".join(
            f"{a[k]['benign_would_violate']}/{a[k]['safety']['n']}" for k in ATTACKS) + " |")
    return "\n".join(out) + "\n"


def main() -> None:
    cfg = load_control_config()
    result = run(cfg)
    out = paths().results / "d2_r2" / "reanalysis"
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "metrics.json", result)
    (out / "tables.md").write_text(tables(result), encoding="utf-8")
    print(f"reanalysis written to {out}")


if __name__ == "__main__":
    main()
