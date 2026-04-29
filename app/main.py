from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth_router,
    barber_router,
    booking_router,
    public_booking_router,
    telegram_router,
    user_router,
)
from app.services.telegram_polling import telegram_polling_runner

app = FastAPI(title="Barber Shop API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(barber_router)
app.include_router(public_booking_router)
app.include_router(booking_router)
app.include_router(telegram_router)


@app.get("/health", tags=["Health"])
def healthcheck():
    return {"status": "ok"}


@app.on_event("startup")
async def start_telegram_polling():
    await telegram_polling_runner.start()


@app.on_event("shutdown")
async def stop_telegram_polling():
    await telegram_polling_runner.stop()
