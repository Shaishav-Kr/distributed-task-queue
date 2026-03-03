"""
celery_worker.py - The Background Worker

This file does TWO things:
1. Creates the Celery app (configured to use Redis as broker)
2. Defines all the tasks that can be run in the background

KEY CONCEPTS:
- @celery_app.task(bind=True, ...) turns a normal Python function into a Celery task
- bind=True gives the task access to `self` so it can retry itself
- max_retries=3 means: if it fails, try 3 more times before giving up
- countdown=5 means: wait 5 seconds before retrying
"""

import time
import random
import logging
from celery import Celery

# ─────────────────────────────────────────────
# CELERY APP CONFIGURATION
# ─────────────────────────────────────────────
# broker_url: Where Celery sends tasks TO (Redis)
# result_backend: Where Celery stores results (also Redis)
# "redis://redis:6379/0" → host=redis (Docker service name), port=6379, db=0

celery_app = Celery(
    "distributed_tasks",
    broker="redis://redis:6379/0",       # Redis as message broker
    result_backend="redis://redis:6379/0" # Redis to store task results
)

# Optional config
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # Enables the STARTED state
    result_expires=3600,       # Results expire after 1 hour
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# TASK 1: Send Email
# ─────────────────────────────────────────────
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_email_task(self, recipient: str, subject: str, body: str):
    """
    Simulates sending an email.
    
    In a real app, you'd use smtplib, SendGrid, AWS SES, etc.
    Here we just simulate it with sleep() to mimic network delay.
    
    `bind=True` + `self` allows us to call self.retry() if it fails.
    """
    try:
        logger.info(f"[EMAIL] Sending to {recipient}: '{subject}'")
        
        # Simulate email sending taking 2 seconds
        time.sleep(2)
        
        # Randomly simulate a failure 20% of the time (to demo retry logic)
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
        # self.retry() re-queues this task — Celery handles the countdown
        raise self.retry(exc=exc, countdown=5)


# ─────────────────────────────────────────────
# TASK 2: Process Data
# ─────────────────────────────────────────────
@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_data_task(self, dataset_size: int):
    """
    Simulates heavy data processing (think: ML inference, ETL pipeline).
    
    The bigger the dataset, the longer it takes.
    We simulate this by sleeping proportional to size.
    """
    logger.info(f"[DATA] Processing dataset of size {dataset_size}")

    results = []
    
    # Simulate processing each "record" in the dataset
    # In real life, this might be: read CSV row → transform → write to DB
    chunk_size = min(dataset_size, 10)  # Process in chunks of 10
    
    for i in range(chunk_size):
        time.sleep(0.1)  # Simulate work per record
        results.append({
            "record_id": i,
            "processed": True,
            "value": random.randint(1, 100)
        })

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


# ─────────────────────────────────────────────
# TASK 3: Generate Report
# ─────────────────────────────────────────────
@celery_app.task(bind=True, max_retries=2, default_retry_delay=15)
def generate_report_task(self, report_type: str):
    """
    Simulates generating a complex report (think: PDF generation,
    querying multiple databases, aggregating data).
    """
    logger.info(f"[REPORT] Generating {report_type} report...")

    # Different report types take different amounts of time
    durations = {
        "monthly": 3,
        "quarterly": 5,
        "annual": 8,
        "custom": 4,
    }
    sleep_time = durations.get(report_type, 3)
    time.sleep(sleep_time)

    report_data = {
        "type": report_type,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "sections": ["Executive Summary", "Sales Metrics", "User Growth", "Projections"],
        "total_pages": random.randint(10, 50),
        "status": "ready"
    }

    logger.info(f"[REPORT] {report_type} report generated successfully")
    return report_data
