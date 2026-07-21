from pathlib import Path

from vibecode.tools.base import Tool, ToolResult


class FileReadTool(Tool):
    name = "file_read"
    description = (
        "Read the contents of a file, given a path relative to the project root "
        "or an absolute path anywhere on disk (not limited to the project). "
        "Returns the content with 1-indexed line numbers."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read."},
        },
        "required": ["path"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        return p.resolve() if p.is_absolute() else (self.project_root / p).resolve()

    def execute(self, path: str) -> ToolResult:
        file_path = self._resolve(path)
        if not file_path.exists():
            return ToolResult(content=f"File not found: {path}", is_error=True)
        if not file_path.is_file():
            return ToolResult(content=f"Not a file: {path}", is_error=True)

        try:
            # Force UTF-8 instead of the platform default (cp1252 on Windows),
            # which raises on bytes outside it; fall back to latin-1 (never raises).
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")
        except Exception as e:
            return ToolResult(content=f"Failed to read {path}: {e}", is_error=True)

        numbered = "\n".join(f"{i + 1}\t{line}" for i, line in enumerate(content.splitlines()))
        return ToolResult(content=numbered or "(empty file)")
