"""
The Task tool: lets the main Agent delegate a subtask to a Sub-Agent.

subagent_type="general-purpose" or "researcher" spins up a nested reasoning
loop with a restricted tool subset (no Task itself — one level of delegation
only, no memory). Delegate by task shape, not file size: open-ended
exploration or a self-contained subtask belongs in a sub-agent, so its
back-and-forth stays out of the main agent's context and only the final
summary comes back. A direct, already-located edit (of any file size) should
just use file_read/file_write in the current loop — spawning a sub-agent for
it adds a round trip for nothing.

"researcher" is for open-web questions: give it a natural-language prompt
describing what you want to know, and it will call web_search for candidate
URLs, pick the relevant ones itself, call web_fetch on each, and return only
the distilled answer — no raw page content ever reaches the main agent's
context.
"""

from typing import Any, Optional

from vibecode.subagents.runner import RESEARCHER_SYSTEM_PROMPT, SUBAGENT_SYSTEM_PROMPT, run_subagent
from vibecode.tools.base import Tool, ToolResult
from vibecode.tools.registry import ToolRegistry

GENERAL_PURPOSE_TOOLS = ["file_read", "file_write", "bash", "search"]
RESEARCHER_TOOLS = ["web_search", "web_fetch"]

_SUBAGENT_CONFIG = {
    "general-purpose": (GENERAL_PURPOSE_TOOLS, SUBAGENT_SYSTEM_PROMPT),
    "researcher": (RESEARCHER_TOOLS, RESEARCHER_SYSTEM_PROMPT),
}


class TaskTool(Tool):
    name = "Task"
    description = (
        "Delegate a subtask to a sub-agent running its own isolated reasoning "
        "loop with a restricted tool set (no further delegation). Only its "
        "final text response comes back to you, not its intermediate steps. "
        "subagent_type='general-purpose' for open-ended exploration or "
        "self-contained file/code subtasks you don't want cluttering your own "
        "context — don't use it for a direct edit to a file you've already "
        "located, regardless of size, just call file_read/file_write yourself. "
        "subagent_type='researcher' for open-web questions: give it a "
        "natural-language prompt and it will search the web, fetch and read "
        "the relevant pages itself, and return only the distilled answer."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "Short (3-5 word) task description"},
            "prompt": {"type": "string", "description": "The full task for the sub-agent to perform"},
            "subagent_type": {
                "type": "string",
                "enum": ["general-purpose", "researcher"],
            },
        },
        "required": ["description", "prompt", "subagent_type"],
    }

    def __init__(self, registry: ToolRegistry, client, on_usage: Optional[Any] = None):
        self.registry = registry
        self.client = client
        self.on_usage = on_usage

    def execute(self, description, prompt, subagent_type) -> ToolResult:
        config = _SUBAGENT_CONFIG.get(subagent_type)
        if config is None:
            return ToolResult(content=f"Unknown subagent_type: {subagent_type}", is_error=True)

        tool_names, system_prompt = config
        subset = self.registry.subset(tool_names)
        text = run_subagent(prompt, subset, self.client, on_usage=self.on_usage, system_prompt=system_prompt)
        return ToolResult(content=text)
