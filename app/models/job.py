from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.sql import func


from app.db.database import Base

class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key = True, index = True)

    # Input sent by the user/API
    features = Column(JSON, nullable = False)

    # queued, processing, completed, failed
    status = Column(String, nullable = False, index = True, default = "queued")

    # ML prediction output will be stored later
    prediction_result = Column(JSON, nullable = True)

    # Error details if a job fails
    error_message = Column(Text, nullable = True)

    # Number of retry attempts already used
    retry_count = Column(Integer, nullable = False, default = 0)

    # Worker/Service that processed the job
    worker_id = Column(String, nullable = True)

    # Timing fields for monitoring
    created_at = Column(DateTime(timezone = True), server_default = func.now(), nullable = False)
    started_at = Column(DateTime(timezone = True), nullable = True)
    completed_at = Column(DateTime(timezone = True), nullable = True)

    # Will help track latency/performance
    latency_ms = Column(Float, nullable = True)
