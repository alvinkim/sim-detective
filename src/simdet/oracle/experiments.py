"""How much each experiment narrows the consistent set (spec 6.3)."""

from __future__ import annotations

from simdet.oracle.fit import OracleData
from simdet.oracle.identifiability import OracleResult, evaluate
from simdet.scenario.world import ExperimentRejected, World

CLASSES = ("resolving", "partial", "useless", "inconclusive", "rejected")


def oracle_of(cfg, world: World, planted: str | None = None) -> OracleResult:
    data = OracleData.from_segment(world.current, float(cfg["sim"]["soc_init"]))
    return evaluate(cfg, data, planted)


def narrowed(before: tuple[str, ...], after: OracleResult, planted: str) -> tuple[tuple[str, ...], str]:
    """Consistent set after more data, restricted to the causes that were still
    possible before it.

    Appending samples that every hypothesis explains equally well lowers every RMS, so
    a hypothesis rejected on the earlier data could drift back under a threshold. A
    rejection is not undone by such data: experiments can only narrow the set.
    Returns (set, status) with the status rules of spec 6.2 applied to that set.
    """
    keep = tuple(h for h in before if h in after.consistent_set)
    if any(h in after.gray for h in before):
        return keep, "ambiguous"
    return keep, ("ok" if planted in keep else "invalid")


def classify(before: tuple[str, ...], after_set: tuple[str, ...], status: str, planted: str) -> str:
    """resolving: the new set is exactly {planted}; partial: smaller but still >= 2;
    useless: unchanged. A verdict that is not 'ok' (a remaining candidate in the gray
    zone, or the planted cause dropped) is inconclusive."""
    if status != "ok":
        return "inconclusive"
    if set(after_set) == {planted}:
        return "resolving"
    if set(after_set) == set(before):
        return "useless"
    return "partial" if len(after_set) >= 2 else "inconclusive"


def experiment_outcome(cfg, world: World, name, args, before: tuple[str, ...], planted: str) -> dict:
    """Run one experiment on a copy of `world` and classify it. Does not mutate `world`."""
    trial = world.clone()
    try:
        trial.run_experiment(name, args)
    except ExperimentRejected as e:
        return {"name": name, "args": args, "class": "rejected", "reason": str(e)}
    new_set, status = narrowed(before, oracle_of(cfg, trial), planted)
    return {
        "name": name,
        "args": trial.experiments[-1]["args"],
        "class": classify(before, new_set, status, planted),
        "new_set": list(new_set),
        "status": status,
    }


def experiment_power(cfg, world: World, before: tuple[str, ...], planted: str) -> list[dict]:
    """Outcome of every menu experiment at its representative arguments."""
    rep = cfg["experiments"]["representative"]
    return [
        experiment_outcome(cfg, world, name, dict(args), before, planted)
        for name, arg_list in rep.items()
        for args in arg_list
    ]


def nearest_representative(cfg, power: list[dict], name: str, args: dict) -> dict | None:
    """The stored outcome whose arguments are closest to `args` (range-normalised)."""
    menu = cfg["experiments"]["menu"].get(name)
    entries = [e for e in power if e["name"] == name]
    if not menu or not entries:
        return None

    def dist(entry: dict) -> float:
        total = 0.0
        for key, (lo, hi) in menu.items():
            total += ((float(args[key]) - float(entry["args"][key])) / (hi - lo)) ** 2
        return total

    return min(entries, key=dist)
