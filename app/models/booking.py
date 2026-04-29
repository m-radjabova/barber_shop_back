import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BookingStatus, sql_enum


class Booking(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    booking_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    barber_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    client_name: Mapped[str] = mapped_column(String(120), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[time] = mapped_column(Time, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[BookingStatus] = mapped_column(
        sql_enum(BookingStatus, "booking_status"),
        nullable=False,
        default=BookingStatus.CONFIRMED,
    )

    barber = relationship("User", foreign_keys=[barber_id], lazy="joined")
    customer = relationship("User", foreign_keys=[customer_id], lazy="joined")

    @property
    def barber_name(self) -> str:
        return self.barber.full_name

    @property
    def barber_avatar(self) -> str | None:
        return self.barber.avatar

    @property
    def barber_specialty(self) -> str | None:
        return self.barber.specialty

    @property
    def barber_rating(self) -> float:
        return self.barber.average_rating

    @property
    def barber_reviews_count(self) -> int:
        return self.barber.reviews_count
