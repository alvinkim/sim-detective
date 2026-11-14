"""Mock models (spec 8.5). They speak the same response format as the real client, so
the whole pipeline runs without the API."""

from __future__ import annotations

import json
from pathlib import Path

MOCK_NAMES = ("mock_always_claim", "mock_always_abstain", "mock_oracle")
BASELINES = ("mock_always_claim", "mock_always_abstain")
_ZERO = {"input_tokens": 0, "output_tokens": 0,
         "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
_FAULTS = ["r0_increase", "soc_offset", "temp_sensor_bias", "structural_change"]


def _reply(name: str, tool: str, tool_input: dict, n_messages: int) -> dict:
    return {
        "model": name,
        "content": [{"type": "tool_use", "id": f"mock_{n_messages}", "name": tool, "input": tool_input}],
        "stop_reason": "tool_use",
        "usage": dict(_ZERO),
        "cached": False,
        "cost_usd": 0.0,
        "list_cost_usd": 0.0,
        "request_sha": None,
    }


def _can_experiment(tools: list, messages: list) -> bool:
    """True on the first turn of a condition-B episode."""
    return any(t["name"] == "run_experiment" for t in tools) and len(messages) == 1


class MockAlwaysClaim:
    name = "mock_always_claim"

    def create(self, system, messages, tools, repeat_index=0, **_) -> dict:
        return _reply(self.name, "submit", {
            "verdict": "identified", "cause": "r0_increase", "candidates": ["r0_increase"],
            "confidence": 1.0, "next_experiment": {"name": "none", "args": {}},
            "rationale": "mock: always claims r0_increase",
        }, len(messages))


class MockAlwaysAbstain:
    name = "mock_always_abstain"
    _rest = {"duration_s": 5400}

    def create(self, system, messages, tools, repeat_index=0, **_) -> dict:
        if _can_experiment(tools, messages):
            return _reply(self.name, "run_experiment",
                          {"name": "rest_test", "args": dict(self._rest)}, len(messages))
        return _reply(self.name, "submit", {
            "verdict": "not_identifiable", "cause": None, "candidates": list(_FAULTS),
            "confidence": 0.5, "next_experiment": {"name": "rest_test", "args": dict(self._rest)},
            "rationale": "mock: always abstains",
        }, len(messages))


class MockOracle:
    """Reads the private file and answers what the oracle says. Only for checking the
    grader; this is the one agent-side class allowed to open scenarios/private/."""

    name = "mock_oracle"

    def __init__(self, private_dir: str | Path):
        self._dir = Path(private_dir)

    def create(self, system, messages, tools, repeat_index=0, scenario_id=None, **_) -> dict:
        with open(self._dir / f"{scenario_id}.json", encoding="utf-8") as f:
            private = json.load(f)
        resolving = next(
            (e for e in private["experiment_power"] if e["class"] == "resolving"), None
        )
        ran_experiment = len(messages) > 1
        if not private["identifiable"] and resolving and _can_experiment(tools, messages):
            return _reply(self.name, "run_experiment",
                          {"name": resolving["name"], "args": resolving["args"]}, len(messages))
        if private["identifiable"] or ran_experiment:
            answer = {
                "verdict": "identified", "cause": private["cause_label"],
                "candidates": [private["cause_label"]], "confidence": 1.0,
                "next_experiment": {"name": "none", "args": {}},
                "rationale": "mock: read from the private file",
            }
        else:
            from simdet.sim.faults import LABELS

            nxt = ({"name": resolving["name"], "args": resolving["args"]} if resolving
                   else {"name": "none", "args": {}})
            answer = {
                "verdict": "not_identifiable", "cause": None,
                "candidates": [LABELS[c] for c in private["consistent_set"]],
                "confidence": 1.0, "next_experiment": nxt,
                "rationale": "mock: read from the private file",
            }
        return _reply(self.name, "submit", answer, len(messages))


def make_mock(name: str, private_dir: str | Path | None = None):
    if name == "mock_always_claim":
        return MockAlwaysClaim()
    if name == "mock_always_abstain":
        return MockAlwaysAbstain()
    if name == "mock_oracle":
        return MockOracle(private_dir)
    raise ValueError(f"unknown mock model: {name}")
