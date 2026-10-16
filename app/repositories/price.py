from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price import Price


class PriceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, ticker: str, price: float, timestamp: int) -> Price:
        record = Price(ticker=ticker, price=price, timestamp=timestamp)
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_all_by_ticker(self, ticker: str) -> list[Price]:
        result = await self._session.execute(
            select(Price).where(Price.ticker == ticker).order_by(Price.timestamp)
        )
        return list(result.scalars().all())

    async def get_latest_by_ticker(self, ticker: str) -> Price | None:
        result = await self._session.execute(
            select(Price)
            .where(Price.ticker == ticker)
            .order_by(Price.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_ticker_and_period(
        self, ticker: str, from_ts: int, to_ts: int
    ) -> list[Price]:
        result = await self._session.execute(
            select(Price)
            .where(
                Price.ticker == ticker,
                Price.timestamp >= from_ts,
                Price.timestamp <= to_ts,
            )
            .order_by(Price.timestamp)
        )
        return list(result.scalars().all())