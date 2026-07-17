import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibecode.diff.generator import generate_diff


def test_no_changes_produces_empty_diff():
    content = "line1\nline2\n"
    assert generate_diff(content, content, "file.py") == ""


def test_added_line_appears_in_diff():
    diff = generate_diff("line1\n", "line1\nline2\n", "file.py")
    assert "+line2" in diff


def test_removed_line_appears_in_diff():
    diff = generate_diff("line1\nline2\n", "line1\n", "file.py")
    assert "-line2" in diff


def test_diff_headers_include_filename():
    diff = generate_diff("a\n", "b\n", "example.py")
    assert "example.py (original)" in diff
    assert "example.py (edited)" in diff
