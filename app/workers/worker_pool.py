import os
import socket
from typing import Optional

from dotenv import load_dotenv

from app.core.queue_client import QueueClient
from app.core.inference_engine import InferenceEngine
from app.db.database import SessionLocal
from app.db.job_repository import JobRepository


load_dotenv()


class WorkerPool:
    """
    WorkerPool is responsible for background job processing.

    Current Batch 7 version:
    - Pulls one job at a time from Redis
    - Reads job details from PostgreSQL
    - Runs ML inference
    - Updates PostgreSQL status/result

    Batch 8 will add multithreading.
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        queue_client: Optional[QueueClient] = None,
        inference_engine: Optional[InferenceEngine] = None
    ):
        self.worker_id = worker_id or self._generate_worker_id()
        self.queue_client = queue_client or QueueClient()
        self.inference_engine = inference_engine or InferenceEngine()

    def _generate_worker_id(self) -> str:
        hostname = socket.gethostname()
        process_id = os.getpid()
        return f"{hostname}-{process_id}"

    def process_next_job(self) -> bool:
        """
        Processes one job from Redis.

        Returns:
            True  -> job was found and processed
            False -> no job was available
        """

        job_id = self.queue_client.pop_job(timeout=5)

        if job_id is None:
            print("No job found in queue.")
            return False

        print(f"[{self.worker_id}] Picked job: {job_id}")

        db = SessionLocal()

        try:
            repository = JobRepository(db)

            job = repository.get_job_by_id(job_id)

            if job is None:
                print(f"[{self.worker_id}] Job not found in database: {job_id}")
                return False

            repository.mark_processing(job_id, self.worker_id)
            print(f"[{self.worker_id}] Processing job: {job_id}")

            prediction_result = self.inference_engine.predict(job["features"])

            repository.mark_completed(job_id, prediction_result)
            print(f"[{self.worker_id}] Completed job: {job_id}")

            return True

        except Exception as error:
            print(f"[{self.worker_id}] Failed job: {job_id}. Error: {error}")

            repository = JobRepository(db)
            repository.mark_failed(job_id, str(error))

            return False

        finally:
            db.close()

    def start(self):
        """
        Continuously listens for jobs.

        Stop manually using CTRL + C.
        """

        print(f"Worker started with worker_id={self.worker_id}")

        while True:
            self.process_next_job()