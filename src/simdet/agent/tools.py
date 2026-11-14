"""The two tools the agent can call (spec 8.2, 8.3) and the answer-format check."""

from __future__ import annotations

from typing import Any, Protocol

CAUSE_LABELS = [
    "no_change", "noise_growth", "r0_increase", "soc_offset",
    "temp_sensor_bias", "structural_change",
]
VERDICTS = ["identified", "not_identifiable"]
EXPERIMENT_NAMES = ["pulse_test", "rest_test", "cc_run"]

SUBMIT_TOOL = {
    "name": "submit",
    "description": "Submit the final answer. Call this once.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": VERDICTS},
            "cause": {
                "type": ["string", "null"],
                "enum": CAUSE_LABELS + [None],
                "description": "Required when verdict is 'identified'; otherwise null.",
            },
            "candidates": {
                "type": "array",
                "items": {"type": "string", "enum": CAUSE_LABELS},
                "description": "At least two labels are required when verdict is 'not_identifiable'.",
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "next_experiment": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": EXPERIMENT_NAMES + ["none"]},
                    "args": {"type": "object"},
                },
                "required": ["name", "args"],
            },
            "rationale": {"type": "string"},
        },
        "required": ["verdict", "confidence", "next_experiment", "rationale"],
    },
}

RUN_EXPERIMENT_TOOL = {
    "name": "run_experiment",
    "description": (
        "Run one experiment on the cell, continuing from its present state. "
        "Returns rows and blocks for the new samples."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "enum": EXPERIMENT_NAMES},
            "args": {
                "type": "object",
                "description": "Arguments of the chosen experiment, e.g. {\"duration_s\": 900}.",
            },
        },
        "required": ["name", "args"],
    },
}


def tools_for(condition: str) -> list[dict]:
    return [RUN_EXPERIMENT_TOOL, SUBMIT_TOOL] if condition == "B" else [SUBMIT_TOOL]


class ExperimentEnv(Protocol):
    """Provided by the caller. The harness never sees the hidden system behind it."""

    def run(self, name: Any, args: Any) -> dict:
        """Returns {'rows': ..., 'blocks': ...}; raises ValueError if the request is refused."""


def validate_submit(args: Any) -> list[str]:
    """Format violations of a `submit` call (empty list = valid). The answer is never
    repaired: a violation is reported back once and then counted as invalid."""
    if not isinstance(args, dict):
        return ["the tool input must be an object"]
    errors = []
    verdict = args.get("verdict")
    if verdict not in VERDICTS:
        errors.append(f"verdict must be one of {VERDICTS}")
    cause = args.get("cause")
    if cause is not None and cause not in CAUSE_LABELS:
        errors.append(f"cause must be null or one of {CAUSE_LABELS}")
    candidates = args.get("candidates", [])
    if not isinstance(candidates, list) or any(c not in CAUSE_LABELS for c in candidates):
        errors.append(f"candidates must be a list of labels from {CAUSE_LABELS}")
        candidates = []
    if verdict == "identified" and cause is None:
        errors.append("cause is required when verdict is 'identified'")
    if verdict == "not_identifiable" and len(set(candidates)) < 2:
        errors.append("candidates needs at least two different labels when verdict is 'not_identifiable'")
    conf = args.get("confidence")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        errors.append("confidence must be a number between 0 and 1")
    nxt = args.get("next_experiment")
    if (
        not isinstance(nxt, dict)
        or nxt.get("name") not in EXPERIMENT_NAMES + ["none"]
        or not isinstance(nxt.get("args"), dict)
    ):
        errors.append(
            "next_experiment must be {\"name\": one of "
            f"{EXPERIMENT_NAMES + ['none']}, \"args\": object}}"
        )
    if not isinstance(args.get("rationale"), str):
        errors.append("rationale must be a string")
    return errors
