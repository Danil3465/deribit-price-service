import aiohttp

from app.config import settings


class DeribitClient:
    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or settings.deribit_base_url

    async def get_index_price(self, ticker: str) -> float:
        url = f"{self._base_url}/public/get_index_price"
        params = {"index_name": ticker}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        return data["result"]["index_price"]