from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.todo import TodoOut
from app.services import todo_service

router = APIRouter(
    prefix="/todos",
    tags=["Todos"]
)

@router.get("/", response_model=list[TodoOut])
def list_todos(db: Session = Depends(get_db)):
    return todo_service.get_todos(db)