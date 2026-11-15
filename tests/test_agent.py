"""Client (cache, budget) and runner (answer format, experiment limits) with fake models."""

import pytest

from simdet.agent.client import Budget, BudgetExceeded, ClaudeClient
from simdet.agent.runner import run_episode
from simdet.agent.tools import validate_submit
from simdet.scenario.env import load_env

MODEL = "claude-haiku-5-5"
GOOD = {"verdict": "identified", "cause": "soc_offset", "confidence": 0.7,
        "next_experiment": {"name": "none", "args": {}}, "rationale": "x"}


class FakeSend:
    def __init__(self, input_tokens=1_000_000, output_tokens=0):
        self.calls = 0
        self.usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}

    def __call__(self, request):
        self.calls += 1
        return {"model": request["model"], "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "hi"}], "usage": self.usage}


def client_with(cfg, tmp_path, send, limit=50.0):
    return ClaudeClient(MODEL, cfg, tmp_path / "cache", Budget(limit), send=send)


def test_cache_hit_does_not_call_the_api(cfg, tmp_path):
    send = FakeSend()
    client = client_with(cfg, tmp_path, send)
    msgs = [{"role": "user", "content": "q"}]
    first = client.create("sys", msgs, [])
    again = client.create("sys", msgs, [])
    assert send.calls == 1
    assert not first["cached"] and again["cached"] and again["cost_usd"] == 0.0
    assert again["content"] == first["content"]
    client.create("sys", msgs, [], repeat_index=1)  # repeat_index is part of the key
    assert send.calls == 2
    assert not any("api_key" in p.read_text() for p in (tmp_path / "cache").glob("*.json"))


def test_cost_uses_configured_prices(cfg, tmp_path):
    client = client_with(cfg, tmp_path, FakeSend(input_tokens=2_000_000, output_tokens=1_000_000))
    price = cfg["agent"]["pricing_usd_per_mtok"][MODEL]
    assert client.create("s", [{"role": "user", "content": "q"}], [])["cost_usd"] == pytest.approx(
        2 * price["input"] + price["output"])


def test_budget_stops_further_calls(cfg, tmp_path):
    send = FakeSend(input_tokens=10_000_000)  # $1 per call at the haiku price
    client = client_with(cfg, tmp_path, send, limit=1.5)
    for i in range(2):
        client.create("s", [{"role": "user", "content": f"q{i}"}], [])
    with pytest.raises(BudgetExceeded):
        client.create("s", [{"role": "user", "content": "q2"}], [])
    assert send.calls == 2
    client.create("s", [{"role": "user", "content": "q0"}], [])  # cached answers stay available


class Scripted:
    """Replays a list of tool calls (or None for a reply without a tool call)."""

    name = "scripted"

    def __init__(self, script):
        self.script = list(script)

    def create(self, system, messages, tools, repeat_index=0, **_):
        step = self.script.pop(0)
        content = ([{"type": "text", "text": "no tool"}] if step is None else
                   [{"type": "tool_use", "id": f"t{len(messages)}", "name": step[0], "input": step[1]}])
        return {"model": self.name, "content": content, "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1}, "cached": False,
                "cost_usd": 0.0, "request_sha": None}


def episode(cfg, scenario_set, script, condition="A"):
    private = next(p for p in scenario_set["privates"] if not p["identifiable"])
    env = load_env(cfg, scenario_set["private_dir"], private["id"]) if condition == "B" else None
    return run_episode(Scripted(script), cfg, scenario_set["publics"][private["id"]], condition, env)


def test_valid_answer_is_stored_unchanged(cfg, scenario_set):
    record = episode(cfg, scenario_set, [("submit", GOOD)])
    assert record["status"] == "answered" and record["answer"] == GOOD
    assert record["format_violations"] == 0 and record["n_calls"] == 1


def test_one_format_violation_is_retried_then_accepted(cfg, scenario_set):
    bad = {**GOOD, "cause": None}
    record = episode(cfg, scenario_set, [("submit", bad), ("submit", GOOD)])
    assert record["status"] == "answered" and record["format_violations"] == 1


def test_second_format_violation_is_invalid(cfg, scenario_set):
    bad = {**GOOD, "verdict": "not_identifiable", "candidates": ["soc_offset"]}
    record = episode(cfg, scenario_set, [("submit", bad), ("submit", bad), ("submit", GOOD)])
    assert record["status"] == "invalid" and record["answer"] is None and record["n_calls"] == 2


def test_no_tool_call_twice_is_invalid(cfg, scenario_set):
    record = episode(cfg, scenario_set, [None, None])
    assert record["status"] == "invalid"


def test_experiment_rules(cfg, scenario_set):
    script = [
        ("run_experiment", {"name": "rest_test", "args": {"duration_s": 10}}),      # out of range
        ("run_experiment", {"name": "cc_run", "args": {"current_a": 25, "duration_s": 1800}}),  # SOC guard
        ("run_experiment", {"name": "rest_test", "args": {"duration_s": 600}}),
        ("run_experiment", {"name": "pulse_test", "args": {"amplitude_a": 10, "duration_s": 30}}),
        ("run_experiment", {"name": "rest_test", "args": {"duration_s": 600}}),     # third: refused
        ("submit", GOOD),
    ]
    record = episode(cfg, scenario_set, script, condition="B")
    assert record["status"] == "answered"
    assert [e["name"] for e in record["experiments"]] == ["rest_test", "pulse_test"]
    results = [m["content"][0] for m in record["transcript"] if m["role"] == "user"]
    assert [bool(r.get("is_error")) for r in results] == [True, True, False, False, True, False]
    assert "not counted" in results[0]["content"]


def test_run_experiment_is_not_a_tool_in_condition_a(cfg, scenario_set):
    record = episode(cfg, scenario_set, [
        ("run_experiment", {"name": "rest_test", "args": {"duration_s": 600}}), ("submit", GOOD)])
    assert record["experiments"] == [] and record["format_violations"] == 1


@pytest.mark.parametrize("change", [
    {"verdict": "maybe"}, {"cause": "aging"}, {"confidence": 1.5}, {"confidence": "high"},
    {"next_experiment": {"name": "none"}}, {"next_experiment": {"name": "x", "args": {}}},
    {"rationale": None}, {"candidates": ["bogus", "soc_offset"]},
])
def test_validate_submit_rejects(change):
    assert validate_submit({**GOOD, **change})


def test_validate_submit_accepts_abstention():
    assert not validate_submit({**GOOD, "verdict": "not_identifiable", "cause": None,
                                "candidates": ["soc_offset", "structural_change"]})


def test_thinking_display_is_part_of_the_request(cfg, tmp_path):
    import copy

    from simdet.config import Config

    seen = []

    def send(request):
        seen.append(request)
        return FakeSend()(request)

    off, on = copy.deepcopy(cfg.raw), copy.deepcopy(cfg.raw)
    off["agent"]["thinking_display"] = None
    on["agent"]["thinking_display"] = "summarized"
    msgs = [{"role": "user", "content": "q"}]
    ClaudeClient(MODEL, Config(off), tmp_path / "c", Budget(50), send=send).create("s", msgs, [])
    ClaudeClient(MODEL, Config(on), tmp_path / "c", Budget(50), send=send).create("s", msgs, [])
    assert [r["thinking_display"] for r in seen] == [None, "summarized"]  # second is not a cache hit


def test_parallel_run_writes_the_same_file_as_sequential(scenario_set, tmp_path, monkeypatch):
    import shutil

    from simdet.cli import main

    shutil.copytree(scenario_set["root"], tmp_path / "scenarios")
    monkeypatch.setenv("SIMDET_ROOT", str(tmp_path))
    models = "mock_always_claim,mock_always_abstain,mock_oracle,mock_random_experiment"
    for workers in ("1", "4"):
        assert main(["run", "--model", models, "--condition", "A,B", "--limit", "16",
                     "--repeats", "2", "--workers", workers]) == 0
    first, second = sorted(d for d in (tmp_path / "results").iterdir() if d.is_dir())
    a = (first / "episodes.jsonl").read_bytes()
    assert a == (second / "episodes.jsonl").read_bytes() and a.count(b"\n") == 4 * 2 * 16 * 2
    assert (first / "summary.md").read_text(encoding="utf-8") == (second / "summary.md").read_text(encoding="utf-8").replace(second.name, first.name)
