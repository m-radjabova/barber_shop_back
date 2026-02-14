import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CourseRating(Base):
    __tablename__ = "course_ratings"
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_rating_course_user"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="ratings")
    user = relationship("User")
