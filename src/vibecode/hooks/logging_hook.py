"""
LoggingHook: append one JSON line per tool-call event. Pure observability —
never blocks, never rewrites input or output.
"""

import json
import time
from pathlib import Path

from vibecode.hooks.base import Hook, HookDecision
from vibecode.tools.base import ToolResult


class LoggingHook(Hook):
    def __init__(self, project_root: Path):
        self.log_path = project_root / ".vibecode" / "logs" / "tool_calls.jsonl"

    def _append(self, event: dict) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as f:
            f.write(json.dumps(event) + "\n")

    def before_tool_call(self, tool_name: str, tool_input: dict) -> HookDecision:
        self._append(
            {
                "event": "before_tool_call",
                "tool": tool_name,
                "input": tool_input,
                "timestamp": time.time(),
            }
        )
        return HookDecision()

    def after_tool_call(self, tool_name: str, tool_input: dict, result: ToolResult) -> HookDecision:
        self._append(
            {
                "event": "after_tool_call",
                "tool": tool_name,
                "input": tool_input,
                "is_error": result.is_error,
                "timestamp": time.time(),
            }
        )
        return HookDecision()
