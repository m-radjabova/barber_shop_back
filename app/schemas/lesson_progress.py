from uuid import UUID

from pydantic import BaseModel, Field


class LessonProgressUpsert(BaseModel):
    watched_sec: int = Field(ge=0, description="Watched seconds for this lesson.")
    duration_sec: int | None = Field(default=None, ge=0, description="Optional lesson duration override.")
    completed: bool | None = Field(default=None, description="Force completed state. If null, derived automatically.")


class LessonProgressOut(BaseModel):
    lesson_id: UUID
    watched_sec: int = Field(ge=0)
    completed: bool

    class Config:
        from_attributes = True


class CourseProgressOut(BaseModel):
    course_id: UUID
    total_lessons: int = Field(ge=0)
    completed_lessons: int = Field(ge=0)
    in_progress_lessons: int = Field(ge=0)
    percent: int = Field(ge=0, le=100)
