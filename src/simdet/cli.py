"""Command line: simdet gen | check | run | report | cost (spec 11)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from simdet.config import load_config, paths


def _csv(text: str) -> list[str]:
    return [t.strip() for t in text.split(",") if t.strip()]


def _print_checks(checks: list[dict]) -> bool:
    ok = True
    for c in checks:
        failed = len(c["failures"])
        ok &= not failed
        print(f"  [{'PASS' if not failed else 'FAIL'}] {c['name']}" + (f" ({failed} scenarios)" if failed else ""))
    return ok


def _print_audit(audit: list[dict]) -> bool:
    """Aliasing audit of the SOC0 / ST pair (delta chi2 over fresh seeds)."""
    for r in audit:
        print(f"  [{'PASS' if r['passed'] else 'FAIL'}] alias audit {r['cause']} {r['label']}: "
              f"mean delta chi2 {r['mean']:+.3f}, above boundary {100 * r['share_above']:.1f}% of {r['seeds']} seeds")
    return all(r["passed"] for r in audit)


def cmd_gen(args) -> int:
    from simdet.scenario import generate as g

    cfg, p = load_config(args.config), paths()
    if list(p.public.glob("*.json")) and not args.force:
        print(f"{p.public} already holds scenarios. Pass --force to replace them.")
        return 2
    result = g.generate(cfg, args.n, args.seed)
    privates = [s["private"] for s in result["scenarios"]]
    checks = g.run_checks(privates)
    print(f"generated {len(privates)} of {args.n} scenarios; discarded {len(result['discarded'])}, "
          f"left empty {len(result['unfilled'])}")
    audit = g.run_audit(cfg)
    ok = _print_checks(checks) and _print_audit(audit) and not result["unfilled"]
    save = ok or args.save_on_check_failure
    if save:
        g.save(result, p.scenarios)
    report = g.write_report(cfg, result, checks, p.scenarios, saved=save, audit=audit)
    print(f"report: {report}")
    if not ok:
        print("Spec 7.4 is not met. " + ("Scenarios were saved anyway (--save-on-check-failure)."
              if save else "Nothing was saved; see the report, or pass --save-on-check-failure."))
        return 1
    return 0


def cmd_check(args) -> int:
    from simdet.scenario import generate as g

    cfg, p = load_config(args.config), paths()
    privates = g.load_privates(p.private)
    if not privates:
        print("no scenarios; run `simdet gen` first")
        return 2
    mismatches = g.recheck(cfg, privates)
    for m in mismatches:
        print(f"  oracle changed for {m['id']}: stored {m['stored']}, now {m['recomputed']} ({m['status']})")
    print(f"{len(privates)} scenarios, oracle recomputed: {len(mismatches)} differ from the stored verdict")
    ok = _print_checks(g.run_checks(privates))
    ok = _print_audit(g.run_audit(cfg)) and ok
    return 0 if ok and not mismatches else 1


def _estimate(cfg, model: str, conditions: list[str], publics: list[dict], repeats: int) -> tuple[float, float]:
    """(calls, USD) expected for one real model. Rough; the pilot gives the real number."""
    from simdet.agent.prompt import build_system_prompt, build_user_message

    agent = cfg["agent"]
    est, price = agent["estimate"], agent["pricing_usd_per_mtok"][model]
    version = agent["prompt_version"]
    calls = cost = 0.0
    for cond in conditions:
        system = build_system_prompt(cfg, cond, version)
        per_episode = float(est["calls_per_episode"][cond])
        for pub in publics:
            tokens_in = (len(system) + len(build_user_message(pub, version))) / float(est["chars_per_token"])
            n = per_episode * repeats
            calls += n
            cost += n * (tokens_in * price["input"] + est["output_tokens_per_call"] * price["output"]) / 1e6
    return calls, cost


def cmd_run(args) -> int:
    from simdet.agent.client import Budget, BudgetExceeded, ClaudeClient
    from simdet.agent.mock import BASELINES, MOCK_NAMES, make_mock
    from simdet.agent.runner import dumps, run_episode
    from simdet.scenario.env import load_env, load_private
    from simdet.scenario.public_view import list_ids, load_public
    from simdet.score.grade import grade_episode

    cfg, p = load_config(args.config), paths()
    models = _csv(args.model)
    conditions = _csv(args.condition)
    if any(c not in ("A", "B") for c in conditions):
        print("--condition takes A, B or A,B")
        return 2
    real = [m for m in models if m not in MOCK_NAMES]
    unknown = [m for m in real if m not in cfg["agent"]["pricing_usd_per_mtok"]]
    if unknown:
        print(f"no price configured for: {', '.join(unknown)} (config agent.pricing_usd_per_mtok)")
        return 2
    if real and not args.no_baselines:
        models += [b for b in BASELINES if b not in models]
    ids = list_ids(p.public)[: args.limit] if args.limit else list_ids(p.public)
    if not ids:
        print("no scenarios; run `simdet gen` first")
        return 2
    publics = [load_public(p.public, sid) for sid in ids]

    n_episodes = len(ids) * len(conditions) * args.repeats
    print(f"{len(ids)} scenarios x {len(conditions)} condition(s) x {args.repeats} repeat(s) "
          f"= {n_episodes} episodes per model; models: {', '.join(models)}")
    total = 0.0
    for m in real:
        calls, cost = _estimate(cfg, m, conditions, publics, args.repeats)
        total += cost
        print(f"  {m}: about {calls:.0f} API calls, about ${cost:.2f} (cached responses cost nothing)")
    budget = Budget(float(cfg["agent"]["budget_usd"]))
    if real:
        print(f"  estimated total ${total:.2f}; budget ${budget.limit_usd:.2f}")
        if not args.yes:
            print("Nothing was sent. Pass --yes to call the API.")
            return 0

    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_dir = p.results / run_id
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = p.results / f"{run_id}-{suffix}"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(json.dumps({
        "run_id": run_dir.name, "models": models, "conditions": conditions, "repeats": args.repeats,
        "scenario_ids": ids, "prompt_version": cfg["agent"]["prompt_version"],
        "effort": cfg["agent"].get("effort"), "max_tokens": cfg["agent"]["max_tokens"],
        "config_sha": cfg.physics_sha(), "budget_usd": budget.limit_usd,
    }, indent=1), encoding="utf-8")

    stopped = None
    with open(run_dir / "episodes.jsonl", "x", encoding="utf-8") as out:
        try:
            for m in models:
                client = (make_mock(m, p.private, cfg) if m in MOCK_NAMES
                          else ClaudeClient(m, cfg, p.cache, budget))
                for cond in conditions:
                    done = 0
                    for pub in publics:
                        private = load_private(p.private, pub["id"])
                        for rep in range(args.repeats):
                            env = load_env(cfg, p.private, pub["id"]) if cond == "B" else None
                            record = run_episode(client, cfg, pub, cond, env, rep)
                            record["grade"] = grade_episode(cfg, record, private)
                            out.write(dumps(record) + "\n")
                            out.flush()
                            done += 1
                    print(f"  {m} {cond}: {done} episodes, spent so far ${budget.spent_usd:.4f}")
        except BudgetExceeded as e:
            stopped = str(e)
            print(f"STOPPED: {e}. Episodes finished so far are saved.")
    if stopped:
        (run_dir / "STOPPED.txt").write_text(stopped + "\n", encoding="utf-8")
    _report(cfg, p, [run_dir])
    print(f"run: {run_dir.name}")
    return 3 if stopped else 0


def _report(cfg, p, run_dirs: list[Path]) -> Path | None:
    from simdet.score.report import write_report

    log_path = p.scenarios / "generation_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else None
    out = run_dirs[0]
    n = 1
    while (out / "summary.md").exists():  # never overwrite an earlier report
        n += 1
        out = run_dirs[0] / f"report_{n}"
    try:
        write_report(cfg, run_dirs, out, log)
    except ValueError as e:
        print(f"no report: {e}")
        return None
    print(f"report: {out}")
    return out


def _run_dirs(p, text: str) -> list[Path] | None:
    dirs = [p.results / r for r in _csv(text)]
    missing = [d.name for d in dirs if not (d / "episodes.jsonl").exists()]
    if missing:
        print(f"no episodes.jsonl for run(s): {', '.join(missing)}")
        return None
    return dirs


def cmd_report(args) -> int:
    cfg, p = load_config(args.config), paths()
    dirs = _run_dirs(p, args.run)
    if dirs is None:
        return 2
    return 0 if _report(cfg, p, dirs) else 1


def cmd_cost(args) -> int:
    from simdet.score.report import cost_rows, load_episodes

    dirs = _run_dirs(paths(), args.run)
    if dirs is None:
        return 2
    header = ["model", "cond", "episodes", "calls", "retried", "input_tok", "output_tok", "usd"]
    rows = [header] + [[str(x) for x in r] for r in cost_rows(load_episodes(dirs))]
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="simdet")
    parser.add_argument("--config", default=None, help="path to a config yaml (default: config/default.yaml)")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("gen", help="generate and validate scenarios")
    g.add_argument("--n", type=int, default=72)
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--force", action="store_true", help="replace existing scenarios")
    g.add_argument("--save-on-check-failure", action="store_true",
                   help="save the scenarios even if a spec 7.4 check fails (the report records it)")
    g.set_defaults(func=cmd_gen)

    c = sub.add_parser("check", help="re-run the spec 7.4 checks on stored scenarios")
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("run", help="run episodes")
    r.add_argument("--model", required=True, help="comma-separated model IDs or mock names")
    r.add_argument("--condition", default="A", help="A, B or A,B")
    r.add_argument("--repeats", type=int, default=1)
    r.add_argument("--limit", type=int, default=None, help="use only the first N scenarios")
    r.add_argument("--yes", action="store_true", help="actually call the API")
    r.add_argument("--no-baselines", action="store_true",
                   help="do not add the two mock baselines to a run with real models")
    r.set_defaults(func=cmd_run)

    rep = sub.add_parser("report", help="build summary, figures and examples for a run")
    rep.add_argument("--run", required=True, help="run id, or several separated by commas")
    rep.set_defaults(func=cmd_report)

    cost = sub.add_parser("cost", help="tokens and cost of a run")
    cost.add_argument("--run", required=True)
    cost.set_defaults(func=cmd_cost)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
