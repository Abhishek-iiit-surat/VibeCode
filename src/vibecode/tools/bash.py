import subprocess
from pathlib import Path

from vibecode.tools.base import Tool, ToolResult


class BashTool(Tool):
    name = "bash"
    description = (
        "Runs a shell command. The user sees each command and must confirm before it"
        "executes — you don't need to ask permission in chat first, but never word a"
        "command to slip past that confirmation, especially for destructive or"
        "irreversible ones (rm -rf, git push --force, git reset --hard, dropping a database)."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The shell command to run."},
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 120).",
            },
        },
        "required": ["command"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def execute(self, command: str, timeout: int = 120) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(content=f"Command timed out after {timeout}s: {command}", is_error=True)
        except Exception as e:
            return ToolResult(content=f"Failed to run command: {e}", is_error=True)

        output = f"Exit code: {result.returncode}\n"
        if result.stdout:
            output += f"stdout:\n{result.stdout}\n"
        if result.stderr:
            output += f"stderr:\n{result.stderr}\n"

        return ToolResult(content=output, is_error=(result.returncode != 0))
