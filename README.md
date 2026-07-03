# Distributed AI Inference & Job Scheduling Platform

A Dockerized backend system for running ML inference jobs asynchronously using FastAPI, Redis, PostgreSQL, distributed workers, retries, and monitoring.

This project focuses on the software engineering layer around AI inference — not model accuracy.  
It answers a practical question: **what happens after a model is ready and prediction requests need to be processed reliably at scale?**

---

## Why this project exists

Most ML demos stop at:

```text
input → model → prediction
```

Real systems need more:

```text
request → queue → worker → retry → state tracking → monitoring → debugging
```

I built this project to understand the backend problems behind production AI systems:

- how to avoid blocking the API during inference
- how to queue prediction jobs safely
- how multiple workers coordinate around shared work
- how failed jobs are retried and tracked
- how system health, latency, retries, and failures are monitored

---

## Architecture

![Architecture Overview](./docs/screenshots/architecture_overview.png)

FastAPI accepts inference jobs. PostgreSQL stores durable job state. Redis stores lightweight job IDs for workers to consume. Dockerized workers process jobs asynchronously. Streamlit reads metrics from the API and visualizes system behavior.

---

## What I built

- FastAPI REST backend for submitting and tracking inference jobs
- Redis queue for asynchronous job dispatch
- PostgreSQL-backed job state tracking with SQLAlchemy
- 3 Dockerized worker services
- 4 threads per worker using `ThreadPoolExecutor`
- 12 total concurrent worker threads
- Retry handling with up to 3 attempts for failed jobs
- scikit-learn dummy credit-risk-style inference model
- Streamlit dashboard for recent jobs and system metrics
- Docker Compose setup for API, Redis, PostgreSQL, workers, and dashboard

---

## Core engineering decisions

### Redis is used for dispatch, not storage

Redis stores only job IDs.

The full job payload, result, status, retry count, error message, and latency are stored in PostgreSQL. This keeps Redis lightweight and makes PostgreSQL the source of truth.

```text
Redis      → fast queue
PostgreSQL → durable job state
```

### Inference is processed asynchronously

The API does not run inference inside the request cycle.

A request creates a job, stores it in PostgreSQL, pushes the job ID to Redis, and returns immediately. Workers pick jobs from Redis and update PostgreSQL as jobs move through their lifecycle.

```text
queued → processing → completed
                  ↘ failed
```

### Workers are distributed and threaded

The system runs 3 worker services, each with 4 threads.

```text
3 workers × 4 threads = 12 concurrent worker threads
```

This demonstrates both service-level concurrency and thread-level concurrency.

### Failed jobs are retried, not lost

A bad job is retried up to 3 times. After that, it is marked permanently failed with the error message saved in PostgreSQL.

Verified failed-job example:

```text
status        : failed
retry_count   : 3
error_message : Expected 5 features, got 2
```

---

## Local validation

Verified local run:

```text
total_jobs                 : 41
completed_jobs             : 40
failed_jobs                : 1
total_retries              : 3
average_latency_ms         : 18.77
max_latency_ms             : 48.55
throughput_jobs_per_minute : 2.0
success_rate_percent       : 97.56
failure_rate_percent       : 2.44
```

This confirms that the API, queue, workers, retry flow, database tracking, and metrics dashboard work end-to-end in Docker Compose.

---

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API health check |
| `GET` | `/queue/health` | Redis queue health check |
| `POST` | `/jobs` | Submit inference job |
| `GET` | `/jobs/{job_id}` | Check job status/result |
| `GET` | `/metrics/summary` | System metrics summary |
| `GET` | `/metrics/recent-jobs` | Recent job history |

---

## Proof of work

| Area | Evidence |
| --- | --- |
| Docker services | [`01-docker-services.txt`](docs/proof/01-docker-services.txt) |
| API health | [`02-api-health.json`](docs/proof/02-api-health.json) |
| Redis queue health | [`03-queue-health.json`](docs/proof/03-queue-health.json) |
| Job submission | [`04-submit-job.json`](docs/proof/04-submit-job.json) |
| Completed job | [`05-completed-job.json`](docs/proof/05-completed-job.json) |
| Failed job retry | [`07-failed-job-retry.json`](docs/proof/07-failed-job-retry.json) |
| Metrics summary | [`08-metrics-summary.json`](docs/proof/08-metrics-summary.json) |
| Recent jobs | [`09-recent-jobs.json`](docs/proof/09-recent-jobs.json) |
| Worker logs | [`worker1`](docs/proof/10-worker1-logs.txt), [`worker2`](docs/proof/11-worker2-logs.txt), [`worker3`](docs/proof/12-worker3-logs.txt) |
| PostgreSQL schema | [`12-postgres-schema.txt`](docs/proof/12-postgres-schema.txt) |
| PostgreSQL job counts | [`13-postgres-status-count.txt`](docs/proof/13-postgres-status-count.txt) |
| Failed jobs in PostgreSQL | [`14-postgres-failed-jobs.txt`](docs/proof/14-postgres-failed-jobs.txt) |
| Completed jobs in PostgreSQL | [`15-postgres-completed-jobs.txt`](docs/proof/15-postgres-completed-jobs.txt) |
| Dashboard | [`Streamlit screenshot`](docs/screenshots/02-streamlit-dashboard.png) |

The 1,000+ job load test is intentionally not claimed until the script prints:

```text
RESULT: PASS - 1,000+ submitted jobs reached terminal state.
```

Current load-test proof:

[`16-load-test-output.txt`](docs/proof/16-load-test-output.txt)

---

## Run locally

Start the platform:

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Dashboard:

```text
http://localhost:8501
```

Stop services:

```bash
docker compose down
```

Clean restart:

```bash
docker compose down -v
docker compose up --build
```

---

## Quick test

Health check:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
```

Submit a job:

```powershell
$body = @{
    features = @(1, 2, 3, 4, 5)
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://localhost:8000/jobs" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

Check metrics:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/metrics/summary" -Method GET
```

Run load test:

```powershell
python -u scripts/load_test.py 2>&1 | Tee-Object docs/proof/16-load-test-output.txt
```

---

## Tech stack

Python, FastAPI, Redis, PostgreSQL, SQLAlchemy, scikit-learn, Streamlit, Docker, Docker Compose, ThreadPoolExecutor

---

## What I would improve next

- authentication and authorization
- rate limiting
- Alembic migrations
- structured logging
- Prometheus/Grafana dashboards
- OpenTelemetry tracing
- exponential backoff retries
- dead-letter queue
- model versioning and registry
- CI/CD pipeline
- Kubernetes deployment
- autoscaling workers based on Redis queue length

---

## Project structure

```text
distributed-ai-inference-platform/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── metrics/
│   ├── models/
│   └── workers/
├── dashboard/
├── scripts/
├── docs/
│   ├── proof/
│   └── screenshots/
├── models/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```