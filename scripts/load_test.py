import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

import requests


def get_metrics(api_base_url: str) -> Dict[str, Any]:
    response = requests.get(
        f"{api_base_url}/metrics/summary",
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def submit_job(api_base_url: str, features: List[float]) -> Dict[str, Any]:
    response = requests.post(
        f"{api_base_url}/jobs",
        json={"features": features},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def run_load_test(
    api_base_url: str,
    total_jobs: int,
    concurrency: int,
    poll_interval_seconds: int,
    max_wait_seconds: int
):
    print("=" * 70)
    print("Distributed AI Inference Load Test")
    print("=" * 70)

    print(f"API URL      : {api_base_url}")
    print(f"Total Jobs   : {total_jobs}")
    print(f"Concurrency  : {concurrency}")
    print("=" * 70)

    before = get_metrics(api_base_url)

    before_total = before["total_jobs"]
    before_completed = before["completed_jobs"]
    before_failed = before["failed_jobs"]
    before_terminal = before_completed + before_failed

    print("\nMetrics before load test:")
    print(before)

    features = [650, 50000, 2, 0, 5]

    submitted_jobs = []
    failed_submissions = 0

    start_submit_time = time.time()

    print("\nSubmitting jobs...")

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(submit_job, api_base_url, features)
            for _ in range(total_jobs)
        ]

        for index, future in enumerate(as_completed(futures), start=1):
            try:
                result = future.result()
                submitted_jobs.append(result["job_id"])
            except Exception as error:
                failed_submissions += 1
                print(f"Submission failed: {error}")

            if index % 100 == 0:
                print(f"Submission progress: {index}/{total_jobs}")

    end_submit_time = time.time()

    successful_submissions = len(submitted_jobs)

    print("\nSubmission finished.")
    print(f"Successful submissions : {successful_submissions}")
    print(f"Failed submissions     : {failed_submissions}")
    print(f"Submission time sec    : {round(end_submit_time - start_submit_time, 2)}")

    expected_total = before_total + successful_submissions
    expected_terminal = before_terminal + successful_submissions

    print("\nWaiting for workers to complete submitted jobs...")

    wait_start_time = time.time()

    final_metrics = None

    while True:
        current = get_metrics(api_base_url)

        current_total = current["total_jobs"]
        current_completed = current["completed_jobs"]
        current_failed = current["failed_jobs"]
        current_terminal = current_completed + current_failed
        current_queued = current["queued_jobs"]
        current_processing = current["processing_jobs"]

        completed_delta = current_completed - before_completed
        failed_delta = current_failed - before_failed
        terminal_delta = current_terminal - before_terminal

        print(
            f"total={current_total}/{expected_total} | "
            f"new_terminal={terminal_delta}/{successful_submissions} | "
            f"new_completed={completed_delta} | "
            f"new_failed={failed_delta} | "
            f"queued={current_queued} | "
            f"processing={current_processing}"
        )

        if current_total >= expected_total and current_terminal >= expected_terminal:
            final_metrics = current
            break

        elapsed = time.time() - wait_start_time

        if elapsed > max_wait_seconds:
            print("\nLoad test timed out before all jobs reached terminal state.")
            final_metrics = current
            break

        time.sleep(poll_interval_seconds)

    total_elapsed = time.time() - start_submit_time

    after_completed = final_metrics["completed_jobs"]
    after_failed = final_metrics["failed_jobs"]

    new_completed = after_completed - before_completed
    new_failed = after_failed - before_failed
    new_terminal = new_completed + new_failed

    print("\n" + "=" * 70)
    print("Load Test Proof Summary")
    print("=" * 70)
    print(f"Jobs requested              : {total_jobs}")
    print(f"Jobs submitted successfully : {successful_submissions}")
    print(f"New completed jobs          : {new_completed}")
    print(f"New failed jobs             : {new_failed}")
    print(f"New terminal jobs           : {new_terminal}")
    print(f"Total elapsed seconds       : {round(total_elapsed, 2)}")
    print(f"Final total jobs            : {final_metrics['total_jobs']}")
    print(f"Final completed jobs        : {final_metrics['completed_jobs']}")
    print(f"Final failed jobs           : {final_metrics['failed_jobs']}")
    print(f"Final total retries         : {final_metrics['total_retries']}")
    print(f"Average latency ms          : {final_metrics['average_latency_ms']}")
    print(f"Max latency ms              : {final_metrics['max_latency_ms']}")
    print(f"Throughput jobs/min         : {final_metrics['throughput_jobs_per_minute']}")
    print(f"Success rate percent        : {final_metrics['success_rate_percent']}")
    print(f"Failure rate percent        : {final_metrics['failure_rate_percent']}")
    print("=" * 70)

    if successful_submissions >= 1000 and new_terminal >= 1000:
        print("RESULT: PASS - 1,000+ submitted jobs reached terminal state.")
    else:
        print("RESULT: CHECK - 1,000+ completed proof not reached yet.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--api-base-url",
        default="http://127.0.0.1:8000"
    )

    parser.add_argument(
        "--jobs",
        type=int,
        default=1000
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=50
    )

    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=3
    )

    parser.add_argument(
        "--max-wait-seconds",
        type=int,
        default=300
    )

    args = parser.parse_args()

    run_load_test(
        api_base_url=args.api_base_url,
        total_jobs=args.jobs,
        concurrency=args.concurrency,
        poll_interval_seconds=args.poll_interval_seconds,
        max_wait_seconds=args.max_wait_seconds
    )