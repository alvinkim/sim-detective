"""Run the Direction 2 pilot (spec 9, G2 and G3).

    python -m simdet.control.run --monitor mock                 # G2: whole pipeline, no API call
    python -m simdet.control.run --monitor claude-haiku-5-5     # prints the cost estimate and stops
    python -m simdet.control.run --monitor claude-haiku-5-5 --yes

Results go to results/d2_pilot/<name>/. A live run reuses the response cache, so it can be
repeated or extended with a second model without paying twice.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from simdet.config import paths
from simdet.control import metrics, monitor_llm, pipeline
from simdet.control.config import ControlConfig, load_control_config
from simdet.control.summary import write_summary


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    raise TypeError(type(o))


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, default=_json_default), encoding="utf-8")


def call_plan(cfg: ControlConfig, episodes: list[dict]) -> dict:
    """Which model scores which conditions with how many repeats, reduced in the order of
    spec 7.3 until the estimate (list price, empty cache) fits the budget."""
    m = cfg["llm_monitor"]
    all_conditions = list(cfg["conditions"])
    plan = {"repeats": int(m["repeats"]), "conditions": {model: all_conditions for model in m["models"]},
            "reductions": []}

    def estimate() -> dict:
        out = {}
        for model, conds in plan["conditions"].items():
            eps = [e for e in episodes if e["condition"] in conds]
            calls, cost = monitor_llm.estimate_cost(cfg, model, eps, plan["repeats"])
            out[model] = {"calls": calls, "usd": cost}
        return out

    est = estimate()
    budget = float(m["budget_usd"])
    if sum(v["usd"] for v in est.values()) > budget:
        for model in plan["conditions"]:
            if "sonnet" in model:
                plan["conditions"][model] = [all_conditions[0], all_conditions[-1]]
        plan["reductions"].append("1: Sonnet monitor only in the first and last twin condition")
        est = estimate()
    if sum(v["usd"] for v in est.values()) > budget:
        plan["repeats"] = 1
        plan["reductions"].append("2: one LLM repeat instead of three")
        est = estimate()
    plan["estimate"] = est
    plan["estimate_total_usd"] = sum(v["usd"] for v in est.values())
    plan["budget_usd"] = budget
    plan["fits"] = plan["estimate_total_usd"] <= budget
    return plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--monitor", action="append", required=True,
                    help="'mock' or a model id of llm_monitor.models; repeatable")
    ap.add_argument("--name", help="result directory name under results/d2_pilot (default: mock or live)")
    ap.add_argument("--config")
    ap.add_argument("--yes", action="store_true", help="really call the API")
    args = ap.parse_args()

    cfg = load_control_config(args.config)
    live = [m for m in args.monitor if m != monitor_llm.MOCK]
    unknown = [m for m in live if m not in cfg["llm_monitor"]["models"]]
    if unknown:
        raise SystemExit(f"not in llm_monitor.models: {unknown}")

    started = time.perf_counter()
    episodes, twin_thresholds = pipeline.generate_episodes(cfg)
    print(f"{len(episodes)} episodes generated in {time.perf_counter() - started:.0f} s")

    plan = call_plan(cfg, episodes)
    print(f"LLM monitor plan: repeats {plan['repeats']}, reductions {plan['reductions'] or 'none'}")
    for model, est in plan["estimate"].items():
        print(f"  {model}: conditions {plan['conditions'][model]}, {est['calls']} calls, about ${est['usd']:.2f}")
    print(f"  estimated total ${plan['estimate_total_usd']:.2f}; budget ${plan['budget_usd']:.2f}")
    if live and not plan["fits"]:
        raise SystemExit("over budget even after reductions 1 and 2; nothing sent (reduction 3 is not automated)")
    if live and not args.yes:
        print("estimate only; add --yes to call the API")
        return

    p = paths()
    out = p.results / "d2_pilot" / (args.name or ("live" if live else "mock"))
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "episodes.json", episodes)
    dump(out / "plan.json", {**plan, "twin_thresholds_k": twin_thresholds, "config": cfg.raw,
                             "monitors": args.monitor})

    llm: dict[str, dict] = {}
    budget = None
    for model in args.monitor:
        if model == monitor_llm.MOCK:
            llm[model] = pipeline.score_llm(cfg, episodes, model, plan["repeats"])
        else:
            from simdet.agent.client import Budget, ClaudeClient
            budget = budget or Budget(float(cfg["llm_monitor"]["budget_usd"]))
            client = ClaudeClient(model, monitor_llm.client_config(cfg), p.cache, budget)
            eps = [e for e in episodes if e["condition"] in plan["conditions"][model]]
            t0 = time.perf_counter()
            llm[model] = pipeline.score_llm(
                cfg, eps, model, plan["repeats"], client,
                progress=lambda done, total: print(f"  {model}: {done}/{total}, spent ${budget.spent_usd:.2f}",
                                                   flush=True))
            print(f"  {model}: done in {time.perf_counter() - t0:.0f} s, spent so far ${budget.spent_usd:.2f}")
        dump(out / f"llm_{model}.json", llm[model])

    result = metrics.evaluate(cfg, episodes, llm)
    result["repeat_spread"] = {model: metrics.repeat_spread(rec) for model, rec in llm.items()}
    result["cost"] = {model: {"usd": sum(r["cost_usd"] for r in rec.values()),
                              "calls": sum(r["calls"] for r in rec.values()),
                              "cached": sum(r["cached"] for r in rec.values()),
                              "unreadable": sum(r["unreadable"] for r in rec.values())}
                      for model, rec in llm.items()}
    dump(out / "metrics.json", result)
    write_summary(cfg, result, out / "summary.md")
    print(f"results in {out}")


if __name__ == "__main__":
    main()
