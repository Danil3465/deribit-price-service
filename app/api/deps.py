from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.repositories.price import PriceRepository
from app.services.price import PriceService


async def get_price_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PriceService:
    repository = PriceRepository(session)
    return PriceService(repository)