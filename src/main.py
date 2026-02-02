import click
import sys
import asyncio
from pathlib import Path

# Add src directory to Python path so we can import modules
# This works whether main.py is called directly or imported
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from agent.planner import plan_edits
from diff.generator import generate_diff
from agent.editor import apply_changes, apply_sandbox_to_real_file
from ui.display import show_diff, get_approval
from agent.feedback import edit_with_validation, smart_edit
from storage.agentfs_manager import AgentFSManager
from ui.display import show_execution_result, show_iteration_summary

@click.command()
@click.argument('prompt', required=False)
@click.argument('filepath', required=False)
def main(prompt, filepath):
    """
    VibeCode: AI-powered code editor with AI-powered validation

    Interactive session mode - edit multiple files without restarting!

    Usage:
      vibe "Add docstrings" src/utils.py    (Single edit mode)
      vibe                                   (Interactive session mode)

    In interactive mode, you can:
      - Enter prompt and filepath for each edit
      - Type 'quit' or press ESC to exit
      - Session persists across edits (AgentFS sandbox preserved)

    Example interactive session:
      $ vibe
      📝 Enter prompt (or 'quit'/'ESC' to exit): Add error handling
      📝 Enter filepath: src/main.py
      [... AI edits with feedback loop ...]
      Apply changes? (y)es / (n)o / (e)dit: y
      ✨ Changes applied!
      📝 Enter prompt (or 'quit'/'ESC' to exit): Fix imports
      📝 Enter filepath: src/config.py
      [... Another edit in same session ...]
    """
    try:
        # If both arguments provided, run single edit mode (legacy behavior)
        if prompt and filepath:
            click.echo("🤖 Single edit mode\n")
            asyncio.run(single_edit_session(prompt, filepath))
        else:
            # Interactive session mode
            click.echo("🤖 VibeCode Interactive Session Mode")
            click.echo("💡 Tip: Type 'quit' or press CTRL+C to exit\n")
            asyncio.run(interactive_session())

    except KeyboardInterrupt:
        click.secho("\n\n👋 Session ended (CTRL+C). Goodbye!", fg='yellow', bold=True)
        sys.exit(0)
    except FileNotFoundError as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Unexpected error: {e}", fg='red')
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def interactive_session():
    """
    Interactive session that allows multiple edits in one session.
    Persists AgentFS sandbox across multiple edits.
    User can quit by typing 'quit', 'exit', 'ESC', or pressing CTRL+C.
    """
    # Initialize AgentFS sandbox once for the entire session
    agentfs_manager = AgentFSManager()
    await agentfs_manager.initialize_agent("vibe-interactive-session")
    click.secho("✅ AgentFS sandbox initialized for this session\n", fg='green')

    try:
        while True:
            # Get user input for this edit
            click.echo("=" * 60)
            prompt = click.prompt("📝 Enter prompt (or 'quit'/'exit' to exit)", type=str).strip()

            # Check for exit commands
            if prompt.lower() in ('quit', 'exit', 'esc', ''):
                click.secho("\n👋 Ending interactive session...", fg='yellow')
                break

            filepath = click.prompt("📁 Enter filepath", type=str).strip()

            # Check for exit command in filepath too
            if filepath.lower() in ('quit', 'exit', 'esc'):
                click.secho("\n👋 Ending interactive session...", fg='yellow')
                break

            click.echo()

            # Process this edit
            try:
                await process_single_edit(filepath, prompt, agentfs_manager)
            except Exception as e:
                click.secho(f"⚠️  Error processing this file: {e}", fg='yellow')
                continue

            # Ask if user wants to continue
            click.echo()
            continue_session = click.confirm("Would you like to edit another file?", default=True)
            if not continue_session:
                click.secho("\n👋 Ending interactive session...", fg='yellow')
                break

    finally:
        # Always cleanup AgentFS on exit
        click.echo("\n⏳ Cleaning up sandbox...")
        await agentfs_manager.close()
        click.secho("✅ Session ended gracefully", fg='green')

async def single_edit_session(filepath, prompt):
    """
    Single edit mode - edit one file and exit.
    Used when user provides prompt and filepath as arguments.
    """
    agentfs_manager = AgentFSManager()
    await agentfs_manager.initialize_agent("vibe-single-edit")
    click.echo("✅ AgentFS sandbox initialized\n")

    try:
        await process_single_edit(filepath, prompt, agentfs_manager)
    finally:
        await agentfs_manager.close()

async def process_single_edit(filepath, prompt, agentfs_manager):
    """
    Core workflow: Edit a single file with LLM feedback loop.

    Workflow:
    1. Validate file path
    2. Run edit with validation (up to 5 iterations with LLM feedback)
    3. Show iteration summary
    4. Show final diff
    5. Get user approval
    6. Apply changes from sandbox to real file
    """
    # Validate filepath
    try:
        file_path_obj = Path(filepath).resolve()
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
    except Exception as e:
        click.secho(f"❌ Invalid filepath: {e}", fg='red')
        return

    click.echo("🔄 Running code through AI feedback loop...\n")

    try:
        # smart_edit auto-routes: small files → whole-file, large files → chunked
        result = await smart_edit(str(file_path_obj), prompt, agentfs_manager, max_iteration=5)

        # Show iteration summary if there were iterations
        if result.iterations:
            show_iteration_summary(result.iterations)

        # Show final diff
        diff_output = generate_diff(result.original_content, result.final_edited_content, filepath)
        click.echo("\n📝 Here's what will change:\n")
        show_diff(diff_output)

        # Show final execution result if available
        if result.iterations:
            final_iteration = result.iterations[-1]
            show_execution_result(final_iteration.execution_result, final_iteration.attempt_number)

        # Get user approval
        click.echo("\n" + "="*60)
        approval = get_approval()

        if approval == 'y':
            # Apply from sandbox to real file
            click.echo("\n⏳ Applying changes to real file...\n")
            await apply_sandbox_to_real_file(str(file_path_obj), agentfs_manager)
            click.secho("✨ Changes applied successfully!", fg='green', bold=True)

        elif approval == 'n':
            click.secho("❌ Changes discarded.", fg='yellow')

        elif approval == 'e':
            click.secho("💡 Edit mode not implemented yet.", fg='blue')
            click.secho("   (You can manually edit the file and run vibe again)", fg='blue')
        else:
            click.secho("Invalid choice. Please use 'y', 'n', or 'e'.", fg='red')

    except Exception as e:
        click.secho(f"❌ Error during edit: {e}", fg='red')
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
