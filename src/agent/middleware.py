"""Middleware helpers for validation and retries."""
from __future__ import annotations

import json
from typing import Any, Callable

from tenacity import retry, stop_after_attempt, wait_exponential


def validate_json(schema: Callable[[dict[str, Any]], Any], payload: str) -> Any:
    """Validate payload against a callable schema."""
    data = json.loads(payload)
    return schema(data)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def safe_tool_call(tool: Callable[..., Any], **kwargs: Any) -> Any:
    """Execute a tool with retry on ValueError."""
    try:
        return tool(**kwargs)
    except ValueError as exc:
        raise exc


__all__ = ["validate_json", "safe_tool_call"]
