from celery import Celery

from app.config import settings

celery_app = Celery(
    "deribit_price_service",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.prices"],
)

celery_app.conf.beat_schedule = {
    "fetch-prices-every-minute": {
        "task": "app.tasks.prices.fetch_and_save_prices",
        "schedule": settings.fetch_interval_seconds,
    },
}

celery_app.conf.timezone = "UTC"
celery_app.conf.broker_connection_retry_on_startup = True