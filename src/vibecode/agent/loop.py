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

import os
from dataclasses import dataclass
from typing import Any, Optional

from vibecode.agent.client import DEFAULT_MODEL, SUBAGENT_MODEL
from vibecode.agent.response import build_tool_result_message, normalize_response, normalize_usage
from vibecode.tools.base import ToolResult
from vibecode.tools.registry import ToolRegistry
from vibecode.ui.display import show_tool_call, show_tool_result, thinking_status

# Once the in-loop message list exceeds this many turns, older turns get
# summarized into one condensed message so a long-running query doesn't keep
# resending its full tool-call/result history on every model call. Override
# via .env — VIBECODE_COMPACT_AFTER_TURNS=20 — same pattern as
# MEM0_RECALL_LIMIT for the mem0 recall size.
COMPACT_AFTER_TURNS = int(os.getenv("VIBECODE_COMPACT_AFTER_TURNS", "12"))
# Turns kept verbatim (uncompacted) right before the current point in the loop.
KEEP_RECENT_TURNS = 4


@dataclass
class AgentResult:
    messages: list
    final_text: str


def _render_message(m: dict) -> str:
    """Flatten one message into a plain transcript line for summarization.

    Assistant tool_use turns carry the call in a separate `tool_calls` field
    with `content` left empty/None, so reading `content` alone would silently
    drop every tool call from the summary — render tool_calls explicitly too.
    """
    role = m.get("role", "?")
    parts = []
    if m.get("content"):
        parts.append(str(m["content"]))
    for tc in m.get("tool_calls") or []:
        fn = tc.get("function", {})
        parts.append(f"[called {fn.get('name')}({fn.get('arguments')})]")
    return f"{role}: {' '.join(parts)}"


def _compact_messages(messages: list, client: Any) -> list:
    """Summarize every message except the system-level task message and the
    most recent KEEP_RECENT_TURNS turns into one condensed user message.
    Keeps the loop's own message list bounded on long-running queries instead
    of resending the full tool-call/result history every turn."""
    if len(messages) <= KEEP_RECENT_TURNS + 1:
        return messages

    head, task_message = messages[1:-KEEP_RECENT_TURNS], messages[0]
    recent = messages[-KEEP_RECENT_TURNS:]
    if not head:
        return messages

    transcript = "\n".join(_render_message(m) for m in head)
    summary_response = client.completion(
        model=SUBAGENT_MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "Summarize this agent transcript concisely, keeping any facts, "
                "file paths, decisions, or tool results that later steps might still need.",
            },
            {"role": "user", "content": transcript},
        ],
    )
    summary_text = normalize_response(summary_response).text
    summary_message = {"role": "user", "content": f"[Earlier conversation summary]\n{summary_text}"}
    return [task_message, summary_message] + recent


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
    messages = (memory.load(task) if memory else []) + [{"role": "user", "content": task}]
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
            if len(messages) > COMPACT_AFTER_TURNS:
                status.update("Compacting context…")
                messages = _compact_messages(messages, client)

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

    final_text = agent_response.text if agent_response is not None else ""

    if memory:
        memory.finalize(messages, client, model)

    return AgentResult(messages=messages, final_text=final_text)
