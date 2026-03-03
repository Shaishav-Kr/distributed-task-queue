# 🚀 Distributed Task Queue & Background Worker

A production-ready background job processing system built with **Python**, **Flask**, **Celery**, **Redis**, and **Docker**.

[![CI](https://github.com/Shaishav-Kr/distributed-task-queue/actions/workflows/ci.yml/badge.svg)](https://github.com/Shaishav-Kr/distributed-task-queue/actions)

---

## 🧠 Architecture

```
User Request
     │
     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────────┐
│  Flask API  │─────▶│    Redis    │─────▶│  Celery Worker  │
│  (port 5000)│      │  (broker)   │      │  (executes job) │
└─────────────┘      └─────────────┘      └─────────────────┘
     │                                            │
     │ returns task_id immediately                │ stores result
     ▼                                            ▼
  Client polls                             Redis (result backend)
  /task/<id>
```

**Why this pattern?**
- User gets an instant response (task_id) instead of waiting
- Workers can process tasks in parallel
- Failed tasks are retried automatically
- System can handle thousands of concurrent tasks

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Flask | HTTP API to receive requests |
| Task Queue | Celery | Distribute & execute background tasks |
| Message Broker | Redis | Queue to hold pending tasks |
| Result Backend | Redis | Store completed task results |
| Containerization | Docker + Compose | Run everything consistently |
| Monitoring | Flower | Real-time task monitoring UI |
| Testing | PyTest | Unit + integration tests |

---

## 📁 Project Structure

```
distributed-task-queue/
├── app/
│   ├── main.py           # Flask API with all endpoints
│   └── celery_worker.py  # Celery config + task definitions
├── tests/
│   └── test_tasks.py     # PyTest unit & integration tests
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI pipeline
├── docker-compose.yml    # Orchestrates all services
├── Dockerfile            # Container recipe
├── requirements.txt      # Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### Run the full stack

```bash
# Clone the repo
git clone https://github.com/Shaishav-Kr/distributed-task-queue.git
cd distributed-task-queue

# Start everything (Redis + Flask + Celery Worker + Flower)
docker-compose up --build
```

That's it! Now you have:
- **Flask API** → http://localhost:5000
- **Flower Dashboard** → http://localhost:5555

---

## 📡 API Endpoints

### Queue an email task
```bash
curl -X POST http://localhost:5000/send-email \
  -H "Content-Type: application/json" \
  -d '{"recipient": "user@example.com", "subject": "Hello!", "body": "Test email"}'
```

**Response:**
```json
{
  "message": "Email task queued!",
  "task_id": "abc123-def456-...",
  "status": "PENDING"
}
```

### Check task status
```bash
curl http://localhost:5000/task/abc123-def456-...
```

**Response (when done):**
```json
{
  "task_id": "abc123-def456-...",
  "status": "SUCCESS",
  "result": {
    "status": "sent",
    "recipient": "user@example.com"
  }
}
```

### Process data
```bash
curl -X POST http://localhost:5000/process-data \
  -H "Content-Type: application/json" \
  -d '{"size": 500}'
```

### Generate a report
```bash
curl -X POST http://localhost:5000/generate-report \
  -H "Content-Type: application/json" \
  -d '{"type": "monthly"}'
```

### Health check
```bash
curl http://localhost:5000/health
```

---

## 🧪 Running Tests

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🌸 Flower Monitoring Dashboard

Visit **http://localhost:5555** to see:
- Active/queued/completed tasks in real-time
- Worker status
- Task retry attempts
- Task execution time

---

## 💡 Key Concepts Explained

### Why Redis as a broker?
Redis is an in-memory data store that's extremely fast. Celery uses it as a "post office" — tasks are written to Redis by the API, and workers continuously poll Redis for new tasks to execute.

### Retry Logic
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_email_task(self, ...):
    try:
        # ... do the work
    except ConnectionError as exc:
        raise self.retry(exc=exc, countdown=5)  # Retry after 5 seconds
```

If a task fails, Celery automatically re-queues it up to `max_retries` times.

### Concurrency
The worker is started with `--concurrency=4`, meaning 4 tasks can run in parallel. Scale this based on your server's CPU cores.

---

## 🐛 Troubleshooting

| Issue | Fix |
|-------|-----|
| `Connection refused` on Redis | Make sure `docker-compose up` is running |
| Tasks stuck in PENDING | Check worker logs: `docker-compose logs worker` |
| Port 5000 already in use | Change port in docker-compose.yml |
