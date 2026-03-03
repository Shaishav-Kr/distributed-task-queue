# """
# test_tasks.py - Unit Tests using PyTest

# WHAT WE'RE TESTING:
# We don't want to actually run Redis/Celery in tests (too slow, complex setup).
# Instead, we use Celery's built-in test utilities to run tasks EAGERLY
# (synchronously, right here in the test process).

# KEY CONCEPT - task_always_eager:
# Setting CELERY_TASK_ALWAYS_EAGER=True makes tasks run immediately and 
# synchronously instead of being queued. Perfect for unit tests.
# """

# import pytest
# import sys
# import os

# # Make sure Python can find our app modules
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app.celery_worker import celery_app, send_email_task, process_data_task, generate_report_task
# from app.main import app as flask_app


# # ─────────────────────────────────────────────
# # TEST FIXTURES
# # ─────────────────────────────────────────────

# @pytest.fixture
# def celery_eager_mode():
#     """
#     This fixture sets Celery to run tasks synchronously during tests.
#     Without this, tasks would be queued (and we'd need Redis running).
#     """
#     celery_app.conf.update(
#         task_always_eager=True,           # Run tasks immediately, not in queue
#         task_eager_propagates=True,        # Let exceptions bubble up to tests
#     )
#     yield
#     # Cleanup: reset to normal async mode after each test
#     celery_app.conf.update(task_always_eager=False)


# @pytest.fixture
# def flask_client():
#     """Creates a test client for our Flask app."""
#     flask_app.config["TESTING"] = True
#     with flask_app.test_client() as client:
#         yield client


# # ─────────────────────────────────────────────
# # UNIT TESTS: Individual Task Functions
# # ─────────────────────────────────────────────

# class TestSendEmailTask:
#     def test_email_task_returns_success(self, celery_eager_mode):
#         """Test that email task completes and returns expected structure."""
#         result = send_email_task.delay(
#             recipient="test@example.com",
#             subject="Test Subject",
#             body="Hello, this is a test."
#         )
#         # In eager mode, .get() is instant
#         output = result.get()
        
#         assert output["status"] == "sent"
#         assert output["recipient"] == "test@example.com"
#         assert output["subject"] == "Test Subject"
#         assert "message" in output

#     def test_email_task_with_different_recipients(self, celery_eager_mode):
#         """Test that task correctly uses the recipient passed in."""
#         result = send_email_task.delay(
#             recipient="another@test.com",
#             subject="Another Test",
#             body="Body text"
#         )
#         output = result.get()
#         assert output["recipient"] == "another@test.com"


# class TestProcessDataTask:
#     def test_process_data_returns_correct_structure(self, celery_eager_mode):
#         """Test data processing task output structure."""
#         result = process_data_task.delay(dataset_size=50)
#         output = result.get()

#         assert output["status"] == "completed"
#         assert output["total_records"] == 50
#         assert "processed_sample" in output
#         assert "summary" in output
#         assert "avg_value" in output["summary"]
#         assert "max_value" in output["summary"]

#     def test_process_data_with_small_dataset(self, celery_eager_mode):
#         """Edge case: dataset_size=1 should still work."""
#         result = process_data_task.delay(dataset_size=1)
#         output = result.get()
#         assert output["status"] == "completed"
#         assert output["total_records"] == 1


# class TestGenerateReportTask:
#     @pytest.mark.parametrize("report_type", ["monthly", "quarterly", "annual", "custom"])
#     def test_all_report_types(self, celery_eager_mode, report_type):
#         """Parametrized test — runs once for each report type."""
#         result = generate_report_task.delay(report_type=report_type)
#         output = result.get()

#         assert output["status"] == "ready"
#         assert output["type"] == report_type
#         assert "sections" in output
#         assert len(output["sections"]) > 0
#         assert "total_pages" in output

#     def test_report_has_timestamp(self, celery_eager_mode):
#         """Ensure the generated_at timestamp is present."""
#         result = generate_report_task.delay(report_type="monthly")
#         output = result.get()
#         assert "generated_at" in output
#         assert len(output["generated_at"]) > 0


# # ─────────────────────────────────────────────
# # INTEGRATION TESTS: Flask API Endpoints
# # ─────────────────────────────────────────────

# class TestFlaskEndpoints:
#     def test_health_check(self, flask_client):
#         """Health endpoint should always return 200."""
#         response = flask_client.get("/health")
#         assert response.status_code == 200
#         data = response.get_json()
#         assert data["status"] == "ok"

#     def test_send_email_endpoint_returns_202(self, flask_client):
#         """Queuing a task should return 202 Accepted."""
#         payload = {
#             "recipient": "user@example.com",
#             "subject": "Hello",
#             "body": "Test body"
#         }
#         response = flask_client.post("/send-email", json=payload)
#         assert response.status_code == 202
#         data = response.get_json()
#         assert "task_id" in data
#         assert data["status"] == "PENDING"

#     def test_process_data_endpoint(self, flask_client):
#         """Data processing endpoint should queue the task."""
#         response = flask_client.post("/process-data", json={"size": 100})
#         assert response.status_code == 202
#         data = response.get_json()
#         assert "task_id" in data

#     def test_generate_report_endpoint(self, flask_client):
#         """Report generation endpoint should return task_id."""
#         response = flask_client.post("/generate-report", json={"type": "monthly"})
#         assert response.status_code == 202
#         data = response.get_json()
#         assert "task_id" in data
#         assert "message" in data

#     def test_task_status_endpoint_with_invalid_id(self, flask_client):
#         """Checking status for a fake task_id should return PENDING (not found = pending in Celery)."""
#         response = flask_client.get("/task/fake-task-id-12345")
#         assert response.status_code == 200
#         data = response.get_json()
#         assert "status" in data
#         assert data["task_id"] == "fake-task-id-12345"


"""
test_tasks.py - Unit Tests using PyTest
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_worker import celery_app, send_email_task, process_data_task, generate_report_task
from main import app as flask_app


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def celery_eager_mode():
    """Run Celery tasks synchronously (no Redis needed)."""
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
    yield
    celery_app.conf.update(task_always_eager=False)


@pytest.fixture
def flask_client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


# ─────────────────────────────────────────────
# UNIT TESTS: Task Functions (no Redis needed)
# ─────────────────────────────────────────────

class TestSendEmailTask:
    def test_email_task_returns_success(self, celery_eager_mode):
        # Patch random to always return 0.5 — prevents the simulated 20% failure
        with patch("celery_worker.random.random", return_value=0.5):
            result = send_email_task.delay("test@example.com", "Test Subject", "Hello.")
            output = result.get()
        assert output["status"] == "sent"
        assert output["recipient"] == "test@example.com"
        assert output["subject"] == "Test Subject"
        assert "message" in output

    def test_email_task_with_different_recipients(self, celery_eager_mode):
        with patch("celery_worker.random.random", return_value=0.5):
            result = send_email_task.delay("another@test.com", "Another Test", "Body")
            output = result.get()
        assert output["recipient"] == "another@test.com"


class TestProcessDataTask:
    def test_process_data_returns_correct_structure(self, celery_eager_mode):
        result = process_data_task.delay(50)
        output = result.get()
        assert output["status"] == "completed"
        assert output["total_records"] == 50
        assert "processed_sample" in output
        assert "summary" in output
        assert "avg_value" in output["summary"]
        assert "max_value" in output["summary"]

    def test_process_data_with_small_dataset(self, celery_eager_mode):
        result = process_data_task.delay(1)
        output = result.get()
        assert output["status"] == "completed"
        assert output["total_records"] == 1


class TestGenerateReportTask:
    @pytest.mark.parametrize("report_type", ["monthly", "quarterly", "annual", "custom"])
    def test_all_report_types(self, celery_eager_mode, report_type):
        result = generate_report_task.delay(report_type)
        output = result.get()
        assert output["status"] == "ready"
        assert output["type"] == report_type
        assert "sections" in output
        assert len(output["sections"]) > 0
        assert "total_pages" in output

    def test_report_has_timestamp(self, celery_eager_mode):
        result = generate_report_task.delay("monthly")
        output = result.get()
        assert "generated_at" in output
        assert len(output["generated_at"]) > 0


# ─────────────────────────────────────────────
# INTEGRATION TESTS: Flask Endpoints
# These mock Redis so they work without a real Redis instance
# ─────────────────────────────────────────────

class TestFlaskEndpoints:
    def test_health_check(self, flask_client):
        response = flask_client.get("/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"

    def test_send_email_endpoint_returns_202(self, flask_client):
        # Mock the task so it doesn't try to connect to Redis
        mock_task = MagicMock()
        mock_task.id = "fake-task-id-email"
        with patch("main.send_email_task.delay", return_value=mock_task):
            response = flask_client.post("/send-email", json={
                "recipient": "user@example.com",
                "subject": "Hello",
                "body": "Test"
            })
        assert response.status_code == 202
        data = response.get_json()
        assert data["task_id"] == "fake-task-id-email"
        assert data["status"] == "PENDING"

    def test_process_data_endpoint(self, flask_client):
        mock_task = MagicMock()
        mock_task.id = "fake-task-id-data"
        with patch("main.process_data_task.delay", return_value=mock_task):
            response = flask_client.post("/process-data", json={"size": 100})
        assert response.status_code == 202
        assert response.get_json()["task_id"] == "fake-task-id-data"

    def test_generate_report_endpoint(self, flask_client):
        mock_task = MagicMock()
        mock_task.id = "fake-task-id-report"
        with patch("main.generate_report_task.delay", return_value=mock_task):
            response = flask_client.post("/generate-report", json={"type": "monthly"})
        assert response.status_code == 202
        assert response.get_json()["task_id"] == "fake-task-id-report"

    def test_task_status_endpoint(self, flask_client):
        # Mock AsyncResult so it doesn't connect to Redis
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.result = {"status": "sent", "recipient": "test@example.com"}
        with patch("main.AsyncResult", return_value=mock_result):
            response = flask_client.get("/task/fake-task-id-12345")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "SUCCESS"
        assert data["task_id"] == "fake-task-id-12345"
        assert "result" in data