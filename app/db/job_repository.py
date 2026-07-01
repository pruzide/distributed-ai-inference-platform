# from typing import List, Optional, Dict, Any
# from sqlalchemy.orm import Session

# from app.models.job import Job


# class JobRepository:
#     """
#     JobRepository is responsible only for database operations.

#     It does not know about FastAPI.
#     It does not know about Redis.
#     It does not run ML inference.

#     Its job is simple:
#     create jobs, read jobs, and later update jobs.
#     """

#     def __init__(self, db: Session):
#         self.db = db

#     def create_job(self, job_id: str, features: List[float]) -> Dict[str, Any]:
#         job = Job(
#             job_id=job_id,
#             features=features,
#             status="queued",
#             retry_count=0
#         )

#         self.db.add(job)
#         self.db.commit()
#         self.db.refresh(job)

#         return self._to_dict(job)

#     def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
#         job = self.db.query(Job).filter(Job.job_id == job_id).first()

#         if job is None:
#             return None

#         return self._to_dict(job)

#     def _to_dict(self, job: Job) -> Dict[str, Any]:
#         """
#         Converts SQLAlchemy Job object into a normal Python dictionary.
#         This makes it easy for FastAPI to return JSON responses.
#         """

#         return {
#             "job_id": job.job_id,
#             "features": job.features,
#             "status": job.status,
#             "prediction_result": job.prediction_result,
#             "error_message": job.error_message,
#             "retry_count": job.retry_count,
#             "worker_id": job.worker_id,
#             "created_at": job.created_at,
#             "started_at": job.started_at,
#             "completed_at": job.completed_at,
#             "latency_ms": job.latency_ms,
#         }



# from typing import List, Optional, Dict, Any
# from datetime import datetime, timezone

# from sqlalchemy.orm import Session

# from app.models.job import Job


# class JobRepository:
#     """
#     JobRepository is responsible only for database operations.

#     It creates jobs, reads jobs, and updates job states.
#     """

#     def __init__(self, db: Session):
#         self.db = db

#     def create_job(self, job_id: str, features: List[float]) -> Dict[str, Any]:
#         job = Job(
#             job_id=job_id,
#             features=features,
#             status="queued",
#             retry_count=0
#         )

#         self.db.add(job)
#         self.db.commit()
#         self.db.refresh(job)

#         return self._to_dict(job)

#     def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
#         job = self.db.query(Job).filter(Job.job_id == job_id).first()

#         if job is None:
#             return None

#         return self._to_dict(job)

#     def mark_processing(self, job_id: str, worker_id: str) -> Optional[Dict[str, Any]]:
#         job = self.db.query(Job).filter(Job.job_id == job_id).first()

#         if job is None:
#             return None

#         job.status = "processing"
#         job.worker_id = worker_id
#         job.started_at = datetime.now(timezone.utc)

#         self.db.commit()
#         self.db.refresh(job)

#         return self._to_dict(job)

#     def mark_completed(
#         self,
#         job_id: str,
#         prediction_result: Dict[str, Any]
#     ) -> Optional[Dict[str, Any]]:
#         job = self.db.query(Job).filter(Job.job_id == job_id).first()

#         if job is None:
#             return None

#         completed_at = datetime.now(timezone.utc)

#         job.status = "completed"
#         job.prediction_result = prediction_result
#         job.completed_at = completed_at
#         job.error_message = None

#         if job.started_at is not None:
#             started_at = job.started_at

#             if started_at.tzinfo is None:
#                 started_at = started_at.replace(tzinfo=timezone.utc)

#             job.latency_ms = (completed_at - started_at).total_seconds() * 1000

#         self.db.commit()
#         self.db.refresh(job)

#         return self._to_dict(job)

#     def mark_failed(
#         self,
#         job_id: str,
#         error_message: str
#     ) -> Optional[Dict[str, Any]]:
#         job = self.db.query(Job).filter(Job.job_id == job_id).first()

#         if job is None:
#             return None

#         completed_at = datetime.now(timezone.utc)

#         job.status = "failed"
#         job.error_message = error_message
#         job.completed_at = completed_at

#         if job.started_at is not None:
#             started_at = job.started_at

#             if started_at.tzinfo is None:
#                 started_at = started_at.replace(tzinfo=timezone.utc)

#             job.latency_ms = (completed_at - started_at).total_seconds() * 1000

#         self.db.commit()
#         self.db.refresh(job)

#         return self._to_dict(job)

#     def _to_dict(self, job: Job) -> Dict[str, Any]:
#         return {
#             "job_id": job.job_id,
#             "features": job.features,
#             "status": job.status,
#             "prediction_result": job.prediction_result,
#             "error_message": job.error_message,
#             "retry_count": job.retry_count,
#             "worker_id": job.worker_id,
#             "created_at": job.created_at,
#             "started_at": job.started_at,
#             "completed_at": job.completed_at,
#             "latency_ms": job.latency_ms,
#         }


from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.job import Job


class JobRepository:
    """
    JobRepository is responsible only for database operations.

    It creates jobs, reads jobs, updates job states,
    and tracks retries/failures.
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

    def mark_processing(self, job_id: str, worker_id: str) -> Optional[Dict[str, Any]]:
        job = self.db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            return None

        job.status = "processing"
        job.worker_id = worker_id
        job.started_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(job)

        return self._to_dict(job)

    def mark_completed(
        self,
        job_id: str,
        prediction_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        job = self.db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            return None

        completed_at = datetime.now(timezone.utc)

        job.status = "completed"
        job.prediction_result = prediction_result
        job.completed_at = completed_at
        job.error_message = None

        if job.started_at is not None:
            started_at = job.started_at

            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)

            job.latency_ms = (completed_at - started_at).total_seconds() * 1000

        self.db.commit()
        self.db.refresh(job)

        return self._to_dict(job)

    def mark_queued_for_retry(
        self,
        job_id: str,
        error_message: str,
        next_retry_count: int
    ) -> Optional[Dict[str, Any]]:
        """
        Marks a failed attempt as retryable.

        The job becomes queued again so that a worker can pick it later.
        """

        job = self.db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            return None

        job.status = "queued"
        job.error_message = error_message
        job.retry_count = next_retry_count
        job.completed_at = None

        self.db.commit()
        self.db.refresh(job)

        return self._to_dict(job)

    def mark_failed(
        self,
        job_id: str,
        error_message: str
    ) -> Optional[Dict[str, Any]]:
        job = self.db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            return None

        completed_at = datetime.now(timezone.utc)

        job.status = "failed"
        job.error_message = error_message
        job.completed_at = completed_at

        if job.started_at is not None:
            started_at = job.started_at

            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)

            job.latency_ms = (completed_at - started_at).total_seconds() * 1000

        self.db.commit()
        self.db.refresh(job)

        return self._to_dict(job)

    def _to_dict(self, job: Job) -> Dict[str, Any]:
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