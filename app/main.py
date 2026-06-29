from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title = "Distributed AI Inference & Job Scheduling Platform",
    description="FastAPI backend for submitting and tracking ML inference jobs",
    version="0.1.0"
)

app.include_router(router)