from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_admin, require_user
from app.models.enums import BarberApplicationStatus
from app.models.user import User
from app.schemas.barber_application import (
    BarberApplicationApprove,
    BarberApplicationConfigOut,
    BarberApplicationCreate,
    BarberApplicationOut,
    BarberApplicationReject,
)
from app.services.barber_application_service import BarberApplicationService

router = APIRouter(prefix="/barber-applications", tags=["Barber Applications"])


@router.get("/config", response_model=BarberApplicationConfigOut)
def get_barber_application_config(db: Session = Depends(get_db)):
    return BarberApplicationService(db).get_public_config()


@router.get("/me", response_model=BarberApplicationOut | None)
def get_my_barber_application(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BarberApplicationService(db)
    application = service.get_my_application(current_user)
    return service.serialize_application(application) if application else None


@router.post("/me", response_model=BarberApplicationOut, status_code=status.HTTP_201_CREATED)
def create_my_barber_application(
    full_name: str = Form(...),
    phone_number: str = Form(...),
    location_text: str = Form(...),
    location_lat: float | None = Form(default=None),
    location_lng: float | None = Form(default=None),
    passport_series: str = Form(...),
    comment: str = Form(...),
    payment_note: str = Form(...),
    receipt: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    service = BarberApplicationService(db)
    application = service.create_or_update_application(
        current_user,
        BarberApplicationCreate(
            full_name=full_name,
            phone_number=phone_number,
            location_text=location_text,
            location_lat=location_lat,
            location_lng=location_lng,
            passport_series=passport_series,
            comment=comment,
            payment_note=payment_note,
        ),
        receipt,
    )
    return service.serialize_application(application)


@router.get("/", response_model=list[BarberApplicationOut])
def list_barber_applications(
    status_value: BarberApplicationStatus | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = BarberApplicationService(db)
    return [service.serialize_application(item) for item in service.list_applications(status_value)]


@router.post("/{application_id}/approve", response_model=BarberApplicationOut)
def approve_barber_application(
    application_id: str,
    payload: BarberApplicationApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = BarberApplicationService(db)
    application = service.approve_application(application_id, current_user, payload)
    return service.serialize_application(application)


@router.post("/{application_id}/reject", response_model=BarberApplicationOut)
def reject_barber_application(
    application_id: str,
    payload: BarberApplicationReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = BarberApplicationService(db)
    application = service.reject_application(application_id, current_user, payload)
    return service.serialize_application(application)
