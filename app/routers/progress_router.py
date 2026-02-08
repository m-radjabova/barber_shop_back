from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.lesson_progress import CourseProgressOut, LessonProgressOut, LessonProgressUpsert
from app.services import progress_service

router = APIRouter(prefix="/me", tags=["Progress"])


def _to_lesson_progress_out(*, lesson_id: UUID, watched_sec: int, completed: bool) -> dict:
    return {
        "lesson_id": lesson_id,
        "watched_sec": watched_sec,
        "completed": completed,
    }


@router.get("/lessons/{lesson_id}/progress", response_model=LessonProgressOut)
def get_my_lesson_progress(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    progress = progress_service.get_lesson_progress(db, user_id=user.id, lesson_id=lesson_id)
    return _to_lesson_progress_out(
        lesson_id=lesson_id,
        watched_sec=progress.watched_sec,
        completed=progress.completed,
    )


@router.put("/lessons/{lesson_id}/progress", response_model=LessonProgressOut)
def upsert_my_lesson_progress(
    lesson_id: UUID,
    payload: LessonProgressUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    progress = progress_service.upsert_lesson_progress(
        db,
        user_id=user.id,
        lesson_id=lesson_id,
        watched_sec=payload.watched_sec,
        duration_sec=payload.duration_sec,
        completed=payload.completed,
    )
    return _to_lesson_progress_out(
        lesson_id=lesson_id,
        watched_sec=progress.watched_sec,
        completed=progress.completed,
    )


@router.get("/courses/{course_id}/progress", response_model=CourseProgressOut)
def get_my_course_progress(
    course_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return progress_service.get_course_progress(db, user_id=user.id, course_id=course_id)
