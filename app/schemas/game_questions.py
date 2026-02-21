from typing import Any
from pydantic import BaseModel, Field


class GameQuestionsUpsert(BaseModel):
    questions: list[dict[str, Any]] = Field(default_factory=list)


class GameQuestionsOut(BaseModel):
    game_key: str
    questions: list[dict[str, Any]]

