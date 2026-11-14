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
