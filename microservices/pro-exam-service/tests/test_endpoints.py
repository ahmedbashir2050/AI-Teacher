import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from fastapi import HTTPException
from api.v1.endpoints.submission import submit_exam

@pytest.mark.asyncio
async def test_submit_exam_late():
    db = MagicMock()
    submission = MagicMock()
    submission.status = "STARTED"
    submission.start_time = datetime.utcnow() - timedelta(minutes=70)
    submission.exam_id = "exam123"

    exam = MagicMock()
    exam.time_limit_minutes = 60

    # Setup mock query results
    mock_query = db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.side_effect = [submission, exam]

    class MockRequest:
        answers = {}

    with patch("api.v1.endpoints.submission.log_audit"):
        with pytest.raises(HTTPException) as excinfo:
            await submit_exam("sub123", MockRequest(), db, "user123")

    assert excinfo.value.status_code == 403
    assert "Time limit exceeded" in excinfo.value.detail
    assert submission.status == "EXPIRED"

@pytest.mark.asyncio
async def test_submit_exam_on_time():
    db = MagicMock()
    submission = MagicMock()
    submission.status = "STARTED"
    submission.start_time = datetime.utcnow() - timedelta(minutes=30)
    submission.exam_id = "exam123"

    exam = MagicMock()
    exam.time_limit_minutes = 60
    exam.content = {"sections": []}

    mock_query = db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.side_effect = [submission, exam]

    class MockRequest:
        answers = {}

    with patch("api.v1.endpoints.submission.scoring_service.calculate_score", return_value=(100, {})):
        with patch("api.v1.endpoints.submission.log_audit"):
            resp = await submit_exam("sub123", MockRequest(), db, "user123")

    assert resp["final_score"] == 100
    assert submission.status == "SUBMITTED"
