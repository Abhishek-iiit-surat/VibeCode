"""
Terminal presentation layer, built on Rich.

Centralizes the single Console instance and every piece of styled output —
banner, tool calls/results, diffs, approval prompts — plus the spinner
shown while waiting on the model or a tool.
"""

from contextlib import contextmanager

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status
from rich.syntax import Syntax
from rich.text import Text

console = Console()

_SPINNER = "star"
_ACCENT = "#E8840A"  # warm coral, evokes Claude Code's status color


def show_banner():
    """Startup banner for interactive mode."""
    console.print()
    console.print(Text("VibeCode", style=f"bold {_ACCENT}"), Text(" — agentic coding assistant", style="dim"))
    console.print(Text("Describe a task, or 'quit' to exit.", style="dim"))
    console.print()


def prompt_task() -> str:
    """Read the next task from the user with a styled prompt."""
    console.print(Text("›", style=f"bold {_ACCENT}"), end=" ")
    return console.input().strip()


@contextmanager
def thinking_status(label: str = "Thinking…"):
    """
    Spinner shown while waiting on Claude or a tool. Use `status.update(text)`
    to change the label, or pause output cleanly with a `with status.pause():`.
    """
    with Status(Text(label, style=_ACCENT), console=console, spinner=_SPINNER) as status:
        yield status


def show_diff(diff_string: str):
    """Display a unified diff in a syntax-highlighted panel."""
    syntax = Syntax(diff_string, "diff", theme="ansi_dark", background_color="default")
    console.print(Panel(syntax, title="Proposed change", border_style=_ACCENT, expand=False))


def get_approval() -> str:
    """Ask the user if they want to apply changes. Returns 'y' / 'n' / 'e'."""
    while True:
        choice = console.input(
            "[bold]Apply changes?[/bold] [green](y)es[/green] / [red](n)o[/red] / [yellow](e)dit[/yellow] "
        ).strip().lower()
        if choice in ("y", "n", "e"):
            return choice
        console.print("Please enter 'y', 'n', or 'e'", style="yellow")


def show_execution_result(result, iteration_num):
    """Show execution result with colors."""
    if result.success:
        console.print(f"\n[bold green]✓ Iteration {iteration_num}: Success![/bold green]")
        if result.stdout:
            console.print(f"Output:\n{result.stdout}")
    else:
        console.print(f"\n[bold red]✗ Iteration {iteration_num}: Failed (exit code {result.exit_code})[/bold red]")
        if result.stderr:
            console.print(f"Error:\n{result.stderr}", style="red")


def show_iteration_summary(iterations):
    """Show summary table of all iterations."""
    console.rule("Iteration summary")
    for it in iterations:
        status = "[green]✓[/green]" if it.success else "[red]✗[/red]"
        console.print(f"  Attempt {it.attempt_number}: {status} (exit code: {it.execution_result.exit_code})")
    console.rule()


def show_agent_text(text: str):
    """Display the agent's final response text for a turn, rendered as markdown."""
    if text:
        console.print()
        console.print(Markdown(text))


def show_tool_call(name: str, tool_input: dict):
    """Display a tool call the agent is about to make."""
    console.print(f"[{_ACCENT}]●[/{_ACCENT}] [bold]{name}[/bold]({_format_input(tool_input)})", style="dim")


def show_tool_result(result):
    """Display the result of a tool call, capped to a max height."""
    style = "red" if result.is_error else "bright_black"
    prefix = "✗" if result.is_error else "└─"
    console.print(f"  {prefix} {_truncate(result.content)}", style=style)


_MAX_LINES = 10
_MAX_LINE_LEN = 200


def _truncate(text: str, max_lines: int = _MAX_LINES) -> str:
    """Shared height/width cap for anything that echoes tool/file content
    to the terminal — long lines and long outputs both get clipped with a
    '…' marker so nothing scrolls the query itself off-screen."""
    lines = [ln if len(ln) <= _MAX_LINE_LEN else ln[: _MAX_LINE_LEN - 1] + "…" for ln in text.splitlines()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    hidden = len(lines) - max_lines
    shown = "\n".join(lines[:max_lines])
    return f"{shown}\n  … +{hidden} more line{'s' if hidden != 1 else ''} (truncated)"


def show_cost(summary: str):
    console.print(Text(f"\nCost for this query:", style="dim"))
    console.print(Text(summary, style="dim"))


def _format_input(tool_input: dict) -> str:
    text = ", ".join(f"{k}={v!r}" for k, v in tool_input.items())
    return _truncate(text, max_lines=1)
