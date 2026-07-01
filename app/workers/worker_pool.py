# import os
# import socket
# from typing import Optional

# from dotenv import load_dotenv

# from app.core.queue_client import QueueClient
# from app.core.inference_engine import InferenceEngine
# from app.db.database import SessionLocal
# from app.db.job_repository import JobRepository


# load_dotenv()


# class WorkerPool:
#     """
#     WorkerPool is responsible for background job processing.

#     Current Batch 7 version:
#     - Pulls one job at a time from Redis
#     - Reads job details from PostgreSQL
#     - Runs ML inference
#     - Updates PostgreSQL status/result

#     Batch 8 will add multithreading.
#     """

#     def __init__(
#         self,
#         worker_id: Optional[str] = None,
#         queue_client: Optional[QueueClient] = None,
#         inference_engine: Optional[InferenceEngine] = None
#     ):
#         self.worker_id = worker_id or self._generate_worker_id()
#         self.queue_client = queue_client or QueueClient()
#         self.inference_engine = inference_engine or InferenceEngine()

#     def _generate_worker_id(self) -> str:
#         hostname = socket.gethostname()
#         process_id = os.getpid()
#         return f"{hostname}-{process_id}"

#     def process_next_job(self) -> bool:
#         """
#         Processes one job from Redis.

#         Returns:
#             True  -> job was found and processed
#             False -> no job was available
#         """

#         job_id = self.queue_client.pop_job(timeout=5)

#         if job_id is None:
#             print("No job found in queue.")
#             return False

#         print(f"[{self.worker_id}] Picked job: {job_id}")

#         db = SessionLocal()

#         try:
#             repository = JobRepository(db)

#             job = repository.get_job_by_id(job_id)

#             if job is None:
#                 print(f"[{self.worker_id}] Job not found in database: {job_id}")
#                 return False

#             repository.mark_processing(job_id, self.worker_id)
#             print(f"[{self.worker_id}] Processing job: {job_id}")

#             prediction_result = self.inference_engine.predict(job["features"])

#             repository.mark_completed(job_id, prediction_result)
#             print(f"[{self.worker_id}] Completed job: {job_id}")

#             return True

#         except Exception as error:
#             print(f"[{self.worker_id}] Failed job: {job_id}. Error: {error}")

#             repository = JobRepository(db)
#             repository.mark_failed(job_id, str(error))

#             return False

#         finally:
#             db.close()

#     def start(self):
#         """
#         Continuously listens for jobs.

#         Stop manually using CTRL + C.
#         """

#         print(f"Worker started with worker_id={self.worker_id}")

#         while True:
#             self.process_next_job()



# import os
# import time
# import socket
# import threading
# from concurrent.futures import ThreadPoolExecutor
# from typing import Optional

# from dotenv import load_dotenv

# from app.core.queue_client import QueueClient
# from app.core.inference_engine import InferenceEngine
# from app.db.database import SessionLocal
# from app.db.job_repository import JobRepository


# load_dotenv()


# class WorkerPool:
#     """
#     WorkerPool is responsible for background job processing.

#     Batch 8 version:
#     - Uses ThreadPoolExecutor
#     - Runs 4 threads per worker by default
#     - Each thread continuously pulls jobs from Redis
#     - Each job gets its own database session
#     """

#     def __init__(
#         self,
#         worker_id: Optional[str] = None,
#         queue_client: Optional[QueueClient] = None,
#         inference_engine: Optional[InferenceEngine] = None,
#         threads_per_worker: Optional[int] = None
#     ):
#         self.worker_id = worker_id or self._generate_worker_id()
#         self.queue_client = queue_client or QueueClient()
#         self.inference_engine = inference_engine or InferenceEngine()

#         self.threads_per_worker = threads_per_worker or int(
#             os.getenv("THREADS_PER_WORKER", "4")
#         )

#         # This event helps all threads stop cleanly when CTRL + C is pressed.
#         self.stop_event = threading.Event()

#     def _generate_worker_id(self) -> str:
#         hostname = socket.gethostname()
#         process_id = os.getpid()
#         return f"{hostname}-{process_id}"

#     def process_next_job(self, thread_name: str) -> bool:
#         """
#         Processes one job from Redis.

#         Returns:
#             True  -> job was found and processed
#             False -> no job was available
#         """

#         job_id = self.queue_client.pop_job(timeout=5)

#         if job_id is None:
#             print(f"[{self.worker_id} | {thread_name}] No job found in queue.")
#             return False

#         print(f"[{self.worker_id} | {thread_name}] Picked job: {job_id}")

#         db = SessionLocal()

#         try:
#             repository = JobRepository(db)

#             job = repository.get_job_by_id(job_id)

#             if job is None:
#                 print(
#                     f"[{self.worker_id} | {thread_name}] "
#                     f"Job not found in database: {job_id}"
#                 )
#                 return False

#             repository.mark_processing(job_id, self.worker_id)
#             print(f"[{self.worker_id} | {thread_name}] Processing job: {job_id}")

#             prediction_result = self.inference_engine.predict(job["features"])

#             repository.mark_completed(job_id, prediction_result)
#             print(f"[{self.worker_id} | {thread_name}] Completed job: {job_id}")

#             return True

#         except Exception as error:
#             print(
#                 f"[{self.worker_id} | {thread_name}] "
#                 f"Failed job: {job_id}. Error: {error}"
#             )

#             repository = JobRepository(db)
#             repository.mark_failed(job_id, str(error))

#             return False

#         finally:
#             db.close()

#     def worker_loop(self, thread_number: int):
#         """
#         This function runs inside one thread.

#         Each thread continuously:
#         1. Pulls a job from Redis
#         2. Processes the job
#         3. Goes back to Redis for the next job
#         """

#         thread_name = f"thread-{thread_number}"

#         print(f"[{self.worker_id} | {thread_name}] Started.")

#         while not self.stop_event.is_set():
#             self.process_next_job(thread_name)

#         print(f"[{self.worker_id} | {thread_name}] Stopped.")

#     def start(self):
#         """
#         Starts multiple worker threads.

#         Stop manually using CTRL + C.
#         """

#     print(
#         f"Worker started with worker_id={self.worker_id}, "
#         f"threads_per_worker={self.threads_per_worker}"
#     )

#     try:
#         with ThreadPoolExecutor(max_workers=self.threads_per_worker) as executor:
#             for thread_number in range(1, self.threads_per_worker + 1):
#                 executor.submit(self.worker_loop, thread_number)

#             # Keep the main process alive without wasting CPU.
#             while not self.stop_event.is_set():
#                 time.sleep(1)

#     except KeyboardInterrupt:
#         print("Stopping worker...")
#         self.stop_event.set()


import os
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from dotenv import load_dotenv

from app.core.queue_client import QueueClient
from app.core.inference_engine import InferenceEngine
from app.core.retry_policy import RetryPolicy
from app.db.database import SessionLocal
from app.db.job_repository import JobRepository


load_dotenv()


class WorkerPool:
    """
    WorkerPool is responsible for background job processing.

    Batch 9 version:
    - Pulls jobs from Redis
    - Processes jobs using 4 threads
    - Runs ML inference
    - Retries failed jobs up to 3 times
    - Marks permanently failed jobs after retries are exhausted
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        queue_client: Optional[QueueClient] = None,
        inference_engine: Optional[InferenceEngine] = None,
        retry_policy: Optional[RetryPolicy] = None,
        threads_per_worker: Optional[int] = None
    ):
        self.worker_id = worker_id or self._generate_worker_id()
        self.queue_client = queue_client or QueueClient()
        self.inference_engine = inference_engine or InferenceEngine()
        self.retry_policy = retry_policy or RetryPolicy()

        self.threads_per_worker = threads_per_worker or int(
            os.getenv("THREADS_PER_WORKER", "4")
        )

        self.stop_event = threading.Event()

    def _generate_worker_id(self) -> str:
        hostname = socket.gethostname()
        process_id = os.getpid()
        return f"{hostname}-{process_id}"

    def process_next_job(self, thread_name: str) -> bool:
        job_id = self.queue_client.pop_job(timeout=5)

        if job_id is None:
            return False

        print(f"[{self.worker_id} | {thread_name}] Picked job: {job_id}")

        db = SessionLocal()

        try:
            repository = JobRepository(db)

            job = repository.get_job_by_id(job_id)

            if job is None:
                print(
                    f"[{self.worker_id} | {thread_name}] "
                    f"Job not found in database: {job_id}"
                )
                return False

            repository.mark_processing(job_id, self.worker_id)
            print(f"[{self.worker_id} | {thread_name}] Processing job: {job_id}")

            prediction_result = self.inference_engine.predict(job["features"])

            repository.mark_completed(job_id, prediction_result)
            print(f"[{self.worker_id} | {thread_name}] Completed job: {job_id}")

            return True

        except Exception as error:
            error_message = str(error)

            repository = JobRepository(db)
            latest_job = repository.get_job_by_id(job_id)

            if latest_job is None:
                print(
                    f"[{self.worker_id} | {thread_name}] "
                    f"Failed job not found in database: {job_id}"
                )
                return False

            current_retry_count = latest_job["retry_count"]

            if self.retry_policy.should_retry(current_retry_count):
                next_retry_count = self.retry_policy.next_retry_count(
                    current_retry_count
                )

                repository.mark_queued_for_retry(
                    job_id=job_id,
                    error_message=error_message,
                    next_retry_count=next_retry_count
                )

                self.queue_client.push_job(job_id)

                print(
                    f"[{self.worker_id} | {thread_name}] "
                    f"Retrying job: {job_id}. "
                    f"retry_count={next_retry_count}/{self.retry_policy.max_retries}. "
                    f"Error: {error_message}"
                )

            else:
                repository.mark_failed(job_id, error_message)

                print(
                    f"[{self.worker_id} | {thread_name}] "
                    f"Permanently failed job: {job_id}. "
                    f"retry_count={current_retry_count}. "
                    f"Error: {error_message}"
                )

            return False

        finally:
            db.close()

    def worker_loop(self, thread_number: int):
        thread_name = f"thread-{thread_number}"

        print(f"[{self.worker_id} | {thread_name}] Started.")

        while not self.stop_event.is_set():
            self.process_next_job(thread_name)

        print(f"[{self.worker_id} | {thread_name}] Stopped.")

    def start(self):
        print(
            f"Worker started with worker_id={self.worker_id}, "
            f"threads_per_worker={self.threads_per_worker}, "
            f"max_retries={self.retry_policy.max_retries}"
        )

        try:
            with ThreadPoolExecutor(max_workers=self.threads_per_worker) as executor:
                for thread_number in range(1, self.threads_per_worker + 1):
                    executor.submit(self.worker_loop, thread_number)

                while not self.stop_event.is_set():
                    time.sleep(1)

        except KeyboardInterrupt:
            print("Stopping worker...")
            self.stop_event.set()