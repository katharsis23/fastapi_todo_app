from celery import Celery
from app.config.config import REDIS_CONFIG

celery_app = Celery(
    "worker",
    broker=REDIS_CONFIG.redis_url.get_secret_value(),
    backend=REDIS_CONFIG.redis_url.get_secret_value(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
