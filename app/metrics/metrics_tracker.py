from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job import Job


class MetricsTracker:
    """
    MetricsTracker calculates monitoring metrics from PostgreSQL.

    It does not process jobs.
    It does not talk to Redis.
    It does not run ML inference.

    Its responsibility:
    read job history and calculate system performance metrics.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_summary(self, window_minutes: int = 10) -> Dict[str, Any]:
        """
        Returns high-level platform metrics.

        window_minutes is used for throughput calculation:
        how many completed jobs happened in the last N minutes.
        """

        total_jobs = self.db.query(func.count(Job.job_id)).scalar() or 0

        status_rows = (
            self.db.query(Job.status, func.count(Job.job_id))
            .group_by(Job.status)
            .all()
        )

        status_counts = {
            "queued": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }

        for status, count in status_rows:
            status_counts[status] = count

        total_retries = self.db.query(func.coalesce(func.sum(Job.retry_count), 0)).scalar() or 0

        avg_latency = (
            self.db.query(func.avg(Job.latency_ms))
            .filter(Job.latency_ms.isnot(None))
            .scalar()
        )

        max_latency = (
            self.db.query(func.max(Job.latency_ms))
            .filter(Job.latency_ms.isnot(None))
            .scalar()
        )

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)

        completed_in_window = (
            self.db.query(func.count(Job.job_id))
            .filter(Job.status == "completed")
            .filter(Job.completed_at >= window_start)
            .scalar()
            or 0
        )

        throughput_per_minute = completed_in_window / window_minutes

        terminal_jobs = status_counts["completed"] + status_counts["failed"]

        if terminal_jobs == 0:
            success_rate = 0.0
        else:
            success_rate = (status_counts["completed"] / terminal_jobs) * 100

        failure_rate = 100 - success_rate if terminal_jobs > 0 else 0.0

        return {
            "total_jobs": total_jobs,
            "queued_jobs": status_counts["queued"],
            "processing_jobs": status_counts["processing"],
            "completed_jobs": status_counts["completed"],
            "failed_jobs": status_counts["failed"],
            "total_retries": int(total_retries),
            "average_latency_ms": round(float(avg_latency), 2) if avg_latency is not None else 0.0,
            "max_latency_ms": round(float(max_latency), 2) if max_latency is not None else 0.0,
            "throughput_window_minutes": window_minutes,
            "completed_in_window": completed_in_window,
            "throughput_jobs_per_minute": round(throughput_per_minute, 2),
            "success_rate_percent": round(success_rate, 2),
            "failure_rate_percent": round(failure_rate, 2),
        }

    def get_recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Returns recent jobs for debugging and monitoring.
        """

        jobs = (
            self.db.query(Job)
            .order_by(Job.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_dict(job) for job in jobs]

    def _to_dict(self, job: Job) -> Dict[str, Any]:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "retry_count": job.retry_count,
            "worker_id": job.worker_id,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "latency_ms": job.latency_ms,
            "prediction_result": job.prediction_result,
        }