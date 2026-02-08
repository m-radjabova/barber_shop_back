from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.category import CategoryOut, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    name: str = Form(...),
    description: str | None = Form(None),
    icon: UploadFile | None = File(None), 
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return category_service.create_category(
        db,
        name=name,
        description=description,
        icon_file=icon,
    )


@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return category_service.get_categories(db)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category_by_id(category_id: UUID, db: Session = Depends(get_db)):
    category = category_service.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return category_service.update_category(db, category_id, category_data)


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    category_service.delete_category(db, category_id)
    return