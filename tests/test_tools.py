import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibecode.tools.base import ToolResult
from vibecode.tools.file_read import FileReadTool
from vibecode.tools.file_write import FileWriteTool
from vibecode.tools.registry import ToolRegistry


def test_registry_lists_schemas_for_registered_tools():
    registry = ToolRegistry()
    registry.register(FileReadTool(Path(".")))
    registry.register_server_tool({"type": "web_search_20260209", "name": "web_search"})

    names = registry.tool_names()
    assert "file_read" in names
    assert "web_search" in names
    assert registry.is_client_tool("file_read")
    assert not registry.is_client_tool("web_search")


def test_registry_subset_only_includes_requested_tools():
    registry = ToolRegistry()
    registry.register(FileReadTool(Path(".")))
    registry.register(FileWriteTool(Path(".")))
    registry.register_server_tool({"type": "web_search_20260209", "name": "web_search"})

    subset = registry.subset(["file_read", "web_search"])
    assert sorted(subset.tool_names()) == ["file_read", "web_search"]


def test_registry_execute_unknown_tool_is_an_error():
    registry = ToolRegistry()
    result = registry.execute("does_not_exist", {})
    assert result.is_error


def test_file_read_missing_file_is_an_error(tmp_path):
    tool = FileReadTool(tmp_path)
    result = tool.execute(path="nope.py")
    assert result.is_error
    assert "not found" in result.content.lower()


def test_file_read_returns_numbered_lines(tmp_path):
    (tmp_path / "hello.py").write_text("a\nb\n")
    tool = FileReadTool(tmp_path)
    result = tool.execute(path="hello.py")
    assert not result.is_error
    assert "1\ta" in result.content
    assert "2\tb" in result.content


def test_file_write_no_change_is_a_noop(tmp_path, monkeypatch):
    called = False

    def fail_if_called():
        nonlocal called
        called = True
        return "y"

    monkeypatch.setattr("vibecode.tools.file_write.get_approval", fail_if_called)

    target = tmp_path / "same.py"
    target.write_text("content\n")
    tool = FileWriteTool(tmp_path)
    result = tool.execute(path="same.py", content="content\n")

    assert not result.is_error
    assert not called  # identical content should never prompt for approval


def test_file_write_declined_does_not_write(tmp_path, monkeypatch):
    monkeypatch.setattr("vibecode.tools.file_write.get_approval", lambda: "n")

    target = tmp_path / "new.py"
    tool = FileWriteTool(tmp_path)
    result = tool.execute(path="new.py", content="new content\n")

    assert result.is_error
    assert not target.exists()


def test_file_write_approved_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr("vibecode.tools.file_write.get_approval", lambda: "y")

    target = tmp_path / "new.py"
    tool = FileWriteTool(tmp_path)
    result = tool.execute(path="new.py", content="new content\n")

    assert not result.is_error
    assert target.read_text() == "new content\n"
