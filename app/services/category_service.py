import os
import uuid
import shutil
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryUpdate

UPLOAD_DIR = "app/static/uploads/categories"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def save_icon(image: UploadFile) -> str:
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, and WEBP images are allowed",
        )

    ext = ALLOWED_TYPES[image.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save icon")

    return f"/static/uploads/categories/{filename}"


def delete_old_icon_if_exists(icon: str | None):
    if not icon:
        return
    old_path = icon.replace("/static/", "app/static/")
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception:
            pass


def check_name(db: Session, name: str) -> bool:
    return db.query(Category).filter(Category.name == name).first() is not None


def get_categories(db: Session):
    return db.query(Category).order_by(Category.created_at.desc()).all()


def get_category_by_id(db: Session, category_id):
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(
    db: Session,
    *,
    name: str,
    description: str | None = None,
    icon_file: UploadFile | None = None,
):
    if check_name(db, name):
        raise HTTPException(status_code=400, detail="Category name already exists")

    icon_path = None
    if icon_file is not None:
        icon_path = save_icon(icon_file)

    new_category = Category(
        name=name,
        description=description,
        icon=icon_path,   # ✅ file bo'lsa shu yerga yoziladi
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def update_category(db: Session, category_id, category_data: CategoryUpdate):
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != db_category.name:
        if check_name(db, update_data["name"]):
            raise HTTPException(status_code=400, detail="Category name already exists")

    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id):
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    delete_old_icon_if_exists(db_category.icon)

    db.delete(db_category)
    db.commit()
    return None