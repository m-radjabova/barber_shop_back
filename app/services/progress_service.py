from uuid import UUID
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress

AUTO_COMPLETE_THRESHOLD = 0.9


def _resolve_duration(*, lesson_duration: int | None, requested_duration: int | None) -> int:
    return max(lesson_duration or requested_duration or 0, 0)


def _normalize_watched_seconds(*, watched_sec: int, duration: int) -> int:
    normalized = max(0, int(watched_sec))
    if duration > 0:
        normalized = min(normalized, duration)
    return normalized


def _resolve_completed_flag(*, completed: bool | None, watched_sec: int, duration: int) -> bool:
    if completed is not None:
        return completed

    if duration <= 0:
        return False

    return (watched_sec / duration) >= AUTO_COMPLETE_THRESHOLD


def upsert_lesson_progress(
    db: Session,
    *,
    user_id: UUID,
    lesson_id: UUID,
    watched_sec: int,
    duration_sec: int | None,
    completed: bool | None,
) -> LessonProgress:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    duration = _resolve_duration(lesson_duration=lesson.duration_sec, requested_duration=duration_sec)
    watched_sec = _normalize_watched_seconds(watched_sec=watched_sec, duration=duration)
    completed = _resolve_completed_flag(completed=completed, watched_sec=watched_sec, duration=duration)

    prog = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        .first()
    )

    if not prog:
        prog = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            watched_sec=watched_sec,
            completed=completed,
        )
        db.add(prog)
    else:
        # Never move progress backwards.
        prog.watched_sec = max(prog.watched_sec, watched_sec)
        prog.completed = prog.completed or completed

    db.commit()
    db.refresh(prog)
    return prog


def get_lesson_progress(db: Session, *, user_id: UUID, lesson_id: UUID) -> LessonProgress:
    prog = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not prog:
        # Virtual row for users who have not started the lesson yet.
        return LessonProgress(user_id=user_id, lesson_id=lesson_id, watched_sec=0, completed=False)
    return prog


def get_course_progress(db: Session, *, user_id: UUID, course_id: UUID) -> dict[str, Any]:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).all()
    total = len(lessons)
    if total == 0:
        return {
            "course_id": course_id,
            "total_lessons": 0,
            "completed_lessons": 0,
            "in_progress_lessons": 0,
            "percent": 0,
        }

    lesson_ids = [l.id for l in lessons]

    progress_rows = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user_id, LessonProgress.lesson_id.in_(lesson_ids))
        .all()
    )
    progress_map = {p.lesson_id: p for p in progress_rows}

    completed_lessons = 0
    in_progress_lessons = 0
    percent_sum = 0.0

    for l in lessons:
        p = progress_map.get(l.id)
        if not p:
            continue

        if p.completed:
            completed_lessons += 1
            percent_sum += 1.0
        else:
            dur = l.duration_sec or 0
            if dur > 0 and p.watched_sec > 0:
                in_progress_lessons += 1
                percent_sum += min(p.watched_sec / dur, 1.0)

    percent = int(round((percent_sum / total) * 100))

    return {
        "course_id": course_id,
        "total_lessons": total,
        "completed_lessons": completed_lessons,
        "in_progress_lessons": in_progress_lessons,
        "percent": max(0, min(percent, 100)),
    }
