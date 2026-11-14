import pytest

from simdet.agent.mock import make_mock
from simdet.agent.runner import run_episode
from simdet.scenario.env import load_env
from simdet.score import stats
from simdet.score.grade import grade_episode


@pytest.fixture(scope="module")
def graded(cfg, scenario_set):
    """Every mock on every scenario in both conditions."""
    out = {}
    for name in ("mock_oracle", "mock_always_claim", "mock_always_abstain"):
        client = make_mock(name, scenario_set["private_dir"])
        for condition in ("A", "B"):
            episodes = []
            for private in scenario_set["privates"]:
                env = load_env(cfg, scenario_set["private_dir"], private["id"]) if condition == "B" else None
                record = run_episode(client, cfg, scenario_set["publics"][private["id"]], condition, env)
                record["grade"] = grade_episode(cfg, record, private)
                episodes.append(record)
            out[(name, condition)] = episodes
    return out


def metric(episodes, name):
    return stats.rate(stats.per_scenario(episodes, name))["rate"]


@pytest.mark.parametrize("condition", ["A", "B"])
def test_mock_oracle_gets_full_marks(graded, condition):
    episodes = graded[("mock_oracle", condition)]
    assert {e["grade"]["verdict"] for e in episodes} <= {"correct", "correct_abstain"}
    assert metric(episodes, "accuracy") == 1.0
    assert metric(episodes, "over_abstain") == 0.0
    assert metric(episodes, "overclaim") in (0.0, None)  # None: nothing left unidentifiable in B
    assert metric(episodes, "experiment") == 1.0
    assert metric(episodes, "invalid") == 0.0


def test_mock_oracle_resolves_everything_in_condition_b(graded):
    assert all(e["grade"]["final_identifiable"] for e in graded[("mock_oracle", "B")])


@pytest.mark.parametrize("condition", ["A", "B"])
def test_always_claim_overclaims_every_time(graded, condition):
    assert metric(graded[("mock_always_claim", condition)], "overclaim") == 1.0


@pytest.mark.parametrize("condition", ["A", "B"])
def test_always_abstain_over_abstains_every_time(graded, condition):
    episodes = graded[("mock_always_abstain", condition)]
    assert metric(episodes, "over_abstain") == 1.0
    assert metric(episodes, "accuracy") == 0.0


def test_lucky_flag(graded):
    lucky = [e["grade"]["lucky"] for e in graded[("mock_always_claim", "A")]
             if e["grade"]["verdict"] == "overclaim"]
    assert lucky and not any(lucky)  # r0_increase is never in a non-identifiable set here


def test_experiments_never_widen_the_set(graded):
    for e in graded[("mock_always_abstain", "B")]:
        assert e["grade"]["n_experiments"] == 1
        assert e["grade"]["verdict"] != "ungraded"
