"""
The Task tool: lets the main Agent delegate a subtask to a Sub-Agent.

subagent_type="general-purpose" spins up a nested reasoning loop with a
restricted tool subset (no Task itself — one level of delegation only, no
memory). subagent_type="large-file-editor" instead runs the specialized
AST-chunked edit/validate/refine procedure for files over ~200 lines.
"""

from vibecode.subagents.large_file_editor import run_large_file_editor
from vibecode.subagents.runner import run_subagent
from vibecode.tools.base import Tool, ToolResult
from vibecode.tools.registry import ToolRegistry

GENERAL_PURPOSE_TOOLS = ["file_read", "file_write", "bash", "web_search"]


class TaskTool(Tool):
    name = "Task"
    description = (
        "Delegate a subtask to a sub-agent running its own reasoning loop. "
        "Use subagent_type='large-file-editor' for editing a single file over "
        "~200 lines (it performs a targeted AST-chunked edit rather than "
        "rewriting the whole file). Use subagent_type='general-purpose' for "
        "any other self-contained subtask (a restricted set of tools; no "
        "further delegation)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "Short (3-5 word) task description"},
            "prompt": {"type": "string", "description": "The full task for the sub-agent to perform"},
            "subagent_type": {
                "type": "string",
                "enum": ["general-purpose", "large-file-editor"],
            },
            "file_path": {
                "type": "string",
                "description": "Required when subagent_type is 'large-file-editor'",
            },
        },
        "required": ["description", "prompt", "subagent_type"],
    }

    def __init__(self, registry: ToolRegistry, client, model: str):
        self.registry = registry
        self.client = client
        self.model = model

    def execute(self, description, prompt, subagent_type, file_path=None) -> ToolResult:
        if subagent_type == "large-file-editor":
            if not file_path:
                return ToolResult(
                    content="file_path is required for subagent_type='large-file-editor'",
                    is_error=True,
                )
            text = run_large_file_editor(file_path, prompt, self.client, self.model)
            return ToolResult(content=text)

        if subagent_type == "general-purpose":
            subset = self.registry.subset(GENERAL_PURPOSE_TOOLS)
            text = run_subagent(prompt, subset, self.client, self.model)
            return ToolResult(content=text)

        return ToolResult(content=f"Unknown subagent_type: {subagent_type}", is_error=True)
