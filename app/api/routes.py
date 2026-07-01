# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from uuid import uuid4
# from typing import List, Dict, Any


# router = APIRouter()


# TEMP_JOBS: Dict[str,Dict[str,Any]] = {}

# class JobRequest(BaseModel):
#     features: List[float]

# class JobResponse(BaseModel):
#     job_id: str
#     status: str
#     message: str


# @router.get("/health")
# def health_check():
#     return { 
#         "status": "ok",
#         "service": "ai-inference-api"
#     }

# @router.post("/jobs", response_model = JobResponse)
# def submit_job(request: JobRequest):
#     job_id = str(uuid4())

#     TEMP_JOBS[job_id] = {
#         "job_id": job_id,
#         "features": request.features,
#         "status": "queued"
#     }

#     return JobResponse(
#         job_id = job_id,
#         status = "queued",
#         message = "Job submitted successfully"
#     )

# @router.get("/jobs/{job_id}")
# def get_job(job_id: str):
#     job = TEMP_JOBS[job_id]

#     if job is None:
#         raise HTTPException(status_code = 404, detail = "Job not found") # 404 since it signifies NOT FOUND error
    
#     return job


# from typing import List
# from fastapi import APIRouter, HTTPException, Depends
# from pydantic import BaseModel
# from sqlalchemy.orm import Session

# from app.db.database import SessionLocal
# from app.db.job_repository import JobRepository
# from app.core.job_manager import JobManager


# router = APIRouter()


# class JobRequest(BaseModel):
#     features: List[float]


# class JobResponse(BaseModel):
#     job_id: str
#     status: str
#     message: str


# def get_db():
#     """
#     Creates one database session for each API request.
#     After the request finishes, the session is closed.
#     """
#     db = SessionLocal()

#     try:
#         yield db
#     finally:
#         db.close()


# @router.get("/health")
# def health_check():
#     return {
#         "status": "ok",
#         "service": "ai-inference-api"
#     }


# @router.post("/jobs", response_model=JobResponse)
# def submit_job(request: JobRequest, db: Session = Depends(get_db)):
#     repository = JobRepository(db)
#     manager = JobManager(repository)

#     return manager.submit_job(request.features)


# @router.get("/jobs/{job_id}")
# def get_job(job_id: str, db: Session = Depends(get_db)):
#     repository = JobRepository(db)
#     manager = JobManager(repository)

#     job = manager.get_job(job_id)

#     if job is None:
#         raise HTTPException(status_code=404, detail="Job not found")

#     return job

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.job_repository import JobRepository
from app.core.job_manager import JobManager
from app.core.queue_client import QueueClient
from app.metrics.metrics_tracker import MetricsTracker


router = APIRouter()


class JobRequest(BaseModel):
    features: List[float]


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


def get_db():
    """
    Creates one database session for each API request.
    After the request finishes, the session is closed.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-inference-api"
    }


@router.get("/queue/health")
def queue_health_check():
    queue_client = QueueClient()

    return {
        "redis_status": "ok" if queue_client.ping() else "not_ok",
        "queue_name": queue_client.queue_name,
        "queue_length": queue_client.get_queue_length()
    }


@router.post("/jobs", response_model=JobResponse)
def submit_job(request: JobRequest, db: Session = Depends(get_db)):
    repository = JobRepository(db)
    queue_client = QueueClient()
    manager = JobManager(repository, queue_client)

    return manager.submit_job(request.features)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    repository = JobRepository(db)
    manager = JobManager(repository)

    job = manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/metrics/summary")
def get_metrics_summary(window_minutes: int = 10, db: Session = Depends(get_db)):
    metrics_tracker = MetricsTracker(db)
    return metrics_tracker.get_summary(window_minutes=window_minutes)


@router.get("/metrics/recent-jobs")
def get_recent_jobs(limit: int = 20, db: Session = Depends(get_db)):
    metrics_tracker = MetricsTracker(db)
    return metrics_tracker.get_recent_jobs(limit=limit)