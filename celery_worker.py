import time
import random
import logging
from celery import Celery

celery_app = Celery(
    "distributed_tasks",
    broker="redis://redis:6379/0",
    result_backend="redis://redis:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_email_task(self, recipient: str, subject: str, body: str):
    try:
        logger.info(f"[EMAIL] Sending to {recipient}: '{subject}'")
        time.sleep(2)
        if random.random() < 0.2:
            raise ConnectionError("SMTP server timeout — simulated failure")
        logger.info(f"[EMAIL] Successfully sent to {recipient}")
        return {
            "status": "sent",
            "recipient": recipient,
            "subject": subject,
            "message": f"Email delivered to {recipient}"
        }
    except ConnectionError as exc:
        logger.warning(f"[EMAIL] Failed, retrying... Attempt {self.request.retries + 1}")
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_data_task(self, dataset_size: int):
    logger.info(f"[DATA] Processing dataset of size {dataset_size}")
    results = []
    chunk_size = min(dataset_size, 10)
    for i in range(chunk_size):
        time.sleep(0.1)
        results.append({"record_id": i, "processed": True, "value": random.randint(1, 100)})
    logger.info(f"[DATA] Finished processing {dataset_size} records")
    return {
        "status": "completed",
        "total_records": dataset_size,
        "processed_sample": results,
        "summary": {
            "avg_value": sum(r["value"] for r in results) / len(results),
            "max_value": max(r["value"] for r in results),
        }
    }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=15)
def generate_report_task(self, report_type: str):
    logger.info(f"[REPORT] Generating {report_type} report...")
    durations = {"monthly": 3, "quarterly": 5, "annual": 8, "custom": 4}
    time.sleep(durations.get(report_type, 3))
    report_data = {
        "type": report_type,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "sections": ["Executive Summary", "Sales Metrics", "User Growth", "Projections"],
        "total_pages": random.randint(10, 50),
        "status": "ready"
    }
    logger.info(f"[REPORT] {report_type} report generated successfully")
    return report_data
