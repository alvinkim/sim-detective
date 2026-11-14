"""Run one episode: prompt -> tool calls -> submitted answer (spec 8.2, 8.3)."""

from __future__ import annotations

import json

from simdet.agent.client import USAGE_KEYS
from simdet.agent.prompt import build_experiment_result, build_system_prompt, build_user_message
from simdet.agent.tools import ExperimentEnv, tools_for, validate_submit

NO_TOOL_CALL = "No tool call was received. Give your final answer by calling the `submit` tool."


def _tool_result(tool_use_id: str, text: str, is_error: bool = False) -> dict:
    block = {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}
    if is_error:
        block["is_error"] = True
    return block


def run_episode(
    client,
    cfg,
    public: dict,
    condition: str,
    env: ExperimentEnv | None = None,
    repeat_index: int = 0,
) -> dict:
    """Returns the raw episode record. The answer is stored exactly as submitted.

    status is 'answered' or 'invalid'. A format violation (no tool call, an unknown
    tool, or a `submit` that breaks the answer format) is sent back once; a second one
    ends the episode as invalid.
    """
    version = cfg["agent"]["prompt_version"]
    max_experiments = int(cfg["experiments"]["max_per_episode"]) if condition == "B" else 0
    system = build_system_prompt(cfg, condition, version)
    tools = tools_for(condition)
    messages: list[dict] = [{"role": "user", "content": build_user_message(public, version)}]

    responses: list[dict] = []
    experiments: list[dict] = []
    usage = {k: 0 for k in USAGE_KEYS}
    cost = 0.0
    violations = 0
    answer = None
    status = "invalid"
    reason = "call limit reached"

    for _ in range(int(cfg["agent"]["max_calls_per_episode"])):
        resp = client.create(system=system, messages=messages, tools=tools,
                             repeat_index=repeat_index, scenario_id=public["id"])
        responses.append({k: resp.get(k) for k in
                          ("model", "content", "stop_reason", "usage", "cached", "cost_usd", "request_sha", "retries", "elapsed_s")})
        for k in USAGE_KEYS:
            usage[k] += resp["usage"].get(k) or 0
        cost += resp["cost_usd"]
        messages.append({"role": "assistant", "content": resp["content"]})

        calls = [b for b in resp["content"] if b.get("type") == "tool_use"]
        if not calls:
            violations += 1
            if violations > 1:
                reason = f"no tool call (stop_reason={resp.get('stop_reason')})"
                break
            messages.append({"role": "user", "content": NO_TOOL_CALL})
            continue

        results = []
        for call in calls:
            if answer is not None:
                results.append(_tool_result(call["id"], "Ignored: the answer was already submitted.", True))
            elif call["name"] == "submit":
                errors = validate_submit(call["input"])
                if not errors:
                    answer = call["input"]
                    results.append(_tool_result(call["id"], "Answer received."))
                else:
                    violations += 1
                    reason = "answer format: " + "; ".join(errors)
                    results.append(_tool_result(
                        call["id"], "Invalid answer format: " + "; ".join(errors) + ". Call `submit` again.", True))
            elif call["name"] == "run_experiment" and condition == "B":
                results.append(_run_experiment(call, env, experiments, max_experiments, cfg, version))
            else:
                violations += 1
                reason = f"unknown tool '{call['name']}'"
                results.append(_tool_result(call["id"], f"Unknown tool '{call['name']}'.", True))
        messages.append({"role": "user", "content": results})
        if answer is not None:
            status, reason = "answered", None
            break
        if violations > 1:
            break

    return {
        "scenario_id": public["id"],
        "model": client.name,
        "condition": condition,
        "repeat_index": repeat_index,
        "prompt_version": version,
        "status": status,
        "invalid_reason": reason,
        "answer": answer,
        "format_violations": violations,
        "experiments": experiments,
        "n_calls": len(responses),
        "usage": usage,
        "cost_usd": cost,
        "elapsed_s": round(sum(r.get("elapsed_s") or 0.0 for r in responses), 3),
        # The first user message is the scenario's public file rendered by the prompt
        # version above; it is not repeated here.
        "transcript": messages[1:],
        "responses": responses,
    }


def _run_experiment(call: dict, env, experiments: list, max_experiments: int, cfg, version: str) -> dict:
    if len(experiments) >= max_experiments:
        return _tool_result(
            call["id"], f"No experiments left (limit {max_experiments}). Call `submit`.", True)
    request = call["input"] if isinstance(call["input"], dict) else {}
    try:
        view = env.run(request.get("name"), request.get("args"))
    except ValueError as e:  # refused: bad arguments or SOC guard; not counted
        return _tool_result(call["id"], f"Experiment refused: {e} This request was not counted.", True)
    done = env.experiments[-1]
    experiments.append(done)
    return _tool_result(call["id"], build_experiment_result(
        view, done["name"], done["args"], len(experiments), cfg, version))


def dumps(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"))
