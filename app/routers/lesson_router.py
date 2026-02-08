from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonOut, LessonUpdate
from app.services import lesson_service

router = APIRouter(tags=["Lessons"])


# ✅ Public: course lessons
@router.get("/courses/{course_id}/lessons", response_model=list[LessonOut])
def list_lessons(course_id: UUID, db: Session = Depends(get_db)):
    return lesson_service.get_lessons(db, course_id)


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: UUID, db: Session = Depends(get_db)):
    lesson = lesson_service.get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


# ✅ Admin: create/update/delete
@router.post("/lessons", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return lesson_service.create_lesson(db, payload)


@router.put("/lessons/{lesson_id}", response_model=LessonOut)
def update_lesson(
    lesson_id: UUID,
    payload: LessonUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return lesson_service.update_lesson(db, lesson_id, payload)


@router.delete("/lessons/{lesson_id}", status_code=204)
def delete_lesson(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    lesson_service.delete_lesson(db, lesson_id)
    return
