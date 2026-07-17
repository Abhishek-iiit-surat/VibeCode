"""
Generic sub-agent runner: a thin wrapper over the same Agent reasoning loop,
given a restricted tool set and no memory. Used by the Task tool for
subagent_type="general-purpose".
"""

from vibecode.agent.loop import run_agent_loop
from vibecode.tools.registry import ToolRegistry

SUBAGENT_SYSTEM_PROMPT = (
    "You are a focused sub-agent delegated a specific task. Complete it using "
    "your available tools and report back concisely — the parent agent only "
    "sees your final text response, not your intermediate steps."
)


def run_subagent(prompt: str, registry: ToolRegistry, client, model: str, max_turns: int = 15) -> str:
    result = run_agent_loop(
        task=prompt,
        tools=registry,
        system_prompt=SUBAGENT_SYSTEM_PROMPT,
        client=client,
        model=model,
        max_turns=max_turns,
    )
    return result.final_text
