"""Episode grading (spec 9.1, 9.2). The submitted answer is used as is."""

from __future__ import annotations

from simdet.oracle.experiments import classify, narrowed, nearest_representative, oracle_of
from simdet.scenario.world import world_from_private
from simdet.sim.faults import CAUSE_OF_LABEL
from simdet.sim.profiles import validate_experiment

VERDICTS = ("correct", "wrong_cause", "over_abstain", "correct_abstain", "overclaim",
            "invalid", "ungraded")
EXPERIMENT_CLASSES = ("resolving", "partial", "useless", "inconclusive", "none", "invalid_args")


def grade_episode(cfg, record: dict, private: dict) -> dict:
    """Judge one episode against the oracle.

    In condition B the oracle is recomputed on the data the agent actually collected
    (the experiments are replayed on the stored true system); experiments can only
    narrow the initial set. If a remaining candidate ends in the gray zone the episode
    is 'ungraded'.
    """
    cause = private["cause"]
    initial_set = tuple(private["consistent_set"])
    final_set, final_status, first_class = initial_set, "ok", None

    if record["experiments"]:
        world = world_from_private(cfg, private)
        for i, e in enumerate(record["experiments"]):
            world.run_experiment(e["name"], e["args"])
            final_set, final_status = narrowed(initial_set, oracle_of(cfg, world), cause)
            if i == 0:
                first_class = classify(initial_set, final_set, final_status, cause)
    final_identifiable = final_status == "ok" and len(final_set) == 1

    answer = record.get("answer") or {}
    said_cause = CAUSE_OF_LABEL.get(answer.get("cause"))
    claimed = answer.get("verdict") == "identified"
    lucky = None
    if record["status"] != "answered":
        verdict = "invalid"
    elif final_status != "ok":
        verdict = "ungraded"
    elif final_identifiable:
        verdict = ("correct" if said_cause == cause else "wrong_cause") if claimed else "over_abstain"
    elif claimed:
        verdict, lucky = "overclaim", said_cause == cause
    else:
        verdict = "correct_abstain"

    experiment_class = None
    if not private["identifiable"]:
        if record["condition"] == "B":
            experiment_class = first_class or "none"
        else:
            experiment_class = _proposed_class(cfg, private, answer.get("next_experiment"))

    return {
        "verdict": verdict,
        "lucky": lucky,
        "planted": cause,
        "regime": private["regime"],
        "answered": ("abstain" if not claimed else said_cause) if record["status"] == "answered" else None,
        "initial_identifiable": private["identifiable"],
        "final_identifiable": final_identifiable,
        "final_set": list(final_set),
        "final_status": final_status,
        "experiment_class": experiment_class,
        "n_experiments": len(record["experiments"]),
        "confidence": answer.get("confidence"),
    }


def _proposed_class(cfg, private: dict, proposal) -> str:
    """Condition A: class of the stored representative run closest to the proposal."""
    if not isinstance(proposal, dict) or proposal.get("name") in (None, "none"):
        return "none"
    try:
        args = validate_experiment(cfg, proposal["name"], proposal.get("args"))
    except ValueError:
        return "invalid_args"
    entry = nearest_representative(cfg, private["experiment_power"], proposal["name"], args)
    if entry is None or entry["class"] == "rejected":
        return "invalid_args"
    return entry["class"]
