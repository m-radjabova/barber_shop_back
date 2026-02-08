from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, AnyUrl


class LessonBase(BaseModel):
    course_id: UUID
    title: str = Field(..., max_length=150)
    description: str | None = None
    order: int = 1
    is_free: bool = False
    video_url: AnyUrl  
    duration_sec: int | None = None


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=150)
    description: str | None = None
    order: int | None = None
    is_free: bool | None = None
    video_url: AnyUrl | None = None
    duration_sec: int | None = None


class LessonOut(LessonBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
