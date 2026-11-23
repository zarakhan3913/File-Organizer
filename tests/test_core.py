"""Unit tests for the OrganizerEngine with mocked AI client."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from src.file_organizer.core import OrganizerEngine
from src.file_organizer.history import HistoryManager


@pytest.fixture
def temp_workspace():
    tmp_dir = tempfile.mkdtemp()
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_is_eligible_file(temp_workspace):
    engine = OrganizerEngine(client=MagicMock())
    categories = ["Finance", "Documents"]

    # Normal file
    test_file = temp_workspace / "report.docx"
    test_file.write_text("hello")
    assert engine.is_eligible_file(str(test_file), categories) is True

    # Ignored system / hidden file
    hidden_file = temp_workspace / ".env"
    hidden_file.write_text("SECRET=1")
    assert engine.is_eligible_file(str(hidden_file), categories) is False

    # Directory matching category
    cat_dir = temp_workspace / "Finance"
    cat_dir.mkdir()
    assert engine.is_eligible_file(str(cat_dir), categories) is False


def test_classify_by_filename_mocked():
    # Setup mock Gemini client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Finance"
    mock_client.models.generate_content.return_value = mock_response

    engine = OrganizerEngine(client=mock_client)
    categories = ["Finance", "Personal", "Code"]

    result = engine.classify_by_filename("january_invoice.pdf", ".pdf", categories)
    assert result == "Finance"
    assert mock_client.models.generate_content.called


def test_classify_unknown_when_not_in_categories():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "SpaceExploration"  # Not in allowed categories
    mock_client.models.generate_content.return_value = mock_response

    engine = OrganizerEngine(client=mock_client)
    categories = ["Finance", "Personal"]

    result = engine.classify_by_filename("mars_rover.pdf", ".pdf", categories)
    assert result == "Unknown"


def test_plan_and_dry_run_execution(temp_workspace):
    # Create test files
    (temp_workspace / "receipt_1.pdf").write_text("test receipt")
    (temp_workspace / "resume.pdf").write_text("test resume")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Finance"
    mock_client.models.generate_content.return_value = mock_response

    engine = OrganizerEngine(client=mock_client)
    categories = ["Finance", "Career"]

    plan, unknown, failed = engine.plan_organization(str(temp_workspace), categories)
    assert len(plan) == 2
    assert len(unknown) == 0
    assert len(failed) == 0

    # Dry-run execution: verify no files were moved
    executed = engine.execute_plan(str(temp_workspace), plan, dry_run=True)
    assert len(executed) == 2
    assert (temp_workspace / "receipt_1.pdf").exists()
    assert not (temp_workspace / "Finance" / "receipt_1.pdf").exists()


def test_api_failure_distinguished_from_unknown():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("503 Service Unavailable")

    engine = OrganizerEngine(client=mock_client)
    categories = ["Finance", "Personal"]

    result = engine.classify_by_filename("invoice.pdf", ".pdf", categories, max_retries=1)
    assert result == "API_ERROR"


def test_display_plan_table():
    from src.file_organizer.cli import display_plan_table
    planned_moves = [
        {"file_name": "test.pdf", "category": "Finance", "method": "Filename Scan"}
    ]
    # Verify it runs without raising exceptions
    display_plan_table(planned_moves, dry_run=True)
    display_plan_table(planned_moves, dry_run=False)
