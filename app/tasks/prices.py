import asyncio
import logging
import time

from app.clients.deribit import DeribitClient
from app.config import settings
from app.database import async_session_maker
from app.repositories.price import PriceRepository
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _fetch_and_save() -> None:
    client = DeribitClient()
    timestamp = int(time.time())

    async with async_session_maker() as session:
        repository = PriceRepository(session)
        for ticker in settings.tickers:
            try:
                price = await client.get_index_price(ticker)
                await repository.save(ticker, price, timestamp)
                logger.info("Saved %s = %s", ticker, price)
            except Exception:
                logger.exception("Failed to fetch %s", ticker)


@celery_app.task(name="app.tasks.prices.fetch_and_save_prices")
def fetch_and_save_prices() -> None:
    asyncio.run(_fetch_and_save())