"""Claude API client with a response cache, cost accounting and a budget (spec 8.4)."""

from __future__ import annotations

import hashlib
import json
import os
import random
import time
from pathlib import Path
from typing import Any, Callable

USAGE_KEYS = (
    "input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
)


class BudgetExceeded(RuntimeError):
    """Cumulative spend passed budget_usd. Nothing more is sent."""


def request_key(request: dict) -> str:
    """SHA-256 of the whole request, including repeat_index."""
    blob = json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _sdk_send(max_retries: int, backoff_base_s: float, sleep: Callable[[float], None]):
    """Build the function that sends one request through the official SDK."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; it is the only place the key is read from.")
    sdk = anthropic.Anthropic(api_key=api_key, max_retries=0)  # retries are handled below

    def send(request: dict) -> dict:
        kwargs: dict[str, Any] = {
            "model": request["model"],
            "max_tokens": request["max_tokens"],
            "system": request["system"],
            "messages": request["messages"],
            "tools": request["tools"],
            "cache_control": {"type": "ephemeral"},  # reuse the long data prefix across turns
        }
        if request.get("effort"):
            kwargs["output_config"] = {"effort": request["effort"]}
        for attempt in range(max_retries + 1):
            try:
                raw = sdk.messages.create(**kwargs).to_dict()
                raw["_retries"] = attempt
                return raw
            except anthropic.RateLimitError:
                if attempt == max_retries:
                    raise
            except anthropic.APIStatusError as e:
                if e.status_code < 500 or attempt == max_retries:
                    raise
            except anthropic.APIConnectionError:
                if attempt == max_retries:
                    raise
            sleep(backoff_base_s * 2**attempt + random.uniform(0, 1))
        raise AssertionError("unreachable")

    return send


class ClaudeClient:
    """One model. `send` can be replaced by a fake for tests."""

    def __init__(
        self,
        model: str,
        cfg,
        cache_dir: str | Path,
        budget: "Budget | None" = None,
        send: Callable[[dict], dict] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        agent = cfg["agent"]
        self.name = model
        self.model = model
        self.max_tokens = int(agent["max_tokens"])
        self.effort = agent.get("effort")
        self.price = agent["pricing_usd_per_mtok"][model]
        self.cache_dir = Path(cache_dir)
        self.budget = budget or Budget(float(agent["budget_usd"]))
        self._send = send or _sdk_send(int(agent["max_retries"]), float(agent["backoff_base_s"]), sleep)

    def cost_of(self, usage: dict) -> float:
        u = {k: usage.get(k) or 0 for k in USAGE_KEYS}
        return (
            u["input_tokens"] * self.price["input"]
            + u["cache_creation_input_tokens"] * self.price["cache_write"]
            + u["cache_read_input_tokens"] * self.price["cache_read"]
            + u["output_tokens"] * self.price["output"]
        ) / 1e6

    def create(self, system: str, messages: list, tools: list, repeat_index: int = 0, **_) -> dict:
        request = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "effort": self.effort,
            "system": system,
            "messages": messages,
            "tools": tools,
            "repeat_index": repeat_index,
        }
        key = request_key(request)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                stored = json.load(f)
            return {**stored, "cached": True, "cost_usd": 0.0, "request_sha": key}

        self.budget.check()
        raw = self._send(request)
        usage = {k: (raw.get("usage") or {}).get(k) or 0 for k in USAGE_KEYS}
        response = {
            "model": raw.get("model", self.model),
            "content": raw.get("content", []),
            "stop_reason": raw.get("stop_reason"),
            "usage": usage,
            "list_cost_usd": self.cost_of(usage),
            "retries": raw.get("_retries", 0),
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False)
        os.replace(tmp, path)
        self.budget.add(response["list_cost_usd"])
        return {**response, "cached": False, "cost_usd": response["list_cost_usd"], "request_sha": key}


class Budget:
    """Spend shared by all clients of a run."""

    def __init__(self, limit_usd: float):
        self.limit_usd = limit_usd
        self.spent_usd = 0.0

    def add(self, cost: float) -> None:
        self.spent_usd += cost

    def check(self) -> None:
        if self.spent_usd > self.limit_usd:
            raise BudgetExceeded(
                f"spent ${self.spent_usd:.2f}, over the budget of ${self.limit_usd:.2f}"
            )
