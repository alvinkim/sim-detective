"""What the agent is allowed to see (spec 7.2, 7.3): sampled rows and block summaries.

Nothing here reads the planted cause, the regime name or the true state.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from simdet.sim.profiles import constant_blocks

ROW_COLUMNS = ["t_s", "I_A", "V_meas", "T_meas", "V_pred", "resid_mV"]
HISTORY_COLUMNS = ["t_start", "t_end", "I_A"]
BLOCK_COLUMNS = [
    "t_start", "t_end", "I_A", "resid_mean_mV", "resid_std_mV",
    "resid_first5s_mV", "resid_last5s_mV", "T_meas_mean", "T_meas_last",
]


def _row_indices(current: np.ndarray, start: int, end: int, max_rows: int, edge: int) -> np.ndarray:
    """Evenly spaced samples plus `edge` samples on each side of every current change."""
    must: set[int] = set()
    for a, _ in constant_blocks(current, start, end)[1:]:
        must.update(range(max(start, a - edge), min(end, a + edge)))
    if len(must) > max_rows:
        raise ValueError("too many current changes to fit the row limit")
    even = np.linspace(start, end - 1, max(max_rows - len(must), 0)).round().astype(int)
    return np.array(sorted(must.union(even.tolist())), dtype=int)


def segment_view(cfg, seg, start: int | None = None, end: int | None = None) -> dict:
    """rows + blocks for samples [start, end) of a segment (default: everything logged)."""
    start = seg.visible_from if start is None else start
    end = seg.n if end is None else end
    sc = cfg["scenario"]
    resid_mv = seg.resid * 1e3
    idx = _row_indices(seg.current, start, end, int(sc["max_rows"]), int(sc["edge_samples"]))
    rows = [
        [int(k), round(float(seg.current[k]), 2), round(float(seg.v_meas[k]), 5),
         round(float(seg.t_meas[k]), 3), round(float(seg.v_pred[k]), 5), round(float(resid_mv[k]), 3)]
        for k in idx
    ]
    blocks = []
    for a, b in constant_blocks(seg.current, start, end):
        r = resid_mv[a:b]
        t = seg.t_meas[a:b]
        blocks.append([
            int(a), int(b), round(float(seg.current[a]), 2),
            round(float(r.mean()), 3), round(float(r.std()), 3),
            round(float(r[:5].mean()), 3), round(float(r[-5:].mean()), 3),
            round(float(t.mean()), 3), round(float(t[-1]), 3),
        ])
    return {
        "rows": {"columns": ROW_COLUMNS, "data": rows},
        "blocks": {"columns": BLOCK_COLUMNS, "data": blocks},
    }


def history_view(seg) -> dict:
    """The current applied before logging started, as constant-current blocks. The
    current is measured exactly and the oracle uses it, so the agent gets it too; the
    voltage and temperature of that time stay hidden."""
    data = [[int(a), int(b), round(float(seg.current[a]), 2)]
            for a, b in constant_blocks(seg.current, 0, seg.visible_from)]
    return {"columns": HISTORY_COLUMNS, "data": data}


def public_scenario(cfg, scenario_id: str, world) -> dict:
    def part(seg) -> dict:
        return {"history": history_view(seg), **segment_view(cfg, seg)}

    return {"id": scenario_id, "baseline": part(world.baseline), "current": part(world.current)}


def list_ids(public_dir: str | Path) -> list[str]:
    return sorted(p.stem for p in Path(public_dir).glob("*.json"))


def load_public(public_dir: str | Path, scenario_id: str) -> dict:
    with open(Path(public_dir) / f"{scenario_id}.json", encoding="utf-8") as f:
        return json.load(f)
