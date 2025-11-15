"""Review processing tasks for RQ worker."""

import logging

from redis import Redis
from rq import Queue

from app.config import settings

logger = logging.getLogger(__name__)

# Create dedicated queue for reviews (separate from jobs queue)
redis_conn = Redis.from_url(settings.redis_url)
review_queue = Queue("reviews", connection=redis_conn)


def enqueue_review_task(review_id: str) -> None:
    """
    Enqueue a review processing task.

    Args:
        review_id: UUID of the review to process
    """
    from app.worker.review_processor import process_review

    job = review_queue.enqueue(process_review, review_id, job_timeout=90)  # 90s timeout
    logger.info(f"Enqueued review task {review_id} as job {job.id}")

