"""Tests for write_html file output logic in generate_visualization."""

from __future__ import annotations

import os
import stat

import pytest

from src.query.generate_visualization import write_html


def test_write_html_creates_file(tmp_path):
    """write_html writes content to the specified path."""
    output = tmp_path / "output.html"
    write_html("<html></html>", str(output))
    assert output.read_text(encoding="utf-8") == "<html></html>"


def test_write_html_creates_missing_directories(tmp_path):
    """write_html creates parent directories that don't exist."""
    output = tmp_path / "a" / "b" / "c" / "graph.html"
    write_html("<h1>test</h1>", str(output))
    assert output.exists()
    assert output.read_text(encoding="utf-8") == "<h1>test</h1>"


def test_write_html_overwrites_existing_file(tmp_path):
    """write_html overwrites an existing file at the output path."""
    output = tmp_path / "graph.html"
    output.write_text("old content", encoding="utf-8")
    write_html("new content", str(output))
    assert output.read_text(encoding="utf-8") == "new content"


def test_write_html_prints_location(tmp_path, capsys):
    """write_html prints the output file location after writing."""
    output = tmp_path / "entity_graph.html"
    write_html("<html></html>", str(output))
    captured = capsys.readouterr()
    assert str(output) in captured.out
    assert "Saved visualization to" in captured.out


def test_write_html_exits_on_unwritable_directory(tmp_path):
    """write_html exits with code 2 when the directory is not writable."""
    read_only_dir = tmp_path / "readonly"
    read_only_dir.mkdir()
    # Remove write permission
    read_only_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

    output = str(read_only_dir / "graph.html")
    try:
        with pytest.raises(SystemExit) as exc_info:
            write_html("<html></html>", output)
        assert exc_info.value.code == 2
    finally:
        # Restore permissions for cleanup
        read_only_dir.chmod(stat.S_IRWXU)


def test_write_html_default_path_pattern(tmp_path):
    """write_html works with a docs/entity_graph.html style path."""
    output = tmp_path / "docs" / "entity_graph.html"
    write_html("<html>graph</html>", str(output))
    assert output.exists()
    assert output.read_text(encoding="utf-8") == "<html>graph</html>"
