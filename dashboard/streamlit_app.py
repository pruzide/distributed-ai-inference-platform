import os
import requests
import pandas as pd
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


st.set_page_config(
    page_title="AI Inference Monitoring Dashboard",
    layout="wide"
)


st.title("Distributed AI Inference Monitoring Dashboard")

st.caption(
    "Tracks job throughput, latency, retries, failures, reliability, and recent job history."
)


def fetch_json(endpoint: str):
    """
    Calls FastAPI and returns JSON response.
    """
    url = f"{API_BASE_URL}{endpoint}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()


try:
    summary = fetch_json("/metrics/summary")
    recent_jobs = fetch_json("/metrics/recent-jobs?limit=20")

except requests.exceptions.RequestException as error:
    st.error(f"Could not connect to FastAPI service: {error}")
    st.stop()


st.subheader("System Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Jobs", summary["total_jobs"])
col2.metric("Completed Jobs", summary["completed_jobs"])
col3.metric("Failed Jobs", summary["failed_jobs"])
col4.metric("Total Retries", summary["total_retries"])

col5, col6, col7, col8 = st.columns(4)

col5.metric("Queued Jobs", summary["queued_jobs"])
col6.metric("Processing Jobs", summary["processing_jobs"])
col7.metric("Success Rate", f'{summary["success_rate_percent"]}%')
col8.metric("Failure Rate", f'{summary["failure_rate_percent"]}%')

st.subheader("Performance Metrics")

col9, col10, col11 = st.columns(3)

col9.metric("Average Latency", f'{summary["average_latency_ms"]} ms')
col10.metric("Max Latency", f'{summary["max_latency_ms"]} ms')
col11.metric(
    "Throughput",
    f'{summary["throughput_jobs_per_minute"]} jobs/min'
)

st.caption(
    f'Throughput calculated over the last {summary["throughput_window_minutes"]} minutes.'
)


st.subheader("Recent Jobs")

if len(recent_jobs) == 0:
    st.info("No jobs found yet.")
else:
    df = pd.DataFrame(recent_jobs)

    columns_to_show = [
        "job_id",
        "status",
        "retry_count",
        "worker_id",
        "latency_ms",
        "error_message",
        "created_at",
        "completed_at",
    ]

    existing_columns = [col for col in columns_to_show if col in df.columns]

    st.dataframe(
        df[existing_columns],
        width="stretch",
        hide_index=True
    )


st.subheader("Debugging Notes")

st.markdown(
    """
    - `failed_jobs` shows jobs that failed after retry attempts were exhausted.
    - `total_retries` shows how many retry attempts happened across all jobs.
    - `latency_ms` measures worker processing time from `started_at` to `completed_at`.
    - `worker_id` helps debug which worker processed each job.
    - `throughput_jobs_per_minute` shows recent processing speed.
    """
)