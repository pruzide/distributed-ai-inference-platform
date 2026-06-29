from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import List, Dict, Any


router = APIRouter()


TEMP_JOBS: Dict[str,Dict[str,Any]] = {}

class JobRequest(BaseModel):
    features: List[float]

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.get("/health")
def health_check():
    return { 
        "status": "ok",
        "service": "ai-inference-api"
    }

@router.post("/jobs", response_model = JobResponse)
def submit_job(request: JobRequest):
    job_id = str(uuid4())

    TEMP_JOBS[job_id] = {
        "job_id": job_id,
        "features": request.features,
        "status": "queued"
    }

    return JobResponse(
        job_id = job_id,
        status = "queued",
        message = "Job submitted successfully"
    )

@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = TEMP_JOBS[job_id]

    if job is None:
        raise HTTPException(status_code = 404, detail = "Job not found") # 404 since it signifies NOT FOUND error
    
    return job


