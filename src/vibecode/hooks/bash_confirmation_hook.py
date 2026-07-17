"""
BashConfirmationHook: pauses before every `bash` tool call and asks the user
to confirm the exact command. Declining blocks the call — the one genuinely
blocking example hook in the default set.
"""

import click

from vibecode.hooks.base import Hook, HookDecision


class BashConfirmationHook(Hook):
    def before_tool_call(self, tool_name: str, tool_input: dict) -> HookDecision:
        if tool_name != "bash":
            return HookDecision()

        command = tool_input.get("command", "")
        click.secho(f"\n$ {command}", fg="yellow")
        if click.confirm("Run this command?", default=True):
            return HookDecision()
        return HookDecision(block=True, reason="User declined to run this command.")
