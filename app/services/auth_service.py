import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import create_token, decode_token
from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import CustomerLoginSchema, CustomerRegisterSchema, LoginSchema
from app.services.base import BaseService, ServiceError


class AuthService(BaseService):
    def login(self, payload: LoginSchema) -> dict:
        normalized_email = payload.email.strip().lower()
        statement = select(User).where(func.lower(User.email) == normalized_email)
        user = self.db.execute(statement).scalar_one_or_none()
        if not user or not verify_password(payload.password, user.password_hash):
            raise ServiceError(401, "Invalid credentials")
        if not user.is_active:
            raise ServiceError(403, "User is inactive")

        tokens = self._build_tokens(user)
        user.refresh_token_hash = hash_password(tokens["refresh_token"])
        self.db.add(user)
        self.commit()
        return tokens

    def login_customer(self, payload: CustomerLoginSchema) -> dict:
        normalized_phone = self._normalize_phone_number(payload.phone_number)
        statement = select(User).where(
            User.phone_number == normalized_phone,
            User.role == UserRole.USER,
        )
        user = self.db.execute(statement).scalar_one_or_none()
        if user is None:
            raise ServiceError(404, "Bu telefon raqami ro'yxatdan o'tmagan")
        if not user.is_active:
            raise ServiceError(403, "User is inactive")

        user.location_text = self._normalize_short_text(payload.location_text)
        user.location_lat, user.location_lng = self._normalize_location(payload.location_lat, payload.location_lng)

        return self._issue_customer_tokens(user)

    def register_customer(self, payload: CustomerRegisterSchema) -> dict:
        normalized_phone = self._normalize_phone_number(payload.phone_number)
        statement = select(User).where(User.phone_number == normalized_phone)
        user = self.db.execute(statement).scalar_one_or_none()
        if user is not None:
            raise ServiceError(409, "Bu telefon raqami allaqachon ro'yxatdan o'tgan")

        user = User(
            full_name=payload.full_name.strip(),
            email=self._build_customer_email(normalized_phone),
            phone_number=normalized_phone,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role=UserRole.USER,
            is_active=True,
            location_text=self._normalize_short_text(payload.location_text),
        )
        user.location_lat, user.location_lng = self._normalize_location(payload.location_lat, payload.location_lng)

        return self._issue_customer_tokens(user)

    def login_or_register_customer(self, payload: CustomerRegisterSchema) -> dict:
        return self.register_customer(payload)

    def _issue_customer_tokens(self, user: User) -> dict:
        if not user.is_active:
            raise ServiceError(403, "User is inactive")

        tokens = self._build_tokens(user)
        user.refresh_token_hash = hash_password(tokens["refresh_token"])
        self.db.add(user)
        self.commit()
        return tokens

    def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ServiceError(401, "Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise ServiceError(401, "Invalid refresh token payload")

        try:
            user_uuid = UUID(str(user_id))
        except (TypeError, ValueError) as exc:
            raise ServiceError(401, "Invalid refresh token payload") from exc

        user = self.db.get(User, user_uuid)
        if not user or not user.refresh_token_hash:
            raise ServiceError(401, "Refresh token expired")
        if not verify_password(refresh_token, user.refresh_token_hash):
            raise ServiceError(401, "Refresh token mismatch")
        if not user.is_active:
            raise ServiceError(403, "User is inactive")

        return {
            "access_token": create_token(
                payload={
                    "sub": str(user.id),
                    "type": "access",
                    "role": user.role.value,
                },
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            ),
            "token_type": "bearer",
        }

    def logout(self, user: User) -> None:
        user.refresh_token_hash = None
        self.db.add(user)
        self.commit()

    def _build_tokens(self, user: User) -> dict:
        access_token = create_token(
            payload={
                "sub": str(user.id),
                "type": "access",
                "role": user.role.value,
            },
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_token(
            payload={"sub": str(user.id), "type": "refresh"},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    @staticmethod
    def _normalize_phone_number(phone_number: str) -> str:
        digits = "".join(char for char in phone_number if char.isdigit())
        if digits.startswith("998"):
            digits = digits[3:]
        if len(digits) != 9:
            raise ServiceError(400, "Telefon raqamini +998 XX XXX XX XX formatida kiriting")
        return f"+998{digits}"

    @staticmethod
    def _build_customer_email(phone_number: str) -> str:
        digits = "".join(char for char in phone_number if char.isdigit())
        return f"user-{digits}@customer.local"

    @staticmethod
    def _normalize_short_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    @staticmethod
    def _normalize_location(lat: float | None, lng: float | None) -> tuple[float | None, float | None]:
        if lat is None and lng is None:
            return None, None
        if lat is None or lng is None:
            raise ServiceError(400, "Lokatsiya to'liq yuborilishi kerak")
        return float(lat), float(lng)


def get_auth_service(db: Session) -> AuthService:
    return AuthService(db)
