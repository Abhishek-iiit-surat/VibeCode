"""
The Agent reasoning loop: the central piece of the architecture.

Calls Claude with the current tool registry, executes any tool_use blocks
(through hooks, if provided), feeds results back, and repeats until Claude
stops calling tools. Standard Anthropic Messages-API manual tool-use loop.
"""

from dataclasses import dataclass
from typing import Any, Optional

import anthropic

from vibecode.agent.client import DEFAULT_MODEL
from vibecode.tools.base import ToolResult
from vibecode.tools.registry import ToolRegistry
from vibecode.ui.display import show_tool_call, show_tool_result


@dataclass
class AgentResult:
    messages: list
    final_text: str


def run_agent_loop(
    task: str,
    tools: ToolRegistry,
    system_prompt: str,
    client: anthropic.Anthropic,
    hooks: Optional[Any] = None,
    memory: Optional[Any] = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8192,
    max_turns: int = 50,
) -> AgentResult:
    messages = (memory.load() if memory else []) + [{"role": "user", "content": task}]

    response = None
    for _ in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=tools.list_schemas(),
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use" or not tools.is_client_tool(block.name):
                continue  # server-tool blocks (web_search) are already resolved in-response

            tool_input = block.input
            show_tool_call(block.name, tool_input)

            if hooks is not None:
                decision = hooks.before_tool_call(block.name, tool_input)
                if decision.block:
                    result = ToolResult(content=decision.reason or "Blocked by hook.", is_error=True)
                else:
                    result = tools.execute(block.name, decision.modified_input or tool_input)
                    result = hooks.after_tool_call(block.name, tool_input, result) or result
            else:
                result = tools.execute(block.name, tool_input)

            show_tool_result(result)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result.content,
                    "is_error": result.is_error,
                }
            )

        messages.append({"role": "user", "content": tool_results})

        if memory:
            memory.save(messages)
            if memory.should_compact(messages):
                messages = memory.compact(messages, client, model)

    final_text = ""
    if response is not None:
        final_text = next((b.text for b in response.content if b.type == "text"), "")

    return AgentResult(messages=messages, final_text=final_text)
