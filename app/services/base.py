from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class ServiceError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class BaseService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def not_found(entity: str) -> ServiceError:
        return ServiceError(status.HTTP_404_NOT_FOUND, f"{entity} topilmadi")

    @staticmethod
    def bad_request(message: str) -> ServiceError:
        return ServiceError(status.HTTP_400_BAD_REQUEST, message)

    @staticmethod
    def forbidden(message: str) -> ServiceError:
        return ServiceError(status.HTTP_403_FORBIDDEN, message)

    def commit(self):
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise self.bad_request(self._get_constraint_message(exc)) from exc

    def refresh(self, instance):
        self.db.refresh(instance)
        return instance

    @staticmethod
    def _get_constraint_message(exc: IntegrityError) -> str:
        diag = getattr(getattr(exc, "orig", None), "diag", None)
        constraint_name = getattr(diag, "constraint_name", None)
        raw_message = str(getattr(exc, "orig", exc)).lower()

        if constraint_name == "uq_groups_course_name" or "uq_groups_course_name" in raw_message:
            return "Bu kurs ichida shu nomdagi guruh allaqachon mavjud"

        if constraint_name == "rooms_name_key" or "rooms_name_key" in raw_message:
            return "Bu nomdagi xona allaqachon mavjud"

        if "groups_course_id_fkey" in raw_message:
            return "Tanlangan kurs topilmadi"

        if "groups_teacher_id_fkey" in raw_message:
            return "Tanlangan teacher topilmadi"

        if "groups_room_id_fkey" in raw_message:
            return "Tanlangan xona topilmadi"

        return "Ma'lumotlar cheklovi buzildi"


def parse_uuid(value: str | UUID, field_name: str = "id") -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ServiceError(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{field_name} noto'g'ri") from exc
