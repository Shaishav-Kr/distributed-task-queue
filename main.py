from flask import Flask, jsonify, request
from celery_worker import send_email_task, process_data_task, generate_report_task, celery_app
from celery.result import AsyncResult

app = Flask(__name__)


@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.get_json()
    task = send_email_task.delay(
        data.get("recipient", "test@example.com"),
        data.get("subject", "Hello!"),
        data.get("body", "Test email.")
    )
    return jsonify({"message": "Email task queued!", "task_id": task.id, "status": "PENDING"}), 202


@app.route("/process-data", methods=["POST"])
def process_data():
    data = request.get_json()
    task = process_data_task.delay(data.get("size", 100))
    return jsonify({"message": "Data processing started!", "task_id": task.id, "status": "PENDING"}), 202


@app.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json()
    task = generate_report_task.delay(data.get("type", "monthly"))
    return jsonify({"message": "Report generation started!", "task_id": task.id, "status": "PENDING"}), 202


@app.route("/task/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task_result = AsyncResult(task_id, app=celery_app)
    response = {"task_id": task_id, "status": task_result.status}
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)
    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "task-queue-api"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
