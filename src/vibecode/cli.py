from pathlib import Path

import click

from vibecode.agent.client import DEFAULT_MODEL, get_client
from vibecode.agent.loop import run_agent_loop
from vibecode.hooks import HookManager
from vibecode.hooks.bash_confirmation_hook import BashConfirmationHook
from vibecode.hooks.logging_hook import LoggingHook
from vibecode.tools import build_default_registry
from vibecode.ui.display import show_agent_text

BASE_SYSTEM_PROMPT = (
    "You are VibeCode, an agentic coding assistant running in a terminal. "
    "You have tools to read files, write files, run shell commands, and "
    "delegate to sub-agents via Task (use subagent_type='large-file-editor' "
    "for files over ~200 lines). The file_write tool always shows the user a "
    "diff and asks for approval before anything is written to disk — never "
    "try to bypass that."
)


@click.command()
@click.argument("task", required=False)
@click.option("--model", default=None, help="Override the Claude model (default: claude-opus-4-8)")
def cli(task, model):
    """VibeCode: an agentic coding assistant."""
    project_root = Path.cwd()
    client = get_client()
    chosen_model = model or DEFAULT_MODEL
    registry = build_default_registry(project_root, client=client, model=chosen_model)
    hooks = HookManager([LoggingHook(project_root), BashConfirmationHook()])

    if task:
        result = run_agent_loop(task, registry, BASE_SYSTEM_PROMPT, client, hooks=hooks, model=chosen_model)
        show_agent_text(result.final_text)
        return

    click.echo("VibeCode — describe a task, or 'quit' to exit.")
    while True:
        task = click.prompt("›").strip()
        if task.lower() in ("quit", "exit", ""):
            break
        result = run_agent_loop(task, registry, BASE_SYSTEM_PROMPT, client, hooks=hooks, model=chosen_model)
        show_agent_text(result.final_text)


if __name__ == "__main__":
    cli()
