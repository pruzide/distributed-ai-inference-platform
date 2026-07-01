from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.job import Job


class JobRepository:
    """
    JobRepository is responsible only for database operations.

    It does not know about FastAPI.
    It does not know about Redis.
    It does not run ML inference.

    Its job is simple:
    create jobs, read jobs, and later update jobs.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_job(self, job_id: str, features: List[float]) -> Dict[str, Any]:
        job = Job(
            job_id=job_id,
            features=features,
            status="queued",
            retry_count=0
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return self._to_dict(job)

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self.db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            return None

        return self._to_dict(job)

    def _to_dict(self, job: Job) -> Dict[str, Any]:
        """
        Converts SQLAlchemy Job object into a normal Python dictionary.
        This makes it easy for FastAPI to return JSON responses.
        """

        return {
            "job_id": job.job_id,
            "features": job.features,
            "status": job.status,
            "prediction_result": job.prediction_result,
            "error_message": job.error_message,
            "retry_count": job.retry_count,
            "worker_id": job.worker_id,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "latency_ms": job.latency_ms,
        }