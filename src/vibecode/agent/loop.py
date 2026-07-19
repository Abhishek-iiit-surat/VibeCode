"""
The Agent reasoning loop: the central piece of the architecture.

Calls the model (via litellm, provider-agnostic) with the current tool
registry, executes any requested tool calls (through hooks, if provided),
feeds results back, and repeats until the model stops calling tools.
Standard OpenAI-style manual tool-use loop — litellm normalizes every
provider's wire format to this shape, and normalize_response() is where
that shape gets converted into the plain ToolCall/AgentResponse dataclasses
the rest of this function works with.
"""

from dataclasses import dataclass
from typing import Any, Optional

from vibecode.agent.client import DEFAULT_MODEL
from vibecode.agent.response import build_tool_result_message, normalize_response, normalize_usage
from vibecode.tools.base import ToolResult
from vibecode.tools.registry import ToolRegistry
from vibecode.ui.display import show_tool_call, show_tool_result, thinking_status


@dataclass
class AgentResult:
    messages: list
    final_text: str


def run_agent_loop(
    task: str,
    tools: ToolRegistry,
    system_prompt: str,
    client: Any,
    hooks: Optional[Any] = None,
    memory: Optional[Any] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8192,
    max_turns: int = 20,
    on_usage: Optional[Any] = None,
) -> AgentResult:
    messages = (memory.load() if memory else []) + [{"role": "user", "content": task}]
    system_message = {"role": "system", "content": system_prompt}
    tool_schemas = tools.list_schemas()

    # Anthropic-only prompt-caching hint. litellm passes extra_headers /
    # cache_control through for anthropic/* models; other providers don't
    # understand it, so it's gated on the model prefix rather than sent
    # unconditionally.
    is_anthropic = model.startswith("anthropic/")
    if is_anthropic:
        system_message["cache_control"] = {"type": "ephemeral"}
        if tool_schemas:
            tool_schemas[-1] = {**tool_schemas[-1], "cache_control": {"type": "ephemeral"}}

    agent_response = None
    with thinking_status("Thinking…") as status:
        for _ in range(max_turns):
            status.update("Thinking…")
            raw_response = client.completion(
                model=model,
                max_tokens=max_tokens,
                messages=[system_message] + messages,
                tools=tool_schemas or None,
            )
            agent_response = normalize_response(raw_response)

            if on_usage is not None:
                on_usage(model, normalize_usage(getattr(raw_response, "usage", None)))

            messages.append(agent_response.raw_assistant_message)

            if agent_response.stop_reason != "tool_use":
                break

            for tool_call in agent_response.tool_calls:
                if not tools.is_client_tool(tool_call.name):
                    continue

                tool_input = tool_call.input
                status.stop()
                show_tool_call(tool_call.name, tool_input)

                if hooks is not None:
                    decision = hooks.before_tool_call(tool_call.name, tool_input)
                    if decision.block:
                        result = ToolResult(content=decision.reason or "Blocked by hook.", is_error=True)
                    else:
                        result = tools.execute(tool_call.name, decision.modified_input or tool_input)
                        result = hooks.after_tool_call(tool_call.name, tool_input, result) or result
                else:
                    result = tools.execute(tool_call.name, tool_input)

                show_tool_result(result)
                status.start()

                messages.append(build_tool_result_message(tool_call.id, result.content, result.is_error))

            if memory:
                memory.save(messages)
                if memory.should_compact(messages):
                    messages = memory.compact(messages, client, model)

    final_text = agent_response.text if agent_response is not None else ""

    return AgentResult(messages=messages, final_text=final_text)
