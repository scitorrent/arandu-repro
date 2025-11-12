"""RQ task definitions."""

from redis import Redis

from app.config import settings

# Initialize Redis connection
redis_conn = Redis.from_url(settings.redis_url)


def enqueue_job_task(job_id: str):
    """Enqueue a job processing task."""
    from rq import Queue

    queue = Queue("default", connection=redis_conn)
    queue.enqueue("app.worker.main.process_job", job_id, job_timeout=3600)  # 1 hour timeout
