import pytest

from app.repositories.price import PriceRepository


@pytest.mark.asyncio
async def test_save_and_get_all(test_session):
    repo = PriceRepository(test_session)
    await repo.save("btc_usd", 80000.0, 1000)
    await repo.save("btc_usd", 81000.0, 2000)

    result = await repo.get_all_by_ticker("btc_usd")
    assert len(result) == 2
    assert result[0].timestamp == 1000
    assert result[1].timestamp == 2000


@pytest.mark.asyncio
async def test_get_latest(test_session):
    repo = PriceRepository(test_session)
    await repo.save("eth_usd", 2000.0, 1000)
    await repo.save("eth_usd", 2100.0, 2000)

    latest = await repo.get_latest_by_ticker("eth_usd")
    assert latest is not None
    assert latest.timestamp == 2000
    assert float(latest.price) == 2100.0


@pytest.mark.asyncio
async def test_get_by_period(test_session):
    repo = PriceRepository(test_session)
    await repo.save("btc_usd", 100.0, 1000)
    await repo.save("btc_usd", 200.0, 2000)
    await repo.save("btc_usd", 300.0, 3000)

    result = await repo.get_by_ticker_and_period("btc_usd", 1500, 2500)
    assert len(result) == 1
    assert result[0].timestamp == 2000


@pytest.mark.asyncio
async def test_get_latest_empty(test_session):
    repo = PriceRepository(test_session)
    latest = await repo.get_latest_by_ticker("btc_usd")
    assert latest is None