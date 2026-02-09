from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LessonProgressUpsert(BaseModel):
    progress_percent: int = Field(..., ge=0, le=100)
    last_position_sec: int = Field(0, ge=0)
    is_completed: bool | None = None


class LessonProgressOut(BaseModel):
    id: UUID
    user_id: UUID
    course_id: UUID
    lesson_id: UUID
    progress_percent: int
    last_position_sec: int
    is_completed: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseProgressOut(BaseModel):
    course_id: UUID
    total_lessons: int
    completed_lessons: int
    progress_percent: int
    lessons: list[LessonProgressOut]
