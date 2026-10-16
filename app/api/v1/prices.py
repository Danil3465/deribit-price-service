from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_price_service
from app.schemas.price import PriceResponse
from app.services.price import PriceService

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("", response_model=list[PriceResponse])
async def get_all_prices(
    ticker: Annotated[str, Query(...)],
    service: Annotated[PriceService, Depends(get_price_service)],
) -> list[PriceResponse]:
    return await service.get_all(ticker)


@router.get("/latest", response_model=PriceResponse)
async def get_latest_price(
    ticker: Annotated[str, Query(...)],
    service: Annotated[PriceService, Depends(get_price_service)],
) -> PriceResponse:
    price = await service.get_latest(ticker)
    if price is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data for ticker {ticker}",
        )
    return price


@router.get("/by-date", response_model=list[PriceResponse])
async def get_prices_by_date(
    ticker: Annotated[str, Query(...)],
    from_ts: Annotated[int, Query(...)],
    to_ts: Annotated[int, Query(...)],
    service: Annotated[PriceService, Depends(get_price_service)],
) -> list[PriceResponse]:
    return await service.get_by_period(ticker, from_ts, to_ts)