from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.schemas.common import validate_app_email
from app.models.enums import BarberApplicationStatus
from app.schemas.common import ORMModel


class BarberApplicationBase(ORMModel):
    full_name: str = Field(min_length=3, max_length=120)
    phone_number: str = Field(min_length=7, max_length=32)
    location_text: str = Field(min_length=3, max_length=255)
    location_lat: float | None = Field(default=None, ge=-90, le=90)
    location_lng: float | None = Field(default=None, ge=-180, le=180)
    passport_series: str = Field(min_length=5, max_length=32)
    comment: str = Field(min_length=3, max_length=2000)
    payment_note: str = Field(min_length=3, max_length=2000)

    @field_validator("full_name", "location_text", "comment", "payment_note")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = " ".join(value.strip().split()) if value.strip() else ""
        if not normalized:
            raise ValueError("Maydon bo'sh bo'lishi mumkin emas")
        return normalized

    @field_validator("passport_series")
    @classmethod
    def normalize_passport_series(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "")
        if len(normalized) < 5:
            raise ValueError("Pasport seriyasi noto'g'ri")
        return normalized

    @field_validator("phone_number")
    @classmethod
    def normalize_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 7:
            raise ValueError("Telefon raqami noto'g'ri")
        return normalized

    @model_validator(mode="after")
    def validate_location(self) -> "BarberApplicationBase":
        has_lat = self.location_lat is not None
        has_lng = self.location_lng is not None
        if has_lat != has_lng:
            raise ValueError("Lokatsiya to'liq yuborilishi kerak")
        return self


class BarberApplicationCreate(BarberApplicationBase):
    pass


class BarberApplicationApprove(ORMModel):
    email: str | None = None
    password: str = Field(min_length=6, max_length=128)
    admin_note: str | None = Field(default=None, max_length=2000)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_app_email(value)

    @field_validator("admin_note")
    @classmethod
    def normalize_admin_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class BarberApplicationReject(ORMModel):
    admin_note: str = Field(min_length=3, max_length=2000)

    @field_validator("admin_note")
    @classmethod
    def normalize_admin_note(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Izoh bo'sh bo'lishi mumkin emas")
        return normalized


class BarberApplicationOut(ORMModel):
    id: str
    user_id: str
    user_email: str | None = None
    user_role: str | None = None
    telegram_connected: bool = False
    full_name: str
    phone_number: str
    location_text: str
    location_lat: float | None = None
    location_lng: float | None = None
    passport_series: str
    comment: str
    payment_card_number: str
    payment_amount: int
    payment_note: str
    receipt_file_url: str
    status: BarberApplicationStatus
    admin_note: str | None = None
    reviewed_by_user_id: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BarberApplicationConfigOut(ORMModel):
    payment_card_number: str
    payment_amount: int
    telegram_required: bool = True
