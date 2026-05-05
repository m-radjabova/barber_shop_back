from datetime import date

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.booking import (
    BarberAvailabilityOut,
    BookingCreate,
    BookingOut,
    BookingRatingCreate,
    PublicBarberOut,
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/public", tags=["Public Booking"])


@router.get("/barbers", response_model=list[PublicBarberOut])
def list_public_barbers(
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float | None = Query(default=None, gt=0, le=100),
    sort_by: Literal["distance", "price_asc", "price_desc"] | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return BookingService(db).list_public_barbers(
        latitude=lat,
        longitude=lng,
        radius_km=radius_km,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )


@router.get("/barbers/{barber_id}/availability", response_model=BarberAvailabilityOut)
def get_barber_availability(
    barber_id: str,
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
):
    return BookingService(db).get_availability(barber_id, date_value)


@router.post("/bookings", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_public_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    return BookingService(db).create_booking(payload)


@router.get("/bookings/{booking_code}", response_model=BookingOut)
def get_public_booking(booking_code: str, db: Session = Depends(get_db)):
    return BookingService(db).get_booking_by_code(booking_code)


@router.post("/bookings/{booking_code}/rating", response_model=BookingOut)
def rate_public_booking(
    booking_code: str,
    payload: BookingRatingCreate,
    db: Session = Depends(get_db),
):
    return BookingService(db).rate_booking_by_code(booking_code, payload)
