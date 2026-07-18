"""
The Task tool: lets the main Agent delegate a subtask to a Sub-Agent.

subagent_type="general-purpose" spins up a nested reasoning loop with a
restricted tool subset (no Task itself — one level of delegation only, no
memory). Delegate by task shape, not file size: open-ended exploration or a
self-contained subtask belongs in a sub-agent, so its back-and-forth stays out
of the main agent's context and only the final summary comes back. A direct,
already-located edit (of any file size) should just use file_read/file_write
in the current loop — spawning a sub-agent for it adds a round trip for
nothing.
"""

from vibecode.subagents.runner import run_subagent
from vibecode.tools.base import Tool, ToolResult
from vibecode.tools.registry import ToolRegistry

GENERAL_PURPOSE_TOOLS = ["file_read", "file_write", "bash", "search", "web_search"]


class TaskTool(Tool):
    name = "Task"
    description = (
        "Delegate a subtask to a sub-agent (subagent_type='general-purpose') "
        "running its own isolated reasoning loop with a restricted tool set "
        "(no further delegation). Only its final text response comes back to "
        "you, not its intermediate steps — use it for open-ended exploration "
        "or self-contained subtasks you don't want cluttering your own "
        "context. Don't use it for a direct edit to a file you've already "
        "located, regardless of the file's size — just call file_read/"
        "file_write yourself."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "Short (3-5 word) task description"},
            "prompt": {"type": "string", "description": "The full task for the sub-agent to perform"},
            "subagent_type": {
                "type": "string",
                "enum": ["general-purpose"],
            },
        },
        "required": ["description", "prompt", "subagent_type"],
    }

    def __init__(self, registry: ToolRegistry, client, model: str):
        self.registry = registry
        self.client = client
        self.model = model

    def execute(self, description, prompt, subagent_type) -> ToolResult:
        if subagent_type == "general-purpose":
            subset = self.registry.subset(GENERAL_PURPOSE_TOOLS)
            text = run_subagent(prompt, subset, self.client, self.model)
            return ToolResult(content=text)

        return ToolResult(content=f"Unknown subagent_type: {subagent_type}", is_error=True)
