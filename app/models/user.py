import uuid
from datetime import datetime, time

from sqlalchemy import BigInteger, Boolean, DateTime, Float, String, Time, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import UserRole, sql_enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(sql_enum(UserRole, "user_role"), nullable=False, default=UserRole.USER)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1200), nullable=True)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    work_start_time: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    work_end_time: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    services: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB, nullable=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True, index=True)
    telegram_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    telegram_marketing_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    telegram_link_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    telegram_link_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    telegram_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def has_role(self, role: UserRole) -> bool:
        return self.role == role

    def has_any_role(self, *roles: UserRole) -> bool:
        return self.role in roles

    @property
    def telegram_connected(self) -> bool:
        return bool(self.telegram_chat_id)

    @property
    def average_rating(self) -> float:
        return float(getattr(self, "_average_rating", 0.0) or 0.0)

    @property
    def reviews_count(self) -> int:
        return int(getattr(self, "_reviews_count", 0) or 0)

    @property
    def completed_bookings_count(self) -> int:
        return int(getattr(self, "_completed_bookings_count", 0) or 0)

    @property
    def price_from(self) -> int | None:
        value = getattr(self, "_price_from", None)
        return int(value) if value is not None else None
