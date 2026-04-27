from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.roles import require_admin, require_admin_or_barber, require_barber
from app.models.enums import BookingStatus
from app.models.user import User
from app.schemas.booking import BarberDashboardOut, BookingOut, BookingStatusUpdate
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/", response_model=list[BookingOut])
def list_bookings(
    date_value: date | None = Query(default=None, alias="date"),
    barber_id: str | None = None,
    status: BookingStatus | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return BookingService(db).list_bookings(
        appointment_date=date_value,
        barber_id=barber_id,
        status=status,
        search=search,
    )


@router.get("/me", response_model=list[BookingOut])
def list_my_bookings(
    date_value: date | None = Query(default=None, alias="date"),
    status: BookingStatus | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_barber),
):
    return BookingService(db).list_barber_bookings(
        current_user,
        appointment_date=date_value,
        status=status,
    )


@router.get("/dashboard", response_model=BarberDashboardOut)
def get_my_dashboard(
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_barber),
):
    return BookingService(db).get_barber_dashboard(current_user, date_value)


@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(
    booking_id: str,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_barber),
):
    return BookingService(db).update_booking_status(booking_id, current_user, payload.status)
