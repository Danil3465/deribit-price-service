from app.models.price import Price
from app.repositories.price import PriceRepository


class PriceService:
    def __init__(self, repository: PriceRepository) -> None:
        self._repository = repository

    async def get_all(self, ticker: str) -> list[Price]:
        return await self._repository.get_all_by_ticker(ticker)

    async def get_latest(self, ticker: str) -> Price | None:
        return await self._repository.get_latest_by_ticker(ticker)

    async def get_by_period(
        self, ticker: str, from_ts: int, to_ts: int
    ) -> list[Price]:
        return await self._repository.get_by_ticker_and_period(ticker, from_ts, to_ts)