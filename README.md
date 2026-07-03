# Distributed AI Inference & Job Scheduling Platform

A Dockerized backend platform for asynchronous ML inference jobs using FastAPI, Redis, PostgreSQL, distributed workers, retries, and monitoring.

This is not a model-accuracy project. It is a backend engineering project around the infrastructure needed after an ML model exists.

---

## Why I built this

Most ML projects stop at a notebook or a basic prediction API.

I built this to understand the real software bottlenecks around AI systems:

- accepting prediction jobs without blocking the API
- queueing work for background processing
- coordinating multiple workers
- tracking job state reliably
- retrying failed inference jobs
- monitoring latency, throughput, failures, and retries

---

## Architecture

<p align="center">
  <img src="docs/screenshots/architecture-overview.png" alt="Distributed AI Inference Platform Architecture" width="950">
</p>

FastAPI accepts jobs, PostgreSQL stores durable job state, Redis queues job IDs, Docker workers process jobs asynchronously, and Streamlit displays system metrics.

---

## What I built

- FastAPI backend with REST APIs for job submission, status tracking, health checks, and metrics
- Redis queue for asynchronous job dispatch
- PostgreSQL job tracking using SQLAlchemy
- 3 Dockerized worker services
- 4 threads per worker using `ThreadPoolExecutor`
- 12 total concurrent worker threads
- Retry handling with up to 3 attempts for failed jobs
- scikit-learn dummy credit-risk-style inference model
- Streamlit dashboard for metrics and recent jobs
- Docker Compose setup for API, Redis, PostgreSQL, workers, and dashboard

---

## Tech stack

Python, FastAPI, Redis, PostgreSQL, SQLAlchemy, scikit-learn, Streamlit, Docker, Docker Compose, ThreadPoolExecutor

---

## API endpoints

| Method | Endpoint | Purpose | Proof |
| --- | --- | --- | --- |
| `GET` | `/health` | API health check | [`02-api-health.json`](docs/proof/02-api-health.json) |
| `GET` | `/queue/health` | Redis queue health check | [`03-queue-health.json`](docs/proof/03-queue-health.json) |
| `POST` | `/jobs` | Submit inference job | [`04-submit-job.json`](docs/proof/04-submit-job.json) |
| `GET` | `/jobs/{job_id}` | Check job status/result | [`05-completed-job.json`](docs/proof/05-completed-job.json) |
| `GET` | `/metrics/summary` | System metrics summary | [`08-metrics-summary.json`](docs/proof/08-metrics-summary.json) |
| `GET` | `/metrics/recent-jobs` | Recent job history | [`09-recent-jobs.json`](docs/proof/09-recent-jobs.json) |

---

## Job lifecycle

```text
queued → processing → completed
                  ↘ failed after retry limit