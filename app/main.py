import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.config import settings
from app import models
from app.routers.user_router import router as users_router
from app.routers.auth_router import router as auth_router
from app.routers.game_questions_router import router as game_questions_router
from app.routers.game_feedback_router import router as game_feedback_router
from app.routers.game_result_router import router as game_result_router

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def create_tables_on_startup():
    if not settings.AUTO_CREATE_TABLES:
        return

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Failed to auto-create database tables")


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(game_questions_router)
app.include_router(game_feedback_router)
app.include_router(game_result_router)
