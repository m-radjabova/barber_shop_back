from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.course import Course
from app.models.course_progress import LessonProgress
from app.models.lesson import Lesson
from app.schemas.progress import CourseProgressOut, LessonProgressOut, LessonProgressUpsert

router = APIRouter(prefix="/progress", tags=["Progress"])


def _ensure_course_and_lesson(db: Session, course_id: UUID, lesson_id: UUID) -> Lesson:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if lesson.course_id != course_id:
        raise HTTPException(status_code=400, detail="Lesson does not belong to this course")

    return lesson


@router.get("/courses/{course_id}", response_model=CourseProgressOut)
def get_course_progress(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    total_lessons = db.query(Lesson).filter(Lesson.course_id == course_id).count()
    rows = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.course_id == course_id,
        )
        .order_by(LessonProgress.updated_at.desc())
        .all()
    )

    completed_lessons = sum(1 for row in rows if row.is_completed)
    progress_percent = (
        round(sum(row.progress_percent for row in rows) / total_lessons) if total_lessons > 0 else 0
    )

    return CourseProgressOut(
        course_id=course_id,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        progress_percent=progress_percent,
        lessons=[LessonProgressOut.model_validate(row) for row in rows],
    )


@router.put("/courses/{course_id}/lessons/{lesson_id}", response_model=LessonProgressOut)
def upsert_lesson_progress(
    course_id: UUID,
    lesson_id: UUID,
    payload: LessonProgressUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _ensure_course_and_lesson(db, course_id, lesson_id)

    normalized_progress = max(0, min(100, payload.progress_percent))
    is_completed = payload.is_completed if payload.is_completed is not None else normalized_progress >= 100
    if is_completed:
        normalized_progress = 100

    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )

    if progress:
        progress.course_id = course_id
        progress.progress_percent = normalized_progress
        progress.last_position_sec = payload.last_position_sec
        progress.is_completed = is_completed
    else:
        progress = LessonProgress(
            user_id=current_user.id,
            course_id=course_id,
            lesson_id=lesson_id,
            progress_percent=normalized_progress,
            last_position_sec=payload.last_position_sec,
            is_completed=is_completed,
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress
