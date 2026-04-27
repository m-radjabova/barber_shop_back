from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.user import BarberCreate, BarberUpdate, UserOut
from app.services.user_service import UserService

router = APIRouter(prefix="/barbers", tags=["Barbers"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_barber(
    payload: BarberCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return UserService(db).create_barber(payload)


@router.get("/", response_model=list[UserOut])
def list_barbers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return UserService(db).list_barbers()


@router.patch("/{barber_id}", response_model=UserOut)
def update_barber(
    barber_id: str,
    payload: BarberUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return UserService(db).update_barber(barber_id, payload)


@router.post("/{barber_id}/avatar", response_model=UserOut)
def upload_barber_avatar(
    barber_id: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    barber = UserService(db).get_barber_by_id(barber_id)
    return UserService(db).update_avatar(barber, image)
