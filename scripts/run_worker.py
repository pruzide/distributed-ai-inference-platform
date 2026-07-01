from app.workers.worker_pool import WorkerPool


if __name__ == "__main__":
    worker = WorkerPool()
    worker.start()