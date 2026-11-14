"""Episode grading (spec 9.1, 9.2). The submitted answer is used as is."""

from __future__ import annotations

from simdet.oracle.experiments import classify, narrowed, nearest_representative, oracle_of
from simdet.scenario.world import world_from_private
from simdet.sim.faults import CAUSE_OF_LABEL
from simdet.sim.profiles import experiment_duration_s, validate_experiment

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

    # Quality of an abstention (not part of the verdict): how the listed candidates
    # compare with the oracle's set on the data the agent had.
    abstention = None
    if record["status"] == "answered" and not claimed:
        listed = {CAUSE_OF_LABEL[c] for c in answer.get("candidates", [])}
        abstention = {"n_candidates": len(listed), "exact": listed == set(final_set),
                      "contains_planted": cause in listed}

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
        "size": private["magnitude"]["size"],
        "answered": ("abstain" if not claimed else said_cause) if record["status"] == "answered" else None,
        "initial_identifiable": private["identifiable"],
        "final_identifiable": final_identifiable,
        "final_set": list(final_set),
        "final_status": final_status,
        "experiment_class": experiment_class,
        "experiment_duration_s": _chosen_duration(cfg, record, answer.get("next_experiment")),
        "abstention": abstention,
        "n_experiments": len(record["experiments"]),
        "confidence": answer.get("confidence"),
    }


def _chosen_duration(cfg, record: dict, proposal) -> int | None:
    """Length of the experiment the agent chose: the first one it ran (condition B) or
    the one it proposed (condition A). None if there is none or its arguments are invalid."""
    if record["condition"] == "B":
        chosen = record["experiments"][0] if record["experiments"] else None
    else:
        chosen = proposal if isinstance(proposal, dict) and proposal.get("name") not in (None, "none") else None
    if not chosen:
        return None
    try:
        return experiment_duration_s(cfg, chosen["name"], validate_experiment(cfg, chosen["name"], chosen.get("args")))
    except ValueError:
        return None


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
