import click
import sys
from pathlib import Path

# Add src directory to Python path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

from agent.planner import plan_edits
from diff.generator import generate_diff
from agent.editor import apply_changes
from ui.display import show_diff, get_approval

@click.command()
@click.argument('prompt')
@click.argument('filepath')
def main(prompt, filepath):
    """
    VibeCode: AI-powered code editor

    PROMPT: The instruction for what changes to make
    FILEPATH: The file to modify

    Example: vibe "Add docstrings" src/utils.py
    """
    try:
        click.echo("🤖 Planning changes with AI...\n")

        # Step 1: Get original and edited content from LLM planner
        original_content, edited_content = plan_edits(filepath, prompt)

        click.echo("✅ Changes planned!\n")

        # Step 2: Generate a unified diff to show the user
        diff_output = generate_diff(original_content, edited_content, filepath)

        # Step 3: Display the diff to the user
        click.echo("📝 Here's what will change:\n")
        show_diff(diff_output)

        # Step 4: Ask user for approval
        click.echo("\n" + "="*50)
        approval = get_approval()

        # Step 5: Apply changes based on user decision
        if approval == 'y':
            apply_changes(filepath, edited_content)
            click.secho("✨ Changes applied successfully!", fg='green', bold=True)
        elif approval == 'n':
            click.secho("❌ Changes discarded.", fg='yellow')
        elif approval == 'e':
            click.echo("Edit mode not implemented yet.")
        else:
            click.secho("Invalid choice. Please use 'y', 'n', or 'e'.", fg='red')

    except FileNotFoundError as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Unexpected error: {e}", fg='red')
        sys.exit(1)


if __name__ == '__main__':
    main()