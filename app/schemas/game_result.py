from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GameResultCreate(BaseModel):
    participant_name: str = Field(..., min_length=1, max_length=255)
    participant_mode: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=0)
    metadata: dict | None = None


class GameResultOut(BaseModel):
    id: UUID
    game_key: str
    user_id: UUID | None = None
    participant_name: str
    participant_mode: str
    score: int
    metadata: dict | None = None
    created_at: datetime


class GameLeaderboardOut(BaseModel):
    items: list[GameResultOut]


class GameResultSaveOut(BaseModel):
    status: str = "ok"
