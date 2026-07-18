"""
Tools available to the Agent reasoning loop: FileRead, FileWrite, Bash, Search
(client-executed) and WebSearch (Anthropic server-executed).
"""

from pathlib import Path
from typing import Optional

from vibecode.tools.base import Tool, ToolResult
from vibecode.tools.bash import BashTool
from vibecode.tools.file_read import FileReadTool
from vibecode.tools.file_write import FileWriteTool
from vibecode.tools.registry import ToolRegistry
from vibecode.tools.search import SearchTool

WEB_SEARCH_SCHEMA = {"type": "web_search_20260209", "name": "web_search"}


def build_default_registry(
    project_root: Path,
    client=None,
    model: Optional[str] = None,
    extra_tools: Optional[list] = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(FileReadTool(project_root))
    registry.register(FileWriteTool(project_root))
    registry.register(BashTool(project_root))
    registry.register(SearchTool(project_root))
    registry.register_server_tool(WEB_SEARCH_SCHEMA)

    if client is not None and model is not None:
        # Imported here (not at module top) to avoid a tools/subagents import
        # cycle — by this point vibecode.tools.registry/.base are fully loaded.
        from vibecode.subagents.task_tool import TaskTool

        registry.register(TaskTool(registry, client, model))

    for tool in extra_tools or []:
        registry.register(tool)

    return registry


__all__ = ["Tool", "ToolResult", "ToolRegistry", "build_default_registry"]
