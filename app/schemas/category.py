from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: str | None = None
    icon: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    description: str | None = None
    icon: str | None = None


class CategoryOut(CategoryBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True