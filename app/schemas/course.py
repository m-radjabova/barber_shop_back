from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CourseBase(BaseModel):
    category_id: UUID
    title: str = Field(..., max_length=150)
    description: str | None = None
    image: str | None = None
    level: str | None = None
    price: int = 0

    # ✅ yangi qo‘shilganlar
    duration: int = 0     # masalan: minutlarda
    rating: int = 0       # masalan: 0–5


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    category_id: UUID | None = None
    title: str | None = Field(default=None, max_length=150)
    description: str | None = None
    image: str | None = None
    level: str | None = None
    price: int | None = None

    # ✅ update uchun ham
    duration: int | None = None
    rating: int | None = None


class CourseOut(CourseBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
