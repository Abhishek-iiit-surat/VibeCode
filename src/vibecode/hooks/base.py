"""
Hook interface: pre/post interception points around every tool call.

Hooks sit between the Agent and its Tools (logging, confirmation gates,
policy checks, ...) — distinct from a tool's own built-in behavior. For
example FileWrite's diff+approval gate is intrinsic to the tool itself, not
a hook, so it can't be silently disabled by removing a hook.
"""

from abc import ABC
from dataclasses import dataclass
from typing import Optional

from vibecode.tools.base import ToolResult


@dataclass
class HookDecision:
    block: bool = False
    reason: Optional[str] = None
    modified_input: Optional[dict] = None
    modified_result: Optional[ToolResult] = None


class Hook(ABC):
    def before_tool_call(self, tool_name: str, tool_input: dict) -> HookDecision:
        return HookDecision()

    def after_tool_call(self, tool_name: str, tool_input: dict, result: ToolResult) -> HookDecision:
        return HookDecision()
