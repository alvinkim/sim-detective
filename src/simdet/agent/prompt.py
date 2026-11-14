"""Prompt assembly (spec 8.1). The wording lives in prompt_<version>.txt; a changed prompt
gets a new version file and the version is recorded with every result."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Template

_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def _sections(version: str) -> dict[str, str]:
    text = (_DIR / f"prompt_{version}.txt").read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    name = None
    for line in text.splitlines():
        if line.startswith("[[") and line.endswith("]]"):
            name = line[2:-2]
            sections[name] = ""
        elif name is not None:
            sections[name] += line + "\n"
    return {k: v.strip() for k, v in sections.items()}


def _num(x) -> str:
    return f"{float(x):g}"


def build_system_prompt(cfg, condition: str, version: str) -> str:
    """System prompt for a condition. It does not depend on the scenario."""
    s = _sections(version)
    exp = cfg["experiments"]
    menu = exp["menu"]
    block = Template(s[f"CONDITION_{condition}"]).substitute(
        max_experiments=exp["max_per_episode"]
    )
    values = {k: _num(v) for k, v in cfg["cell"].items()}
    values.update(
        soc_init=_num(cfg["sim"]["soc_init"]),
        pulse_amp_lo=_num(menu["pulse_test"]["amplitude_a"][0]),
        pulse_amp_hi=_num(menu["pulse_test"]["amplitude_a"][1]),
        pulse_dur_lo=_num(menu["pulse_test"]["duration_s"][0]),
        pulse_dur_hi=_num(menu["pulse_test"]["duration_s"][1]),
        pulse_pre=_num(exp["pulse_pre_rest_s"]),
        pulse_post=_num(exp["pulse_post_rest_s"]),
        rest_lo=_num(menu["rest_test"]["duration_s"][0]),
        rest_hi=_num(menu["rest_test"]["duration_s"][1]),
        cc_cur_lo=_num(menu["cc_run"]["current_a"][0]),
        cc_cur_hi=_num(menu["cc_run"]["current_a"][1]),
        cc_dur_lo=_num(menu["cc_run"]["duration_s"][0]),
        cc_dur_hi=_num(menu["cc_run"]["duration_s"][1]),
        condition_block=block,
    )
    return Template(s["SYSTEM"]).substitute(values)


def table_csv(table: dict) -> str:
    lines = [",".join(table["columns"])]
    lines += [",".join(_num(v) if isinstance(v, float) else str(v) for v in row) for row in table["data"]]
    return "\n".join(lines)


def build_user_message(public: dict, version: str) -> str:
    """The scenario data: rows and blocks of the baseline and current segments."""
    return Template(_sections(version)["USER"]).substitute(
        scenario_id=public["id"],
        baseline_rows=table_csv(public["baseline"]["rows"]),
        baseline_blocks=table_csv(public["baseline"]["blocks"]),
        current_rows=table_csv(public["current"]["rows"]),
        current_blocks=table_csv(public["current"]["blocks"]),
    )


def build_experiment_result(view: dict, name: str, args: dict, index: int, cfg, version: str) -> str:
    return Template(_sections(version)["EXPERIMENT_RESULT"]).substitute(
        index=index,
        max_experiments=cfg["experiments"]["max_per_episode"],
        name=name,
        args=", ".join(f"{k}={_num(v)}" for k, v in args.items()),
        rows=table_csv(view["rows"]),
        blocks=table_csv(view["blocks"]),
    )
