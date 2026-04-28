from __future__ import annotations

import random
import string
from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.enums import BookingStatus, UserRole
from app.models.user import User
from app.core.config import settings
from app.schemas.booking import BookingCreate, BookingRatingCreate
from app.services.base import BaseService

BOOKING_OPEN_HOUR = 9
BOOKING_CLOSE_HOUR = 17
BOOKING_LAST_SLOT_MINUTE = 30
BOOKING_SLOT_MINUTES = 30


class BookingService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)

    def list_public_barbers(self) -> list[User]:
        statement = (
            select(User)
            .where(User.role == UserRole.BARBER, User.is_active.is_(True))
            .order_by(User.created_at.asc())
        )
        barbers = list(self.db.execute(statement).scalars().all())
        self._attach_barber_metrics(barbers)
        return barbers

    def get_public_barber(self, barber_id: str) -> User:
        barber = self._get_barber(barber_id)
        if not barber.is_active:
            raise self.bad_request("Bu barber hozir faol emas")
        self._attach_barber_metrics([barber])
        return barber

    def get_availability(self, barber_id: str, appointment_date: date) -> dict:
        barber = self.get_public_barber(barber_id)
        booked_times = {
            booking.appointment_time.strftime("%H:%M")
            for booking in self._get_bookings_for_day(barber.id, appointment_date)
            if booking.status != BookingStatus.CANCELLED
        }

        slots = []
        for slot_time in self._generate_slot_times():
            key = slot_time.strftime("%H:%M")
            is_past_slot = self._is_past_slot(appointment_date, slot_time)
            slots.append(
                {
                    "time": key,
                    "label": self._format_time_label(slot_time),
                    "status": "booked" if key in booked_times else "past" if is_past_slot else "available",
                }
            )

        return {
            "barber": barber,
            "date": appointment_date.isoformat(),
            "display_date": self._format_display_date(appointment_date),
            "slots": slots,
        }

    def create_booking(self, payload: BookingCreate) -> Booking:
        barber = self.get_public_barber(payload.barber_id)
        appointment_time = self._parse_time(payload.appointment_time)
        self._validate_booking_datetime(payload.appointment_date, appointment_time)
        self._ensure_slot_available(barber.id, payload.appointment_date, appointment_time)

        booking = Booking(
            booking_code=self._generate_booking_code(),
            barber_id=barber.id,
            client_name=payload.client_name.strip(),
            client_phone=payload.client_phone.strip(),
            appointment_date=payload.appointment_date,
            appointment_time=appointment_time,
            status=BookingStatus.CONFIRMED,
        )
        self.db.add(booking)
        self.commit()
        return self.refresh(booking)

    def get_booking_by_code(self, booking_code: str) -> Booking:
        statement = select(Booking).where(Booking.booking_code == booking_code.upper())
        booking = self.db.execute(statement).scalar_one_or_none()
        if not booking:
            raise self.not_found("Booking")
        self._attach_barber_metrics([booking.barber])
        return booking

    def rate_booking_by_code(self, booking_code: str, payload: BookingRatingCreate) -> Booking:
        booking = self.get_booking_by_code(booking_code)

        if booking.status != BookingStatus.COMPLETED:
            raise self.bad_request("Rating faqat bajarilgan booking uchun qoldiriladi")

        booking.rating = payload.rating
        self.db.add(booking)
        self.commit()
        refreshed = self.refresh(booking)
        self._attach_barber_metrics([refreshed.barber])
        return refreshed

    def list_bookings(
        self,
        *,
        appointment_date: date | None = None,
        barber_id: str | None = None,
        status: BookingStatus | None = None,
        search: str | None = None,
    ) -> list[Booking]:
        statement: Select[tuple[Booking]] = select(Booking).join(Booking.barber)

        if appointment_date:
            statement = statement.where(Booking.appointment_date == appointment_date)
        if barber_id:
            statement = statement.where(Booking.barber_id == self._parse_uuid(barber_id))
        if status:
            statement = statement.where(Booking.status == status)
        if search:
            search_value = f"%{search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Booking.client_name).like(search_value),
                    func.lower(Booking.client_phone).like(search_value),
                    func.lower(Booking.booking_code).like(search_value),
                    func.lower(User.full_name).like(search_value),
                )
            )

        statement = statement.order_by(Booking.appointment_date.desc(), Booking.appointment_time.asc())
        return list(self.db.execute(statement).scalars().all())

    def list_barber_bookings(
        self,
        barber: User,
        *,
        appointment_date: date | None = None,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        statement: Select[tuple[Booking]] = select(Booking).where(Booking.barber_id == barber.id)

        if appointment_date:
            statement = statement.where(Booking.appointment_date == appointment_date)
        if status:
            statement = statement.where(Booking.status == status)

        statement = statement.order_by(Booking.appointment_date.asc(), Booking.appointment_time.asc())
        return list(self.db.execute(statement).scalars().all())

    def get_barber_dashboard(self, barber: User, appointment_date: date) -> dict:
        self._attach_barber_metrics([barber])
        bookings = self.list_barber_bookings(barber, appointment_date=appointment_date)
        completed = sum(1 for booking in bookings if booking.status == BookingStatus.COMPLETED)
        pending = sum(1 for booking in bookings if booking.status == BookingStatus.CONFIRMED)
        total = len(bookings)
        next_booking = next((booking for booking in bookings if booking.status == BookingStatus.CONFIRMED), None)

        completion_ratio = round((completed / total), 4) if total else 0.0

        return {
            "barber": barber,
            "date": appointment_date.isoformat(),
            "display_date": self._format_display_date(appointment_date),
            "stats": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "completion_ratio": completion_ratio,
            },
            "next_booking": next_booking,
            "appointments": bookings,
        }

    def update_booking_status(self, booking_id: str, current_user: User, status: BookingStatus) -> Booking:
        booking = self.get_booking_by_id(booking_id)

        if current_user.role == UserRole.BARBER and booking.barber_id != current_user.id:
            raise self.forbidden("Bu booking sizga tegishli emas")

        if status == BookingStatus.COMPLETED and booking.status == BookingStatus.CANCELLED:
            raise self.bad_request("Cancelled booking'ni completed qilib bo'lmaydi")
        if status == BookingStatus.CANCELLED and booking.status == BookingStatus.COMPLETED:
            raise self.bad_request("Completed booking'ni cancelled qilib bo'lmaydi")

        booking.status = status
        self.db.add(booking)
        self.commit()
        return self.refresh(booking)

    def get_booking_by_id(self, booking_id: str) -> Booking:
        booking_uuid = self._parse_uuid(booking_id)
        booking = self.db.get(Booking, booking_uuid)
        if not booking:
            raise self.not_found("Booking")
        return booking

    def _get_barber(self, barber_id: str) -> User:
        barber_uuid = self._parse_uuid(barber_id)
        barber = self.db.get(User, barber_uuid)
        if not barber or barber.role != UserRole.BARBER:
            raise self.not_found("Barber")
        return barber

    def _attach_barber_metrics(self, barbers: list[User]) -> None:
        if not barbers:
            return

        barber_ids = [barber.id for barber in barbers]
        metrics_statement = (
            select(
                Booking.barber_id,
                func.coalesce(func.avg(Booking.rating), 0.0).label("average_rating"),
                func.count(Booking.rating).label("reviews_count"),
                func.coalesce(
                    func.sum(case((Booking.status == BookingStatus.COMPLETED, 1), else_=0)),
                    0,
                ).label("completed_bookings_count"),
            )
            .where(Booking.barber_id.in_(barber_ids))
            .group_by(Booking.barber_id)
        )
        rows = self.db.execute(metrics_statement).all()
        metrics_by_barber_id = {
            barber_id: {
                "average_rating": round(float(average_rating or 0.0), 1),
                "reviews_count": int(reviews_count or 0),
                "completed_bookings_count": int(completed_bookings_count or 0),
            }
            for barber_id, average_rating, reviews_count, completed_bookings_count in rows
        }

        for barber in barbers:
            metrics = metrics_by_barber_id.get(
                barber.id,
                {
                    "average_rating": 0.0,
                    "reviews_count": 0,
                    "completed_bookings_count": 0,
                },
            )
            barber._average_rating = metrics["average_rating"]
            barber._reviews_count = metrics["reviews_count"]
            barber._completed_bookings_count = metrics["completed_bookings_count"]

    def _get_bookings_for_day(self, barber_id: UUID, appointment_date: date) -> list[Booking]:
        statement = (
            select(Booking)
            .where(
                Booking.barber_id == barber_id,
                Booking.appointment_date == appointment_date,
            )
            .order_by(Booking.appointment_time.asc())
        )
        return list(self.db.execute(statement).scalars().all())

    def _ensure_slot_available(self, barber_id: UUID, appointment_date: date, appointment_time: time) -> None:
        if self._is_past_slot(appointment_date, appointment_time):
            raise self.bad_request("Bu vaqt o'tib ketgan")

        statement = select(Booking).where(
            Booking.barber_id == barber_id,
            Booking.appointment_date == appointment_date,
            Booking.appointment_time == appointment_time,
            Booking.status != BookingStatus.CANCELLED,
        )
        existing = self.db.execute(statement).scalar_one_or_none()
        if existing:
            raise self.bad_request("Bu vaqt band bo'lib qoldi")

    def _validate_booking_datetime(self, appointment_date: date, appointment_time: time) -> None:
        current_date = self._now().date()

        if appointment_date < current_date:
            raise self.bad_request("O'tgan sanaga booking qilib bo'lmaydi")

        if appointment_time not in self._generate_slot_times():
            raise self.bad_request("Vaqt noto'g'ri tanlangan")

        if self._is_past_slot(appointment_date, appointment_time):
            raise self.bad_request("O'tib ketgan vaqtga booking qilib bo'lmaydi")

    def _generate_booking_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        for _ in range(20):
            code = "".join(random.choices(alphabet, k=6))
            exists = self.db.execute(select(Booking.id).where(Booking.booking_code == code)).scalar_one_or_none()
            if not exists:
                return code
        raise self.bad_request("Booking code yaratib bo'lmadi")

    @staticmethod
    def _parse_time(value: str) -> time:
        try:
            parsed = datetime.strptime(value.strip(), "%H:%M")
        except ValueError as exc:
            raise BaseService.bad_request("Vaqt formati noto'g'ri") from exc
        return parsed.time()

    @staticmethod
    def _format_time_label(value: time) -> str:
        hour = value.hour % 12 or 12
        minute = str(value.minute).zfill(2)
        meridiem = "PM" if value.hour >= 12 else "AM"
        return f"{hour}:{minute} {meridiem}"

    @staticmethod
    def _format_display_date(value: date) -> str:
        return value.strftime("%A, %B") + f" {value.day}"

    @staticmethod
    def _generate_slot_times() -> list[time]:
        slots: list[time] = []
        cursor = datetime.combine(date.today(), time(hour=BOOKING_OPEN_HOUR, minute=0))
        final = datetime.combine(date.today(), time(hour=BOOKING_CLOSE_HOUR, minute=BOOKING_LAST_SLOT_MINUTE))
        while cursor <= final:
            slots.append(cursor.time())
            cursor += timedelta(minutes=BOOKING_SLOT_MINUTES)
        return slots

    @staticmethod
    def _now() -> datetime:
        return datetime.now(settings.app_timezone)

    def _is_past_slot(self, appointment_date: date, appointment_time: time) -> bool:
        now = self._now()
        if appointment_date != now.date():
            return False
        return appointment_time <= now.time().replace(second=0, microsecond=0)

    @staticmethod
    def _parse_uuid(value: str) -> UUID:
        try:
            return UUID(str(value))
        except ValueError as exc:
            raise BaseService.bad_request("Id noto'g'ri") from exc
