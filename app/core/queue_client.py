import os
from typing import Optional

import redis
from dotenv import load_dotenv


load_dotenv()


class QueueClient:
    """
    QueueClient is responsible only for Redis queue operations.

    It does not know about FastAPI.
    It does not know about PostgreSQL.
    It does not run ML inference.

    Its job is simple:
    push job IDs into Redis and later allow workers to pull them.
    """

    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.queue_name = os.getenv("REDIS_QUEUE_NAME", "inference_jobs")

        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )

    def ping(self) -> bool:
        """
        Checks whether Redis is reachable.
        """
        return self.client.ping()

    def push_job(self, job_id: str) -> int:
        """
        Pushes a job ID into the Redis queue.

        rpush means:
        add this job ID to the right side of the queue.
        """
        queue_length = self.client.rpush(self.queue_name, job_id)
        return queue_length

    def pop_job(self, timeout: int = 5) -> Optional[str]:
        """
        Pulls a job ID from Redis.

        blpop means:
        wait for a job for up to timeout seconds.
        If no job comes, return None.

        This will be used by workers in Batch 7.
        """
        result = self.client.blpop(self.queue_name, timeout=timeout)

        if result is None:
            return None

        queue_name, job_id = result
        return job_id

    def get_queue_length(self) -> int:
        """
        Returns how many jobs are currently waiting in Redis.
        """
        return self.client.llen(self.queue_name)