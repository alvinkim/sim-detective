"""Configuration loading and repository paths."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from simdet.sim.cell import CellParams


def repo_root() -> Path:
    """Repository root. SIMDET_ROOT overrides it (used by tests)."""
    env = os.environ.get("SIMDET_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "default.yaml"


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any]

    @property
    def cell(self) -> CellParams:
        return CellParams(**{k: float(v) for k, v in self.raw["cell"].items()})

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def physics_sha(self) -> str:
        """Hash of everything that changes simulated data or oracle verdicts."""
        keys = ("cell", "sim", "regimes", "faults", "oracle", "experiments", "scenario")
        blob = json.dumps({k: self.raw[k] for k in keys}, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_config(path: str | Path | None = None) -> Config:
    with open(path or DEFAULT_CONFIG, encoding="utf-8") as f:
        return Config(yaml.safe_load(f))


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def public(self) -> Path:
        return self.root / "scenarios" / "public"

    @property
    def private(self) -> Path:
        return self.root / "scenarios" / "private"

    @property
    def scenarios(self) -> Path:
        return self.root / "scenarios"

    @property
    def results(self) -> Path:
        return self.root / "results"

    @property
    def cache(self) -> Path:
        return self.root / "results" / "cache"


def paths(root: str | Path | None = None) -> Paths:
    return Paths(Path(root) if root else repo_root())
