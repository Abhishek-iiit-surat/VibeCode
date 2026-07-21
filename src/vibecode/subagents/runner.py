"""
Generic sub-agent runner: a thin wrapper over the same Agent reasoning loop,
given a restricted tool set and no memory. Used by the Task tool for
subagent_type="general-purpose".
"""

from typing import Any, Optional

from vibecode.agent.client import SUBAGENT_MODEL
from vibecode.agent.loop import run_agent_loop
from vibecode.tools.registry import ToolRegistry

SUBAGENT_SYSTEM_PROMPT = (
    "You are a focused sub-agent delegated a specific task. Complete it using "
    "your available tools and report back concisely — the parent agent only "
    "sees your final text response, not your intermediate steps."
)

RESEARCHER_SYSTEM_PROMPT = (
    "You are a focused research sub-agent delegated a natural-language "
    "question. Use web_search to find candidate pages, judge from the "
    "titles/snippets which ones are actually likely to answer the question, "
    "then use web_fetch on those (not every result) to read their full "
    "content. Report back only the distilled answer — facts, figures, and "
    "quotes relevant to the question — not raw page content or your search "
    "process. The parent agent only sees your final text response."
)

SUBAGENT_MAX_TURNS = 10


def run_subagent(
    prompt: str,
    registry: ToolRegistry,
    client,
    on_usage: Optional[Any] = None,
    system_prompt: str = SUBAGENT_SYSTEM_PROMPT,
) -> str:
    result = run_agent_loop(
        task=prompt,
        tools=registry,
        system_prompt=system_prompt,
        client=client,
        model=SUBAGENT_MODEL,
        max_turns=SUBAGENT_MAX_TURNS,
        on_usage=on_usage,
    )
    return result.final_text
