"""Nothing private reaches the agent (spec 12, 14)."""

import ast
import json
import re
from pathlib import Path

import simdet.agent
from simdet.agent.prompt import build_experiment_result, build_system_prompt, build_user_message
from simdet.agent.tools import CAUSE_LABELS
from simdet.scenario.env import load_env
from simdet.sim.faults import LABELS

AGENT_DIR = Path(simdet.agent.__file__).parent
REGIME_WORD = re.compile(r"\b(CC|DYN)\b")


def test_prompts_do_not_leak(cfg, scenario_set):
    version = cfg["agent"]["prompt_version"]
    for condition in ("A", "B"):
        system = build_system_prompt(cfg, condition, version)  # takes no scenario at all
        assert "identifiab" not in system.lower()
        assert not REGIME_WORD.search(system)
    for private in scenario_set["privates"]:
        user = build_user_message(scenario_set["publics"][private["id"]], version)
        assert "identifiab" not in user.lower()
        assert private["regime"] not in REGIME_WORD.findall(user)
        assert not REGIME_WORD.search(user)
        assert all(label not in user for label in CAUSE_LABELS)
        assert private["cause_label"] not in user


def test_experiment_results_do_not_leak(cfg, scenario_set):
    private = next(p for p in scenario_set["privates"] if not p["identifiable"])
    env = load_env(cfg, scenario_set["private_dir"], private["id"])
    view = env.run("rest_test", {"duration_s": 600})
    text = build_experiment_result(view, "rest_test", {"duration_s": 600.0}, 1, cfg,
                                   cfg["agent"]["prompt_version"])
    assert all(label not in text for label in CAUSE_LABELS)
    assert not REGIME_WORD.search(text) and "identifiab" not in text.lower()


def test_public_files_hold_only_id_and_data(scenario_set):
    for path in scenario_set["public_dir"].glob("*.json"):
        public = json.loads(path.read_text(encoding="utf-8"))
        assert set(public) == {"id", "baseline", "current"}
        assert re.fullmatch(r"[0-9a-f]{8}", public["id"])
        for part in ("baseline", "current"):
            assert set(public[part]) == {"history", "rows", "blocks"}
            assert public[part]["history"]["columns"] == ["t_start", "t_end", "I_A"]
            assert len(public[part]["rows"]["data"]) <= 240


def test_history_gives_only_the_current_before_logging(cfg, scenario_set):
    version = cfg["agent"]["prompt_version"]
    assert version == "v2"
    for private in scenario_set["privates"]:
        public = scenario_set["publics"][private["id"]]
        user = build_user_message(public, version)
        for part in ("baseline", "current"):
            history = public[part]["history"]["data"]
            first_row = public[part]["rows"]["data"][0][0]
            if private["regime"] == "CC":
                assert history == [[0, 2400, 25.0]] and first_row == 2400
            else:
                assert history == [] and first_row == 0
        assert ("0,2400,25" in user) == (private["regime"] == "CC")
        assert ("history:\nnone" in user) == (private["regime"] == "DYN")


def test_prompt_v1_is_kept_and_still_renders(cfg, scenario_set):
    public = next(iter(scenario_set["publics"].values()))
    assert "history" not in build_user_message(public, "v1")
    assert "history" not in build_system_prompt(cfg, "A", "v1")
    assert "history" in build_system_prompt(cfg, "A", "v2")


def test_agent_modules_do_not_touch_private_data():
    """Only mock.py (mock_oracle) may open scenarios/private or import the hidden side."""
    forbidden = ("simdet.scenario", "simdet.oracle", "simdet.score")
    for path in AGENT_DIR.glob("*.py"):
        if path.name == "mock.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert "private" not in source.lower(), path.name
        for node in ast.walk(ast.parse(source)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            assert not any(n.startswith(forbidden) for n in names), (path.name, names)
    for path in AGENT_DIR.glob("prompt_*.txt"):
        assert "private" not in path.read_text(encoding="utf-8").lower()


def test_tool_labels_match_cause_definitions():
    assert CAUSE_LABELS == list(LABELS.values())
