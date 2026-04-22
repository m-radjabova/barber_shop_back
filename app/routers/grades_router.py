from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_teacher_or_admin
from app.models.user import User
from app.schemas.grades import GradeBulkUpsert, GradeCreate, GradeResponse, GradeUpdate
from app.services.grade_service import GradeService

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.get("/", response_model=list[GradeResponse])
def list_grades(
    lesson_id: str | None = Query(default=None),
    student_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return GradeService(db).list_grades(current_user, lesson_id, student_id)


@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
def give_grade(payload: GradeCreate, db: Session = Depends(get_db), current_user: User = Depends(require_teacher_or_admin)):
    return GradeService(db).give_grade(payload, current_user)


@router.post("/save-many", response_model=list[GradeResponse], status_code=status.HTTP_201_CREATED)
def bulk_upsert_grades(
    payload: GradeBulkUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    return GradeService(db).bulk_upsert_grades(payload.records, current_user)


@router.patch("/{grade_id}", response_model=GradeResponse)
def update_grade(
    grade_id: str,
    payload: GradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher_or_admin),
):
    return GradeService(db).update_grade(grade_id, payload, current_user)
