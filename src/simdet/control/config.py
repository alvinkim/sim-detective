"""Configuration of the control pilot: config/control.yaml plus the cell of config/default.yaml."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from simdet.config import load_config
from simdet.sim.cell import CellParams

CONTROL_CONFIG = Path(__file__).resolve().parents[3] / "config" / "control.yaml"
TEMPLATES = Path(__file__).resolve().parent / "templates.yaml"


@dataclass(frozen=True)
class ControlConfig:
    raw: dict[str, Any]
    cell: CellParams  # nominal cell = the twin

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def plant_cell(self, condition: str) -> CellParams:
        """Plant of a twin condition: R0 x (1 + delta) and h_th x (1 - delta)."""
        delta = float(self.raw["conditions"][condition])
        return replace(self.cell, r0_ref=self.cell.r0_ref * (1 + delta),
                       h_th=self.cell.h_th * (1 - delta))


def load_control_config(path: str | Path | None = None) -> ControlConfig:
    with open(path or CONTROL_CONFIG, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ControlConfig(raw, load_config().cell)


def load_templates(path: str | Path | None = None) -> dict[str, list[str]]:
    with open(path or TEMPLATES, encoding="utf-8") as f:
        return yaml.safe_load(f)
