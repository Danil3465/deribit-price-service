import pytest

from app.repositories.price import PriceRepository


@pytest.mark.asyncio
async def test_get_all(client, test_session):
    repo = PriceRepository(test_session)
    await repo.save("btc_usd", 80000.0, 1000)

    response = await client.get("/api/v1/prices", params={"ticker": "btc_usd"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "btc_usd"


@pytest.mark.asyncio
async def test_get_latest(client, test_session):
    repo = PriceRepository(test_session)
    await repo.save("eth_usd", 2000.0, 1000)
    await repo.save("eth_usd", 2100.0, 2000)

    response = await client.get("/api/v1/prices/latest", params={"ticker": "eth_usd"})
    assert response.status_code == 200
    assert response.json()["timestamp"] == 2000


@pytest.mark.asyncio
async def test_get_latest_not_found(client):
    response = await client.get("/api/v1/prices/latest", params={"ticker": "btc_usd"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_by_date(client, test_session):
    repo = PriceRepository(test_session)
    await repo.save("btc_usd", 100.0, 1000)
    await repo.save("btc_usd", 200.0, 2000)
    await repo.save("btc_usd", 300.0, 3000)

    response = await client.get(
        "/api/v1/prices/by-date",
        params={"ticker": "btc_usd", "from_ts": 1500, "to_ts": 2500},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["timestamp"] == 2000


@pytest.mark.asyncio
async def test_missing_ticker(client):
    response = await client.get("/api/v1/prices")
    assert response.status_code == 422