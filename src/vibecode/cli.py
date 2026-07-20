from pathlib import Path

import click

from vibecode.agent.client import DEFAULT_MODEL, get_client
from vibecode.agent.loop import run_agent_loop
from vibecode.agent.system_prompt import build_system_prompt
from vibecode.context.loader import load_project_context
from vibecode.hooks import HookManager
from vibecode.hooks.bash_confirmation_hook import BashConfirmationHook
from vibecode.hooks.logging_hook import LoggingHook
from vibecode.hooks.pricing_hook import PricingTracker
from vibecode.memory.mem0_store import Mem0Store
from vibecode.tools import build_default_registry
from vibecode.ui.display import show_agent_text, show_banner, show_cost, prompt_task

MAIN_AGENT_MAX_TURNS = 20


@click.command()
@click.argument("task", required=False)
@click.option(
    "--model",
    default=None,
    help="Override the model, as a litellm id, e.g. 'anthropic/claude-sonnet-4-6' "
    "or 'openai/gpt-4.1' (default: anthropic/claude-sonnet-4-6)",
)
def cli(task, model):
    """VibeCode: an agentic coding assistant."""
    project_root = Path.cwd()
    client = get_client()
    chosen_model = model or DEFAULT_MODEL
    pricing = PricingTracker()
    registry = build_default_registry(
        project_root, client=client, model=chosen_model, on_usage=pricing.on_usage
    )
    hooks = HookManager([LoggingHook(project_root), BashConfirmationHook()])
    memory = Mem0Store(project_root)
    context = load_project_context(project_root)
    system_prompt = build_system_prompt(context, registry.tool_names())

    show_banner()
    first_task = task
    while True:
        if first_task is not None:
            task = first_task
            first_task = None
        else:
            task = prompt_task()
        if task.lower() in ("quit", "exit", ""):
            break
        pricing.reset()
        result = run_agent_loop(
            task,
            registry,
            system_prompt,
            client,
            hooks=hooks,
            memory=memory,
            model=chosen_model,
            max_turns=MAIN_AGENT_MAX_TURNS,
            on_usage=pricing.on_usage,
        )
        show_agent_text(result.final_text)
        show_cost(pricing.summary())


if __name__ == "__main__":
    cli()
