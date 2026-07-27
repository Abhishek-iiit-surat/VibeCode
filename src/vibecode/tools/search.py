from pathlib import Path
import re

from vibecode.tools.base import Tool, ToolResult

EXCLUDED_DIRS = {
    "venv", "env", ".venv", "__pycache__", ".git",
    "node_modules", ".pytest_cache", ".vibecode",
}
# A venv created in-place at the project root (python -m venv .) lays down
# Lib/Scripts/Include next to pyvenv.cfg instead of inside a venv/ wrapper �
# detect that case so a search doesn't wade through installed packages.
IN_PLACE_VENV_DIRS = {"Lib", "Scripts", "Include"}
MAX_RESULTS = 200


class SearchTool(Tool):
    """One tool for exploring a project: find files by name (glob) or by
    content (grep), so the agent has a single way to navigate large codebases
    instead of reading files blindly."""

    name = "search"
    description = (
        "Explore the project by name or by content. Pass 'glob' to find files "
        "matching a name pattern (e.g. '**/*.py'). Pass 'pattern' (a regex) to "
        "find files whose contents match it, returned as 'path:line: text'. "
        "Pass both to grep only within files matching the glob. Use this before "
        "file_read to locate the right file/line in a large codebase."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex to search file contents for."},
            "glob": {"type": "string", "description": "Filename glob, e.g. '**/*.py' or 'src/**/test_*.py'."},
            "path": {
                "type": "string",
                "description": "Directory or file to search from: relative to the project root "
                "(default), or an absolute path to search anywhere on disk.",
            },
            "case_insensitive": {"type": "boolean", "description": "Case-insensitive content match (default: false)."},
        },
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._excluded_dirs = EXCLUDED_DIRS | (
            IN_PLACE_VENV_DIRS if (project_root / "pyvenv.cfg").exists() else set()
        )

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        return p.resolve() if p.is_absolute() else (self.project_root / p).resolve()

    def _rel(self, file_path: Path) -> str:
        return str(file_path.relative_to(self.project_root)) if file_path.is_relative_to(self.project_root) else str(file_path)

    def _candidate_files(self, root: Path, glob: str):
        if root.is_file():
            yield root
            return

        # A pattern with no "**" (e.g. "*.py") is treated as recursive by
        # filename, matching what users mean by "*.py" in a search tool �
        # Path.glob would otherwise only match the top-level directory.
        pattern = glob or "**/*"
        walk_pattern = pattern if "**" in pattern else f"**/{pattern}"

        for file_path in root.glob(walk_pattern):
            if file_path.is_file() and not any(part in self._excluded_dirs for part in file_path.parts):
                yield file_path

    def execute(self, pattern: str = None, glob: str = None, path: str = ".", case_insensitive: bool = False) -> ToolResult:
        if not pattern and not glob:
            return ToolResult(content="Provide at least one of 'pattern' or 'glob'.", is_error=True)

        root = self._resolve(path)
        if not root.exists():
            return ToolResult(content=f"Path not found: {path}", is_error=True)

        if not pattern:
            return self._find_by_name(root, glob)
        return self._find_by_content(root, glob, pattern, case_insensitive)

    def _find_by_name(self, root: Path, glob: str) -> ToolResult:
        if not root.is_dir():
            return ToolResult(content=f"Not a directory: {root}", is_error=True)

        candidates = list(self._candidate_files(root, glob))
        if not candidates:
            return ToolResult(content=f"No files matched '{glob}'.")

        candidates.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        truncated = len(candidates) > MAX_RESULTS
        candidates = candidates[:MAX_RESULTS]

        header = f"(showing first {MAX_RESULTS} of more matches)\n" if truncated else ""
        return ToolResult(content=header + "\n".join(self._rel(f) for f in candidates))

    def _find_by_content(self, root: Path, glob: str, pattern: str, case_insensitive: bool) -> ToolResult:
        try:
            regex = re.compile(pattern, re.IGNORECASE if case_insensitive else 0)
        except re.error as e:
            return ToolResult(content=f"Invalid regex '{pattern}': {e}", is_error=True)

        matches = []
        for file_path in self._candidate_files(root, glob):
            try:
                text = file_path.read_text(errors="ignore")
            except OSError:
                continue

            rel = self._rel(file_path)
            for line_no, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    matches.append(f"{rel}:{line_no}: {line.strip()}")
                    if len(matches) >= MAX_RESULTS:
                        break
            if len(matches) >= MAX_RESULTS:
                break

        if not matches:
            return ToolResult(content=f"No matches for '{pattern}'.")

        header = f"(showing first {MAX_RESULTS} matches, results truncated)\n" if len(matches) >= MAX_RESULTS else ""
        return ToolResult(content=header + "\n".join(matches))
