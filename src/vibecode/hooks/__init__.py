"""
HookManager: runs the registered hooks around each tool call.

The Agent loop only talks to HookManager, never to individual Hooks — it
calls before_tool_call() to get a HookDecision (which may block the call or
rewrite its input) and after_tool_call() to get the (possibly rewritten)
ToolResult.
"""

from vibecode.hooks.base import Hook, HookDecision
from vibecode.tools.base import ToolResult


class HookManager:
    def __init__(self, hooks: list[Hook]):
        self.hooks = hooks

    def before_tool_call(self, tool_name: str, tool_input: dict) -> HookDecision:
        for hook in self.hooks:
            decision = hook.before_tool_call(tool_name, tool_input)
            if decision.block:
                return decision
            if decision.modified_input is not None:
                tool_input = decision.modified_input
        return HookDecision(modified_input=tool_input)

    def after_tool_call(self, tool_name: str, tool_input: dict, result: ToolResult) -> ToolResult:
        for hook in self.hooks:
            decision = hook.after_tool_call(tool_name, tool_input, result)
            if decision.modified_result is not None:
                result = decision.modified_result
        return result


__all__ = ["Hook", "HookDecision", "HookManager"]
