from datetime import date, time
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import BookingStatus
from app.schemas.common import ORMModel, TimestampedSchema


class PublicBarberOut(ORMModel):
    id: UUID
    full_name: str
    avatar: str | None = None
    specialty: str | None = None
    average_rating: float = 0.0
    reviews_count: int = 0
    completed_bookings_count: int = 0
    is_active: bool = True


class AvailabilitySlotOut(ORMModel):
    time: str
    label: str
    status: str


class BarberAvailabilityOut(ORMModel):
    barber: PublicBarberOut
    date: str
    display_date: str
    slots: list[AvailabilitySlotOut]


class BookingCreate(ORMModel):
    barber_id: str
    client_name: str = Field(min_length=3, max_length=120)
    client_phone: str = Field(min_length=7, max_length=32)
    appointment_date: date
    appointment_time: str

    @field_validator("client_name")
    @classmethod
    def validate_client_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("client_phone")
    @classmethod
    def validate_client_phone(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Telefon raqami kiritilishi shart")
        return normalized


class BookingOut(TimestampedSchema):
    booking_code: str
    barber_id: UUID
    barber_name: str
    barber_avatar: str | None = None
    barber_specialty: str | None = None
    barber_rating: float = 0.0
    barber_reviews_count: int = 0
    client_name: str
    client_phone: str
    appointment_date: date
    appointment_time: time
    rating: int | None = None
    status: BookingStatus


class BookingRatingCreate(ORMModel):
    rating: int = Field(ge=1, le=5)


class BookingStatusUpdate(ORMModel):
    status: BookingStatus


class BarberDashboardStatsOut(ORMModel):
    total: int
    completed: int
    pending: int
    completion_ratio: float


class BarberDashboardOut(ORMModel):
    barber: PublicBarberOut
    date: str
    display_date: str
    stats: BarberDashboardStatsOut
    next_booking: BookingOut | None = None
    appointments: list[BookingOut]
