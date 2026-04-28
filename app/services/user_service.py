from __future__ import annotations

import uuid
from pathlib import Path
from uuid import UUID

import requests
from fastapi import UploadFile, status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import BarberCreate, BarberUpdate, ChangePasswordSchema, UserUpdate
from app.services.base import BaseService, ServiceError


class UserService(BaseService):
    def get_user_by_id(self, user_id: str) -> User:
        try:
            user_uuid = UUID(str(user_id))
        except ValueError as exc:
            raise self.bad_request("Foydalanuvchi id noto'g'ri") from exc

        user = self.db.get(User, user_uuid)
        if not user:
            raise self.not_found("Foydalanuvchi")
        return user

    def get_barber_by_id(self, barber_id: str) -> User:
        barber = self.get_user_by_id(barber_id)
        if barber.role != UserRole.BARBER:
            raise self.bad_request("Bu foydalanuvchi barber emas")
        return barber

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.strip().lower())
        return self.db.execute(statement).scalar_one_or_none()

    def create_barber(self, payload: BarberCreate) -> User:
        return self._create_user(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=UserRole.BARBER,
        )

    def create_admin(self, full_name: str, email: str, password: str) -> User:
        return self._create_user(full_name=full_name, email=email, password=password, role=UserRole.ADMIN)

    def list_barbers(self) -> list[User]:
        statement = select(User).where(User.role == UserRole.BARBER).order_by(User.created_at.desc())
        return list(self.db.execute(statement).scalars().all())

    def update_current_user(self, current_user: User, payload: UserUpdate) -> User:
        data = payload.model_dump(exclude_unset=True)
        if "email" in data:
            data["email"] = data["email"].strip().lower()
            self._ensure_email_available(data["email"], exclude_user_id=current_user.id)
        if "specialty" in data:
            data["specialty"] = self._normalize_specialty(data["specialty"])

        for field, value in data.items():
            setattr(current_user, field, value)

        self.db.add(current_user)
        self.commit()
        return self.refresh(current_user)

    def update_barber(self, barber_id: str, payload: BarberUpdate) -> User:
        barber = self.get_barber_by_id(barber_id)

        data = payload.model_dump(exclude_unset=True)
        if "email" in data:
            data["email"] = data["email"].strip().lower()
            self._ensure_email_available(data["email"], exclude_user_id=barber.id)
        if "specialty" in data:
            data["specialty"] = self._normalize_specialty(data["specialty"])
        if "password" in data:
            data["password_hash"] = hash_password(data.pop("password"))

        for field, value in data.items():
            setattr(barber, field, value)

        self.db.add(barber)
        self.commit()
        return self.refresh(barber)

    def change_my_password(self, current_user: User, payload: ChangePasswordSchema) -> User:
        if not verify_password(payload.current_password, current_user.password_hash):
            raise self.bad_request("Joriy parol noto'g'ri")

        current_user.password_hash = hash_password(payload.new_password)
        current_user.refresh_token_hash = None
        self.db.add(current_user)
        self.commit()
        return self.refresh(current_user)

    def update_avatar(self, user: User, image: UploadFile) -> User:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise ServiceError(status.HTTP_400_BAD_REQUEST, "Faqat rasm yuklash mumkin")

        file_extension = self._resolve_extension(image.filename or "", image.content_type)
        filename = f"{uuid.uuid4().hex}.{file_extension}"
        image.file.seek(0)
        file_bytes = image.file.read()

        uploaded_url = self._upload_to_imagekit(filename, file_bytes)
        user.avatar = uploaded_url
        self.db.add(user)
        self.commit()
        return self.refresh(user)

    def delete_avatar(self, user: User) -> User:
        user.avatar = None
        self.db.add(user)
        self.commit()
        return self.refresh(user)

    def _create_user(self, full_name: str, email: str, password: str, role: UserRole) -> User:
        normalized_email = email.strip().lower()
        self._ensure_email_available(normalized_email)

        user = User(
            full_name=full_name.strip(),
            email=normalized_email,
            password_hash=hash_password(password),
            role=role,
        )
        self.db.add(user)
        self.commit()
        return self.refresh(user)

    def _ensure_email_available(self, email: str, exclude_user_id=None) -> None:
        existing_user = self.get_by_email(email)
        if existing_user and existing_user.id != exclude_user_id:
            raise self.bad_request("Bu email allaqachon mavjud")

    @staticmethod
    def _normalize_specialty(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _resolve_extension(filename: str, content_type: str) -> str:
        extension = Path(filename).suffix.lower().lstrip(".")
        if extension in {"jpg", "jpeg", "png", "webp"}:
            return "jpg" if extension == "jpeg" else extension

        content_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }
        return content_map.get(content_type, "jpg")

    @staticmethod
    def _upload_to_imagekit(filename: str, file_bytes: bytes) -> str:
        if not settings.IMAGEKIT_PRIVATE_KEY or not settings.IMAGEKIT_URL_ENDPOINT:
            raise ServiceError(status.HTTP_500_INTERNAL_SERVER_ERROR, "ImageKit sozlanmagan")

        response = requests.post(
            "https://upload.imagekit.io/api/v1/files/upload",
            auth=(settings.IMAGEKIT_PRIVATE_KEY, ""),
            files={"file": (filename, file_bytes)},
            data={
                "fileName": filename,
                "folder": "/barber-shop/avatars",
                "useUniqueFileName": "true",
            },
            timeout=30,
        )

        if response.status_code >= 400:
            raise ServiceError(status.HTTP_400_BAD_REQUEST, "Rasmni ImageKit'ga yuklab bo'lmadi")

        payload = response.json()
        url = payload.get("url")
        if not url:
            raise ServiceError(status.HTTP_400_BAD_REQUEST, "ImageKit URL qaytarmadi")
        return url
