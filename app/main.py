from fastapi import FastAPI

from app.api.v1.prices import router as prices_router

app = FastAPI(title="Deribit Price Service")

app.include_router(prices_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}