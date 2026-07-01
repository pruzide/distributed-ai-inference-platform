# from typing import List, Optional, Dict, Any
# from uuid import uuid4

# from app.db.job_repository import JobRepository


# class JobManager:
#     """
#     JobManager controls the job lifecycle from the application/business side.

#     Right now it can:
#     1. Create a new job
#     2. Fetch job details

#     Later it will also:
#     1. Push job IDs to Redis
#     2. Coordinate job status changes
#     3. Work with retry and metrics logic
#     """

#     def __init__(self, job_repository: JobRepository):
#         self.job_repository = job_repository

#     def submit_job(self, features: List[float]) -> Dict[str, Any]:
#         job_id = str(uuid4())

#         job = self.job_repository.create_job(
#             job_id=job_id,
#             features=features
#         )

#         return {
#             "job_id": job["job_id"],
#             "status": job["status"],
#             "message": "Job submitted successfully"
#         }

#     def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
#         return self.job_repository.get_job_by_id(job_id)

from typing import List, Optional, Dict, Any
from uuid import uuid4

from app.db.job_repository import JobRepository
from app.core.queue_client import QueueClient


class JobManager:
    """
    JobManager controls the job lifecycle from the application/business side.

    Current responsibility:
    1. Create job ID
    2. Store job in PostgreSQL
    3. Push job ID into Redis queue
    4. Fetch job details

    This keeps the API route clean.
    """

    def __init__(
        self,
        job_repository: JobRepository,
        queue_client: Optional[QueueClient] = None
    ):
        self.job_repository = job_repository
        self.queue_client = queue_client

    def submit_job(self, features: List[float]) -> Dict[str, Any]:
        job_id = str(uuid4())

        job = self.job_repository.create_job(
            job_id=job_id,
            features=features
        )

        if self.queue_client is not None:
            self.queue_client.push_job(job["job_id"])

        return {
            "job_id": job["job_id"],
            "status": job["status"],
            "message": "Job submitted successfully and queued for processing"
        }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.job_repository.get_job_by_id(job_id)