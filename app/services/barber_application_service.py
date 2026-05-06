from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile, status
from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.models.barber_application import BarberApplication
from app.models.enums import BarberApplicationStatus, UserRole
from app.models.user import User
from app.schemas.barber_application import (
    BarberApplicationApprove,
    BarberApplicationCreate,
    BarberApplicationReject,
)
from app.services.base import BaseService, ServiceError
from app.services.telegram_service import TelegramService
from app.services.user_service import UserService


class BarberApplicationService(BaseService):
    def get_public_config(self) -> dict[str, object]:
        return {
            "payment_card_number": settings.BARBER_APPLICATION_CARD_NUMBER,
            "payment_amount": settings.BARBER_APPLICATION_PAYMENT_AMOUNT,
            "telegram_required": True,
        }

    def get_my_application(self, current_user: User) -> BarberApplication | None:
        statement = select(BarberApplication).where(BarberApplication.user_id == current_user.id)
        return self.db.execute(statement).scalar_one_or_none()

    def create_or_update_application(
        self,
        current_user: User,
        payload: BarberApplicationCreate,
        receipt: UploadFile,
    ) -> BarberApplication:
        if current_user.role != UserRole.USER:
            raise self.bad_request("Faqat oddiy foydalanuvchi barber ariza topshira oladi")
        if not current_user.telegram_connected:
            raise self.forbidden("Ariza topshirishdan oldin Telegram botga ulanishingiz kerak")

        existing = self.get_my_application(current_user)
        if existing and existing.status == BarberApplicationStatus.APPROVED:
            raise self.bad_request("Sizning barber arizangiz allaqachon tasdiqlangan")

        normalized_phone = UserService._normalize_phone_number(payload.phone_number)
        receipt_url = self._upload_receipt(receipt)

        if existing is None:
            application = BarberApplication(
                user_id=current_user.id,
                payment_card_number=settings.BARBER_APPLICATION_CARD_NUMBER,
                payment_amount=settings.BARBER_APPLICATION_PAYMENT_AMOUNT,
            )
        else:
            application = existing

        application.full_name = payload.full_name
        application.phone_number = normalized_phone
        application.location_text = payload.location_text
        application.location_lat = payload.location_lat
        application.location_lng = payload.location_lng
        application.passport_series = payload.passport_series
        application.comment = payload.comment
        application.payment_card_number = settings.BARBER_APPLICATION_CARD_NUMBER
        application.payment_amount = settings.BARBER_APPLICATION_PAYMENT_AMOUNT
        application.payment_note = payload.payment_note
        application.receipt_file_url = receipt_url
        application.status = BarberApplicationStatus.PENDING
        application.admin_note = None
        application.reviewed_by_user_id = None
        application.reviewed_at = None

        self.db.add(application)
        self.commit()
        return self.refresh(application)

    def list_applications(
        self,
        status_value: BarberApplicationStatus | None = None,
    ) -> list[BarberApplication]:
        statement = select(BarberApplication).order_by(BarberApplication.created_at.desc())
        if status_value is not None:
            statement = statement.where(BarberApplication.status == status_value)
        return list(self.db.execute(statement).scalars().all())

    def approve_application(
        self,
        application_id: str,
        admin_user: User,
        payload: BarberApplicationApprove,
    ) -> BarberApplication:
        application = self._get_application_by_id(application_id)
        applicant = self._get_user(application.user_id)

        if application.status == BarberApplicationStatus.APPROVED:
            raise self.bad_request("Bu ariza allaqachon tasdiqlangan")

        applicant.role = UserRole.BARBER
        applicant.full_name = application.full_name
        applicant.phone_number = application.phone_number
        applicant.location_text = application.location_text
        applicant.location_lat = application.location_lat
        applicant.location_lng = application.location_lng
        applicant.email = self._resolve_barber_login_email(applicant, preferred_email=payload.email)
        applicant.password_hash = hash_password(payload.password)
        applicant.refresh_token_hash = None

        application.status = BarberApplicationStatus.APPROVED
        application.admin_note = payload.admin_note
        application.reviewed_by_user_id = admin_user.id
        application.reviewed_at = datetime.now(settings.app_timezone)

        self.db.add(applicant)
        self.db.add(application)
        self.commit()
        updated_application = self.refresh(application)
        self.refresh(applicant)

        TelegramService(self.db).send_barber_application_approved(
            applicant,
            login_email=applicant.email,
            password=payload.password,
        )

        return updated_application

    def reject_application(
        self,
        application_id: str,
        admin_user: User,
        payload: BarberApplicationReject,
    ) -> BarberApplication:
        application = self._get_application_by_id(application_id)
        if application.status == BarberApplicationStatus.APPROVED:
            raise self.bad_request("Tasdiqlangan arizani rad etib bo'lmaydi")

        application.status = BarberApplicationStatus.REJECTED
        application.admin_note = payload.admin_note
        application.reviewed_by_user_id = admin_user.id
        application.reviewed_at = datetime.now(settings.app_timezone)

        self.db.add(application)
        self.commit()
        updated_application = self.refresh(application)

        applicant = self._get_user(application.user_id)
        TelegramService(self.db).send_barber_application_rejected(
            applicant,
            admin_note=payload.admin_note,
        )

        return updated_application

    def serialize_application(self, application: BarberApplication) -> dict[str, object]:
        applicant = self._get_user(application.user_id)
        return {
            "id": str(application.id),
            "user_id": str(application.user_id),
            "user_email": applicant.email,
            "user_role": applicant.role.value,
            "telegram_connected": applicant.telegram_connected,
            "full_name": application.full_name,
            "phone_number": application.phone_number,
            "location_text": application.location_text,
            "location_lat": application.location_lat,
            "location_lng": application.location_lng,
            "passport_series": application.passport_series,
            "comment": application.comment,
            "payment_card_number": application.payment_card_number,
            "payment_amount": application.payment_amount,
            "payment_note": application.payment_note,
            "receipt_file_url": application.receipt_file_url,
            "status": application.status,
            "admin_note": application.admin_note,
            "reviewed_by_user_id": str(application.reviewed_by_user_id) if application.reviewed_by_user_id else None,
            "reviewed_at": application.reviewed_at,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
        }

    def _get_application_by_id(self, application_id: str) -> BarberApplication:
        try:
            application_uuid = uuid.UUID(str(application_id))
        except ValueError as exc:
            raise self.bad_request("Ariza ID noto'g'ri") from exc

        application = self.db.get(BarberApplication, application_uuid)
        if not application:
            raise self.not_found("Ariza")
        return application

    def _get_user(self, user_id) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise self.not_found("Foydalanuvchi")
        return user

    @staticmethod
    def _resolve_receipt_extension(filename: str, content_type: str) -> str:
        extension = Path(filename).suffix.lower().lstrip(".")
        if extension in {"jpg", "jpeg", "png", "webp", "pdf"}:
            return "jpg" if extension == "jpeg" else extension

        content_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "application/pdf": "pdf",
        }
        return content_map.get(content_type, "jpg")

    def _upload_receipt(self, receipt: UploadFile) -> str:
        allowed_types = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
        if not receipt.content_type or receipt.content_type not in allowed_types:
            raise ServiceError(
                status.HTTP_400_BAD_REQUEST,
                "Chek uchun JPG, PNG, WEBP yoki PDF fayl yuklang",
            )

        file_extension = self._resolve_receipt_extension(receipt.filename or "", receipt.content_type)
        filename = f"{uuid.uuid4().hex}.{file_extension}"
        receipt.file.seek(0)
        file_bytes = receipt.file.read()

        return UserService._upload_to_imagekit(
            filename,
            file_bytes,
            folder="/barber-shop/barber-applications",
        )

    def _resolve_barber_login_email(self, applicant: User, preferred_email: str | None = None) -> str:
        if preferred_email:
            normalized_email = preferred_email.strip().lower()
            existing_user = UserService(self.db).get_by_email(normalized_email)
            if existing_user and existing_user.id != applicant.id:
                raise self.bad_request("Ushbu email allaqachon mavjud")
            return normalized_email

        current_email = (applicant.email or "").strip().lower()
        if current_email and not current_email.endswith("@customer.local"):
            return current_email

        digits = "".join(char for char in (applicant.phone_number or "") if char.isdigit())
        if not digits:
            raise self.bad_request("Foydalanuvchi telefon raqami topilmadi")

        generated_email = f"barber-{digits}@staff.local"
        existing_user = UserService(self.db).get_by_email(generated_email)
        if existing_user and existing_user.id != applicant.id:
            raise self.bad_request("Ushbu barber login allaqachon mavjud")
        return generated_email
