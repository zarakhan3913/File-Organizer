"""Unit tests for the HistoryManager and Rollback/Undo mechanism."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from src.file_organizer.history import HistoryManager


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing file operations."""
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_history_record_and_undo(temp_workspace):
    history_file = str(temp_workspace / "test_history.json")
    mgr = HistoryManager(history_file=history_file)

    # 1. Create a dummy file
    source_file = temp_workspace / "invoice_test.pdf"
    source_file.write_text("dummy invoice content")

    # 2. Simulate moving it to category folder
    dest_dir = temp_workspace / "Invoices"
    dest_dir.mkdir()
    dest_file = dest_dir / "invoice_test.pdf"
    shutil.move(str(source_file), str(dest_file))

    # 3. Record move in history
    actions = [
        {
            "source": str(source_file),
            "destination": str(dest_file),
            "category": "Invoices",
        }
    ]
    session_id = mgr.record_session(str(temp_workspace), actions)
    assert session_id is not None

    # Check file exists at destination
    assert dest_file.exists()
    assert not source_file.exists()

    # 4. Perform Undo
    success, msg, restored = mgr.undo_last_session()
    assert success is True
    assert len(restored) == 1

    # Verify original file restored and destination directory cleaned up
    assert source_file.exists()
    assert not dest_file.exists()
    assert not dest_dir.exists()


def test_undo_empty_history(temp_workspace):
    history_file = str(temp_workspace / "empty_history.json")
    mgr = HistoryManager(history_file=history_file)

    success, msg, restored = mgr.undo_last_session()
    assert success is False
    assert len(restored) == 0
