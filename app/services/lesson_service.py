from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.lesson import Lesson
from app.models.course import Course
from app.schemas.lesson import LessonCreate, LessonUpdate


def _ensure_course_exists(db: Session, course_id: UUID):
    exists = db.query(Course).filter(Course.id == course_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Course not found")


def create_lesson(db: Session, payload: LessonCreate):
    _ensure_course_exists(db, payload.course_id)

    lesson = Lesson(
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        order=payload.order,
        is_free=payload.is_free,
        video_url=str(payload.video_url),
        duration_sec=payload.duration_sec,
    )

    db.add(lesson)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This lesson order already exists in the course")

    db.refresh(lesson)
    return lesson


def get_lessons(db: Session, course_id: UUID):
    _ensure_course_exists(db, course_id)
    return (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.order.asc())
        .all()
    )


def get_lesson_by_id(db: Session, lesson_id: UUID):
    return db.query(Lesson).filter(Lesson.id == lesson_id).first()


def update_lesson(db: Session, lesson_id: UUID, payload: LessonUpdate):
    lesson = get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    data = payload.model_dump(exclude_unset=True)

    if "video_url" in data and data["video_url"] is not None:
        data["video_url"] = str(data["video_url"])

    for k, v in data.items():
        setattr(lesson, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This lesson order already exists in the course")

    db.refresh(lesson)
    return lesson


def delete_lesson(db: Session, lesson_id: UUID):
    lesson = get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    db.delete(lesson)
    db.commit()
    return None
