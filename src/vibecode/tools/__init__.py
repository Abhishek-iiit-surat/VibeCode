"""
Tools available to the Agent reasoning loop: FileRead, FileWrite, Bash, Search
— all client-executed.
"""

from pathlib import Path
from typing import Any, Optional

from vibecode.tools.base import Tool, ToolResult
from vibecode.tools.bash import BashTool
from vibecode.tools.file_read import FileReadTool
from vibecode.tools.file_write import FileWriteTool
from vibecode.tools.registry import ToolRegistry
from vibecode.tools.search import SearchTool
from vibecode.tools.web_fetch import WebFetchTool
from vibecode.tools.web_search import WebSearchTool


def build_default_registry(
    project_root: Path,
    client=None,
    model: Optional[str] = None,
    extra_tools: Optional[list] = None,
    on_usage: Optional[Any] = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(FileReadTool(project_root))
    registry.register(FileWriteTool(project_root))
    registry.register(BashTool(project_root))
    registry.register(SearchTool(project_root))
    registry.register(WebSearchTool())
    registry.register(WebFetchTool())

    if client is not None and model is not None:
        # Imported here (not at module top) to avoid a tools/subagents import
        # cycle — by this point vibecode.tools.registry/.base are fully loaded.
        # TaskTool no longer takes `model`: sub-agents always run on
        # SUBAGENT_MODEL (agent/client.py), independent of the main agent's model.
        from vibecode.subagents.task_tool import TaskTool

        registry.register(TaskTool(registry, client, on_usage=on_usage))

    for tool in extra_tools or []:
        registry.register(tool)

    return registry


__all__ = ["Tool", "ToolResult", "ToolRegistry", "build_default_registry"]
