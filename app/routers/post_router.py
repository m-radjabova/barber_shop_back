from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.post import PostCreate, PostOut
from app.services import post_service


router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

@router.post("/", response_model=PostOut)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return post_service.create_post(db, post, current_user.id)

@router.get("/", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    return post_service.get_posts(db)

@router.put("/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_post = post_service.update_post(db, post_id, post_data)
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post_service.delete_post(db, post_id)

@router.get("/user/{user_id}", response_model=list[PostOut])
def get_posts_by_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    return post_service.get_posts_by_user(db, user_id)