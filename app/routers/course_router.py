from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.course import (
    CourseOut,
    CourseRatingSummaryOut,
    CourseRatingUpsert,
    CourseUpdate,
)
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    category_id: UUID = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    level: str | None = Form(None),
    price: int = Form(0),
    duration: int = Form(0),
    rating: int = Form(0),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return course_service.create_course(
        db,
        category_id=category_id,
        title=title,
        description=description,
        level=level,
        price=price,
        duration=duration,
        rating=rating,
        image=image,
    )


@router.get("/", response_model=list[CourseOut])
def list_courses(
    category_id: UUID | None = None,
    level: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return course_service.get_courses(
        db,
        category_id=category_id,
        level=level,
        search=search,
    )


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: UUID, db: Session = Depends(get_db)):
    course = course_service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/rating", response_model=CourseRatingSummaryOut)
def get_course_rating(
    course_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return course_service.get_course_rating_summary(db, course_id, current_user.id)


@router.post("/{course_id}/rating", response_model=CourseRatingSummaryOut)
def upsert_course_rating(
    course_id: UUID,
    payload: CourseRatingUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return course_service.upsert_course_rating(
        db,
        course_id=course_id,
        user_id=current_user.id,
        score=payload.score,
    )


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return course_service.update_course(db, course_id, payload)


@router.post("/{course_id}/image", response_model=CourseOut)
def upload_course_image(
    course_id: UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    course = course_service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course_service.update_course_image(db, course, image)


@router.delete("/{course_id}", status_code=204)
def delete_course(
    course_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    course_service.delete_course(db, course_id)
    return
