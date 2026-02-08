import os
import uuid
import shutil
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.category import Category
from app.schemas.course import CourseUpdate  # CourseCreate routerda Form orqali keladi


# =========================
# Image helpers
# =========================
UPLOAD_DIR = "app/static/uploads/courses"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _save_course_image(image: UploadFile) -> str:
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and WEBP images are allowed")

    ext = ALLOWED_TYPES[image.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save image")

    return f"/static/uploads/courses/{filename}"


def _delete_old_image_if_exists(image: str | None):
    if not image:
        return
    old_path = image.replace("/static/", "app/static/")
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass


# =========================
# CRUD
# =========================
def _ensure_category_exists(db: Session, category_id: UUID):
    exists = db.query(Category).filter(Category.id == category_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Category not found")


def create_course(
    db: Session,
    *,
    category_id: UUID,
    title: str,
    description: str | None = None,
    level: str | None = None,
    price: int = 0,
    duration: int = 0,
    rating: int = 0,
    image: UploadFile | None = None,
):
    _ensure_category_exists(db, category_id)

    image_path = _save_course_image(image) if image else None

    course = Course(
        category_id=category_id,
        title=title,
        description=description,
        level=level,
        price=price,
        duration=duration,
        rating=rating,
        image=image_path,
    )

    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def get_courses(db: Session, category_id: UUID | None = None):
    q = db.query(Course)
    if category_id:
        q = q.filter(Course.category_id == category_id)
    return q.order_by(Course.created_at.desc()).all()


def get_course_by_id(db: Session, course_id: UUID):
    return db.query(Course).filter(Course.id == course_id).first()


def update_course(db: Session, course_id: UUID, payload: CourseUpdate):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data:
        _ensure_category_exists(db, data["category_id"])

    for k, v in data.items():
        setattr(course, k, v)

    db.commit()
    db.refresh(course)
    return course


def update_course_image(db: Session, course: Course, image: UploadFile):
    _delete_old_image_if_exists(course.image)
    course.image = _save_course_image(image)

    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course_id: UUID):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    _delete_old_image_if_exists(course.image)

    db.delete(course)
    db.commit()
    return None
