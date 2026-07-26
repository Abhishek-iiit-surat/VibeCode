"""
The provider-agnostic seam.

litellm.completion() always returns an OpenAI-shaped response regardless of
which backend (Anthropic, OpenAI, ...) actually served it. Nothing outside
this module should read response.choices[...] or a tool_call's raw
.function.arguments JSON string directly — normalize_response() converts
that wire format into these plain dataclasses once, right after the API
call returns, and everything downstream (loop.py, pricing_hook.py) works
with these instead.
"""

import json
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class AgentResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end"  # "tool_use" | "end"
    raw_assistant_message: dict = field(default_factory=dict)


def normalize_response(response) -> AgentResponse:
    """Convert a litellm.completion() response into an AgentResponse."""
    message = response.choices[0].message
    raw_tool_calls = message.tool_calls or []

    tool_calls = [
        ToolCall(id=tc.id, name=tc.function.name, input=json.loads(tc.function.arguments or "{}"))
        for tc in raw_tool_calls
    ]

    return AgentResponse(
        text=message.content or "",
        tool_calls=tool_calls,
        stop_reason="tool_use" if tool_calls else "end",
        raw_assistant_message=message.model_dump(),
    )


def build_tool_result_message(tool_call_id: str, content: str, is_error: bool = False) -> dict:
    """The message appended to history after a tool executes.

    is_error has no dedicated OpenAI-format field — both providers just
    convey failure via the content text — so it's accepted for call-site
    symmetry with ToolResult but not encoded separately here.
    """
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}


def normalize_usage(usage) -> dict:
    """Convert a litellm usage object into the field names PricingTracker expects."""
    if usage is None:
        return {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}
    prompt_tokens_details = getattr(usage, "prompt_tokens_details", None)
    cache_read = getattr(prompt_tokens_details, "cached_tokens", 0) if prompt_tokens_details else 0
    return {
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "cache_read_tokens": cache_read or getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cache_write_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }
