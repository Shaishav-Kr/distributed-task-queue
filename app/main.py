"""
main.py - The Web Application (Flask)

This is the "front door" of the system.
Users hit these endpoints, and instead of doing heavy work immediately,
we DISPATCH tasks to Celery workers via Redis.

Flow: User → Flask API → Redis (queue) → Celery Worker → Result stored in Redis
"""

from flask import Flask, jsonify, request
from celery_worker import (
    send_email_task,
    process_data_task,
    generate_report_task,
    celery_app
)
from celery.result import AsyncResult

app = Flask(__name__)


# ─────────────────────────────────────────────
# ENDPOINT 1: Trigger a background email task
# ─────────────────────────────────────────────
@app.route("/send-email", methods=["POST"])
def send_email():
    """
    Instead of sending an email synchronously (which could take seconds),
    we push it to the task queue and immediately return a task_id to the user.
    """
    data = request.get_json()
    recipient = data.get("recipient", "test@example.com")
    subject = data.get("subject", "Hello!")
    body = data.get("body", "This is a test email.")

    # .delay() is the magic — it sends the task to Redis asynchronously
    task = send_email_task.delay(recipient, subject, body)

    return jsonify({
        "message": "Email task queued!",
        "task_id": task.id,         # Use this ID to check status later
        "status": "PENDING"
    }), 202  # 202 = Accepted (not done yet, but we got your request)


# ─────────────────────────────────────────────
# ENDPOINT 2: Trigger a data processing task
# ─────────────────────────────────────────────
@app.route("/process-data", methods=["POST"])
def process_data():
    """
    Simulate processing a large dataset in the background.
    e.g., parsing CSVs, running ML models, aggregating stats.
    """
    data = request.get_json()
    dataset_size = data.get("size", 100)

    task = process_data_task.delay(dataset_size)

    return jsonify({
        "message": "Data processing started!",
        "task_id": task.id,
        "status": "PENDING"
    }), 202


# ─────────────────────────────────────────────
# ENDPOINT 3: Trigger a report generation task
# ─────────────────────────────────────────────
@app.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json()
    report_type = data.get("type", "monthly")

    task = generate_report_task.delay(report_type)

    return jsonify({
        "message": f"{report_type} report generation started!",
        "task_id": task.id,
        "status": "PENDING"
    }), 202


# ─────────────────────────────────────────────
# ENDPOINT 4: Check task status by ID
# ─────────────────────────────────────────────
@app.route("/task/<task_id>", methods=["GET"])
def get_task_status(task_id):
    """
    Poll this endpoint with the task_id to check if your task is done.
    
    Celery task states:
    - PENDING  → Task is waiting in queue
    - STARTED  → Worker picked it up and is running it
    - SUCCESS  → Completed successfully
    - FAILURE  → Something went wrong
    - RETRY    → Failed, but Celery is retrying it
    """
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task_result.status,
    }

    if task_result.status == "SUCCESS":
        response["result"] = task_result.result   # The actual return value
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)  # The exception message

    return jsonify(response)


# ─────────────────────────────────────────────
# ENDPOINT 5: Health check
# ─────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "task-queue-api"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
