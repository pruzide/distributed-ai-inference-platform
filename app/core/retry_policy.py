import os
from dotenv import load_dotenv


load_dotenv()


class RetryPolicy:
    """
    RetryPolicy decides whether a failed job should be retried.

    retry_count means:
    how many retry attempts have already been scheduled.

    If max_retries = 3:
    - first failure  -> retry_count becomes 1
    - second failure -> retry_count becomes 2
    - third failure  -> retry_count becomes 3
    - fourth failure -> permanently failed
    """

    def __init__(self, max_retries: int | None = None):
        self.max_retries = max_retries or int(os.getenv("MAX_RETRIES", "3"))

    def should_retry(self, current_retry_count: int) -> bool:
        return current_retry_count < self.max_retries

    def next_retry_count(self, current_retry_count: int) -> int:
        return current_retry_count + 1