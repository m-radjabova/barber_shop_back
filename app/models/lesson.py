import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint("course_id", "order", name="uq_lessons_course_order"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    order = Column(Integer, default=1)

    is_free = Column(Boolean, default=False)

    video_url = Column(String, nullable=False)
    duration_sec = Column(Integer, nullable=True) 

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="lessons")

    assignments = relationship(
        "Assignment",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )