"""
Tools available to the Agent reasoning loop: FileRead, FileWrite, Bash
(client-executed) and WebSearch (Anthropic server-executed).
"""

from pathlib import Path
from typing import Optional

from vibecode.tools.base import Tool, ToolResult
from vibecode.tools.bash import BashTool
from vibecode.tools.file_read import FileReadTool
from vibecode.tools.file_write import FileWriteTool
from vibecode.tools.registry import ToolRegistry

WEB_SEARCH_SCHEMA = {"type": "web_search_20260209", "name": "web_search"}


def build_default_registry(project_root: Path, extra_tools: Optional[list] = None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(FileReadTool(project_root))
    registry.register(FileWriteTool(project_root))
    registry.register(BashTool(project_root))
    registry.register_server_tool(WEB_SEARCH_SCHEMA)

    for tool in extra_tools or []:
        registry.register(tool)

    return registry


__all__ = ["Tool", "ToolResult", "ToolRegistry", "build_default_registry"]
