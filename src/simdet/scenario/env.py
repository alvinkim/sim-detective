"""The experiment environment handed to the agent harness.

It owns the hidden world; the harness only gets `run()`, which returns the same
rows/blocks view as the scenario files.
"""

from __future__ import annotations

import json
from pathlib import Path

from simdet.scenario.public_view import segment_view
from simdet.scenario.world import World, world_from_private


def load_private(private_dir: str | Path, scenario_id: str) -> dict:
    with open(Path(private_dir) / f"{scenario_id}.json", encoding="utf-8") as f:
        return json.load(f)


class ScenarioEnv:
    def __init__(self, cfg, world: World):
        self._cfg = cfg
        self._world = world

    def run(self, name, args) -> dict:
        """Run an experiment on the true system. Raises ValueError (message safe to show
        to the agent) if the request is refused."""
        start, end = self._world.run_experiment(name, args)
        return segment_view(self._cfg, self._world.current, start, end)

    @property
    def experiments(self) -> list[dict]:
        return list(self._world.experiments)


def load_env(cfg, private_dir: str | Path, scenario_id: str) -> ScenarioEnv:
    return ScenarioEnv(cfg, world_from_private(cfg, load_private(private_dir, scenario_id)))
