from pathlib import Path

from vibecode.diff.generator import generate_diff
from vibecode.tools.base import Tool, ToolResult
from vibecode.ui.display import get_approval, show_diff


def _read_existing(file_path: Path) -> str:
    # Force UTF-8 instead of the platform default (cp1252 on Windows),
    # which raises on bytes outside it; fall back to latin-1 (never raises).
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


class FileWriteTool(Tool):
    name = "file_write"
    description = (
        "Writes content to a file. Always shows the user a diff and requires approval"
        "before anything is written to disk. Never attempt to bypass that."       
    )
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to write."},
            "content": {"type": "string", "description": "The complete new content of the file."},
        },
        "required": ["path", "content"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        return p.resolve() if p.is_absolute() else (self.project_root / p).resolve()

    def execute(self, path: str, content: str) -> ToolResult:
        file_path = self._resolve(path)
        original = _read_existing(file_path) if file_path.exists() else ""

        diff = generate_diff(original, content, path)
        if not diff:
            return ToolResult(content=f"No changes — {path} already matches the requested content.")

        show_diff(diff)
        approval = get_approval()

        if approval == "n":
            return ToolResult(
                content=f"User declined the write to {path}. Do not retry without new instructions.",
                is_error=True,
            )
        if approval == "e":
            return ToolResult(
                content=f"User chose to edit {path} manually instead of applying this change.",
                is_error=True,
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return ToolResult(content=f"Wrote {path}.")
