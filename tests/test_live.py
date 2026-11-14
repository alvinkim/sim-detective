"""Real API call. Excluded by default; run with `pytest -m live` and ANTHROPIC_API_KEY set."""

import os

import pytest

from simdet.agent.client import Budget, ClaudeClient
from simdet.agent.runner import run_episode


@pytest.mark.live
def test_one_real_episode(cfg, scenario_set, tmp_path):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY is not set")
    client = ClaudeClient("claude-haiku-5-5", cfg, tmp_path / "cache", Budget(0.50))
    public = next(iter(scenario_set["publics"].values()))
    record = run_episode(client, cfg, public, "A")
    assert record["status"] == "answered", record["invalid_reason"]
    assert record["usage"]["input_tokens"] > 0 and record["cost_usd"] > 0


@pytest.mark.live
@pytest.mark.parametrize("model", ["claude-haiku-5-5", "claude-sonnet-5-5"])
@pytest.mark.parametrize("display", [None, "summarized"])
def test_condition_b_and_thinking_display(cfg, scenario_set, tmp_path, model, display):
    """Multi-turn path (tool results and thinking blocks sent back) on both models, with
    and without the thinking summary. Run before the pilot; costs a few cents."""
    import copy

    from simdet.config import Config
    from simdet.scenario.env import load_env

    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY is not set")
    raw = copy.deepcopy(cfg.raw)
    raw["agent"]["thinking_display"] = display
    local = Config(raw)
    private = next(p for p in scenario_set["privates"] if not p["identifiable"])
    client = ClaudeClient(model, local, tmp_path / "cache", Budget(0.50))
    record = run_episode(client, local, scenario_set["publics"][private["id"]], "B",
                         load_env(local, scenario_set["private_dir"], private["id"]))
    assert record["status"] == "answered", record["invalid_reason"]
    kinds = {b["type"] for r in record["responses"] for b in r["content"]}
    if display == "summarized":
        texts = [b.get("thinking", "") for r in record["responses"] for b in r["content"] if b["type"] == "thinking"]
        assert any(texts), f"no thinking summary came back (block types: {kinds})"
