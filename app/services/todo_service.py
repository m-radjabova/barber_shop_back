
from sqlalchemy.orm import Session
from app.models.todo import Todo

def get_todos(db: Session):
    return db.query(Todo).all()