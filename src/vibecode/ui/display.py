import click

def show_diff(diff_string):
    """
    Display a unified diff to the user with color formatting.

    Args:
        diff_string (str): The unified diff output
    """
    for line in diff_string.split('\n'):
        if line.startswith('-') and not line.startswith('---'):
            # Red for removed lines
            click.secho(line, fg='red')
        elif line.startswith('+') and not line.startswith('+++'):
            # Green for added lines
            click.secho(line, fg='green')
        elif line.startswith('@@'):
            # Cyan for line number markers
            click.secho(line, fg='cyan')
        else:
            # Normal text for context
            click.echo(line)

def get_approval():
    """
    Ask the user if they want to apply changes.

    Returns:
        str: User's choice ('y' for yes, 'n' for no, 'e' for edit)
    """
    while True:
        choice = click.prompt(
            "Apply changes? (y)es / (n)o / (e)dit",
            type=str
        ).strip().lower()

        if choice in ('y', 'n', 'e'):
            return choice
        else:
            click.secho("Please enter 'y', 'n', or 'e'", fg='yellow')

def show_execution_result(result, iteration_num):
    """
    Show execution result with colors.

    Args:
        result: ExecutionResult object with success, stdout, stderr
        iteration_num: Iteration number for display
    """
    if result.success:
        click.secho(f"\n✅ Iteration {iteration_num}: Success!", fg='green', bold=True)
        if result.stdout:
            click.echo(f"Output:\n{result.stdout}")
    else:
        click.secho(f"\n❌ Iteration {iteration_num}: Failed (exit code {result.exit_code})", fg='red', bold=True)
        if result.stderr:
            click.secho(f"Error:\n{result.stderr}", fg='red')

def show_iteration_summary(iterations):
    """
    Show summary table of all iterations.

    Args:
        iterations: List of Iteration objects
    """
    click.echo("\n" + "="*60)
    click.echo("ITERATION SUMMARY")
    click.echo("="*60)
    for it in iterations:
        status = "✅" if it.success else "❌"
        click.echo(f"  Attempt {it.attempt_number}: {status} (exit code: {it.execution_result.exit_code})")
    click.echo("="*60)
