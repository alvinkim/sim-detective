"""Scenario generation, validation (spec 7.4) and storage."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from simdet.oracle.experiments import experiment_power, oracle_of
from simdet.scenario.public_view import public_scenario
from simdet.scenario.world import World, world_from_private
from simdet.sim.faults import LABELS, SHIFT_CAUSES, magnitude, make_fault

NOTES_MARKER = "<!-- Notes below this line are written by hand and kept by `simdet gen`. -->"


def plan(cfg, n: int) -> list[dict]:
    """The 7.1 table as a list of slots, interleaved so that a prefix stays balanced."""
    groups: list[list[dict]] = []
    for regime, counts in cfg["scenario"]["plan"].items():
        for cause, count in counts.items():
            if cause == "H":
                sizes = [None] * count
            else:
                sizes = ["small" if i % 2 == 0 else "large" for i in range(count)]
            groups.append([{"regime": regime, "cause": cause, "size": s} for s in sizes])
    base: list[dict] = []
    for i in range(max(len(g) for g in groups)):
        base.extend(g[i] for g in groups if i < len(g))
    return [base[i % len(base)] for i in range(n)]


def _slot_seed(master_seed: int, slot: int, attempt: int) -> int:
    return int(np.random.SeedSequence([master_seed, slot, attempt]).generate_state(1)[0])


def build_private(cfg, scenario_id: str, slot: dict, seed: int, world: World, oracle) -> dict:
    cause = slot["cause"]
    power = (
        experiment_power(cfg, world, oracle.consistent_set, cause)
        if oracle.status == "ok" and len(oracle.consistent_set) >= 2
        else []
    )
    return {
        "id": scenario_id,
        "cause": cause,
        "cause_label": LABELS[cause],
        "magnitude": {"size": slot["size"], "value": magnitude(cause, slot["size"], cfg)},
        "regime": slot["regime"],
        "seed": seed,
        "fault": asdict(world.fault),
        "consistent_set": list(oracle.consistent_set),
        "identifiable": oracle.identifiable,
        "oracle": oracle.to_json(),
        "experiment_power": power,
        "true_state": asdict(world.current.true_state),
        "twin_state": asdict(world.current.twin_state),
        "n_samples": world.current.n,
        "config_sha": cfg.physics_sha(),
    }


def generate(cfg, n: int, master_seed: int) -> dict:
    """Generate up to `n` scenarios. A slot whose oracle verdict is ambiguous or invalid
    is retried with another seed (rules 3 and 4 of spec 6.2), up to max_attempts."""
    slots = plan(cfg, n)
    id_rng = np.random.default_rng([master_seed, 0x5D])
    used: set[str] = set()
    scenarios, discarded, unfilled = [], [], []
    for index, slot in enumerate(slots):
        fault = make_fault(slot["cause"], magnitude(slot["cause"], slot["size"], cfg))
        for attempt in range(int(cfg["scenario"]["max_attempts"])):
            seed = _slot_seed(master_seed, index, attempt)
            world = World(cfg, fault, slot["regime"], seed)
            oracle = oracle_of(cfg, world, slot["cause"])
            if oracle.status == "ok":
                break
            discarded.append({"slot": index, **slot, "seed": seed, "reason": oracle.status,
                              "oracle": oracle.to_json()})
        else:
            unfilled.append({"slot": index, **slot})
            continue
        while True:
            scenario_id = f"{int(id_rng.integers(0, 2**32)):08x}"
            if scenario_id not in used:
                used.add(scenario_id)
                break
        scenarios.append({
            "public": public_scenario(cfg, scenario_id, world),
            "private": build_private(cfg, scenario_id, slot, seed, world, oracle),
        })
    return {"scenarios": scenarios, "discarded": discarded, "unfilled": unfilled,
            "requested": n, "seed": master_seed}


def run_checks(privates: list[dict]) -> list[dict]:
    """The four conditions of spec 7.4. Each returns the scenarios that violate it."""

    def brief(p: dict, why: str) -> dict:
        return {"id": p["id"], "regime": p["regime"], "cause": p["cause"],
                "size": p["magnitude"]["size"], "consistent_set": p["consistent_set"],
                "why": why, "rms_v": p["oracle"]["rms_v"], "rms_t": p["oracle"]["rms_t"]}

    c1 = [brief(p, "not identifiable") for p in privates
          if p["regime"] == "DYN" and p["magnitude"]["size"] == "large"
          and p["cause"] in SHIFT_CAUSES and not p["identifiable"]]
    c2 = [brief(p, "consistent set has fewer than 2 causes") for p in privates
          if p["regime"] == "CC" and p["cause"] in SHIFT_CAUSES and len(p["consistent_set"]) < 2]
    c3 = [brief(p, "set is not exactly the planted cause") for p in privates
          if p["cause"] in ("H", "N") and p["consistent_set"] != [p["cause"]]]
    c4 = [brief(p, "no resolving experiment") for p in privates
          if not p["identifiable"]
          and not any(e["class"] == "resolving" for e in p["experiment_power"])]
    return [
        {"name": "DYN large scenarios are identifiable", "failures": c1},
        {"name": "CC scenarios of R0, SOC0, TB, ST have a consistent set of size >= 2", "failures": c2},
        {"name": "H scenarios give {H}, N scenarios give {N}", "failures": c3},
        {"name": "every non-identifiable scenario has a resolving experiment", "failures": c4},
    ]


def recheck(cfg, privates: list[dict]) -> list[dict]:
    """Recompute the oracle of stored scenarios from scratch; returns mismatches."""
    mismatches = []
    for p in privates:
        world = world_from_private(cfg, p)
        oracle = oracle_of(cfg, world, p["cause"])
        if list(oracle.consistent_set) != p["consistent_set"] or oracle.status != "ok":
            mismatches.append({"id": p["id"], "stored": p["consistent_set"],
                               "recomputed": list(oracle.consistent_set), "status": oracle.status})
    return mismatches


def load_privates(private_dir: str | Path) -> list[dict]:
    out = []
    for path in sorted(Path(private_dir).glob("*.json")):
        with open(path, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def _dump(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, separators=(",", ":"))


def save(result: dict, scenarios_dir: str | Path) -> None:
    """Replace the stored scenario set with `result`."""
    root = Path(scenarios_dir)
    for sub in ("public", "private"):
        (root / sub).mkdir(parents=True, exist_ok=True)
        for old in (root / sub).glob("*.json"):
            old.unlink()
    for s in result["scenarios"]:
        sid = s["private"]["id"]
        _dump(root / "public" / f"{sid}.json", s["public"])
        _dump(root / "private" / f"{sid}.json", s["private"])


def composition(privates: list[dict]) -> dict:
    """(regime, cause) -> counts, for reports."""
    table: dict[tuple[str, str], dict] = {}
    for p in privates:
        cell = table.setdefault((p["regime"], p["cause"]), {"n": 0, "identifiable": 0, "sets": {}})
        cell["n"] += 1
        cell["identifiable"] += int(p["identifiable"])
        key = "{" + ", ".join(p["consistent_set"]) + "}"
        cell["sets"][key] = cell["sets"].get(key, 0) + 1
    return table


def discard_summary(result_or_log: dict) -> dict:
    reasons: dict[str, int] = {}
    for d in result_or_log.get("discarded", []):
        reasons[d["reason"]] = reasons.get(d["reason"], 0) + 1
    return {"discarded": reasons, "unfilled": len(result_or_log.get("unfilled", []))}


def write_report(cfg, result: dict, checks: list[dict], scenarios_dir: str | Path, saved: bool) -> Path:
    """Write scenarios/GENERATION_REPORT.md and generation_log.json."""
    root = Path(scenarios_dir)
    root.mkdir(parents=True, exist_ok=True)
    privates = [s["private"] for s in result["scenarios"]]
    th = cfg["oracle"]
    lines = [
        "# Scenario generation report",
        "",
        "Generated by `simdet gen`. Everything above the notes marker is rewritten on each run.",
        "",
        f"- requested: {result['requested']}, seed: {result['seed']}, generated: {len(privates)}, "
        f"saved to scenarios/: {'yes' if saved else 'NO'}",
        f"- config hash: `{cfg.physics_sha()}`",
        f"- oracle thresholds: consistent <= {th['consistent_max']}, clear reject >= "
        f"{th['clear_reject_min']}, noise ratio >= {th['noise_ratio_min']}, "
        f"channel combination: `{th.get('rms_mode', 'max_channel')}`",
        "",
        "## Composition",
        "",
        "| Regime | Cause | n | identifiable | consistent sets |",
        "|---|---|---|---|---|",
    ]
    for (regime, cause), cell in sorted(composition(privates).items()):
        sets = ", ".join(f"{k} x{v}" for k, v in sorted(cell["sets"].items()))
        lines.append(f"| {regime} | {cause} | {cell['n']} | {cell['identifiable']} | {sets} |")
    n_ident = sum(p["identifiable"] for p in privates)
    lines += ["", f"Identifiable: {n_ident}, not identifiable: {len(privates) - n_ident}.", ""]

    lines += ["## Discarded and unfilled", ""]
    if not result["discarded"] and not result["unfilled"]:
        lines.append("None.")
    for d in result["discarded"]:
        lines.append(
            f"- slot {d['slot']} ({d['regime']} {d['cause']} {d['size']}, seed {d['seed']}): "
            f"{d['reason']}; set {d['oracle']['consistent_set']}, gray {d['oracle']['gray']}, "
            f"decision rms {_fmt(d['oracle']['decision_rms'])}"
        )
    for u in result["unfilled"]:
        lines.append(f"- slot {u['slot']} ({u['regime']} {u['cause']} {u['size']}): no usable seed "
                     f"in {cfg['scenario']['max_attempts']} attempts, left empty")
    lines += ["", "## Spec 7.4 checks", ""]
    for c in checks:
        lines.append(f"### {'PASS' if not c['failures'] else 'FAIL'}: {c['name']}")
        lines.append("")
        if c["failures"]:
            lines.append("Per-hypothesis RMS is given as voltage channel / temperature channel "
                         "(units of sigma_hat / SIGMA_T).")
            lines.append("")
            lines.append("| id | regime | cause | size | consistent set | why | H | R0 | SOC0 | TB | ST |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
            for f in c["failures"]:
                cells = " | ".join(f"{f['rms_v'][h]:.2f} / {f['rms_t'][h]:.2f}"
                                   for h in ("H", "R0", "SOC0", "TB", "ST"))
                lines.append(f"| {f['id']} | {f['regime']} | {f['cause']} | {f['size']} | "
                             f"{{{', '.join(f['consistent_set'])}}} | {f['why']} | {cells} |")
            lines.append("")
    path = root / "GENERATION_REPORT.md"
    notes = ""
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if NOTES_MARKER in old:
            notes = old.split(NOTES_MARKER, 1)[1]
    path.write_text("\n".join(lines) + "\n" + NOTES_MARKER + (notes or "\n"), encoding="utf-8")
    _dump(root / "generation_log.json", {
        "requested": result["requested"], "seed": result["seed"], "generated": len(privates),
        "saved": saved, "discarded": result["discarded"], "unfilled": result["unfilled"],
        "checks": [{"name": c["name"], "failed": len(c["failures"])} for c in checks],
    })
    return path


def _fmt(d: dict) -> str:
    return "{" + ", ".join(f"{k}: {v:.2f}" for k, v in d.items()) + "}"
