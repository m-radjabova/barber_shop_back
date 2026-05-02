from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.booking import Booking
from app.models.enums import BookingStatus, UserRole
from app.models.user import User
from app.schemas.user import TelegramPromotionCreate
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class TelegramService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.bot_username = settings.TELEGRAM_BOT_USERNAME
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ""

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.bot_username)

    def get_connection_info(self, user: User, *, refresh_token: bool = False) -> dict[str, object]:
        if self.is_configured() and (refresh_token or not user.telegram_connected):
            if refresh_token or not user.telegram_link_token or self._is_token_expired(user):
                self._issue_link_token(user)

        return {
            "connected": user.telegram_connected,
            "bot_username": self.bot_username or None,
            "bot_url": self._build_bot_url(),
            "deep_link_url": self._build_deep_link(user.telegram_link_token) if user.telegram_link_token else None,
            "token_expires_at": user.telegram_link_expires_at,
            "telegram_connected_at": user.telegram_connected_at,
            "telegram_notifications_enabled": user.telegram_notifications_enabled,
            "telegram_marketing_enabled": user.telegram_marketing_enabled,
            "subscribers_count": self.count_barber_subscribers(user) if user.role == UserRole.BARBER else 0,
        }

    def handle_webhook(self, update: dict) -> None:
        message = update.get("message") or update.get("edited_message") or {}
        text = str(message.get("text") or "").strip()
        chat = message.get("chat") or {}
        chat_id = chat.get("id")

        if not text.startswith("/start") or not isinstance(chat_id, int):
            return

        token = text.split(maxsplit=1)[1].strip() if " " in text else ""
        if not token:
            self.send_message(
                chat_id,
                (
                    "👋 Assalomu alaykum!\n\n"
                    "💈 Botga ulanish uchun ilovadagi QR kodni skaner qiling "
                    "yoki maxsus ulanish havolasi orqali qayta /start bosing.\n\n"
                    "🪮 Sizning qulayligingiz uchun bot tayyor!"
                ),
            )
            return

        user = self._get_user_by_link_token(token)
        if not user:
            self.send_message(
                chat_id,
                (
                    "⚠️ Ulanish havolasi eskirgan yoki noto‘g‘ri.\n\n"
                    "🔄 Iltimos, ilovadan yangi QR kod yoki yangi ulanish havolasini oling.\n\n"
                    "💈 Barber Shop bot sizni kutmoqda!"
                ),
            )
            return

        self._connect_chat(user, chat_id)
        self.send_message(chat_id, self._build_connected_message(user))

    def send_booking_created_notification(self, booking: Booking) -> bool:
        barber = booking.barber
        if not barber.telegram_chat_id or not barber.telegram_notifications_enabled:
            return False

        text = (
            "🔥 <b>Yangi bron tushdi!</b>\n\n"
            f"👤 <b>Klient:</b> {booking.client_name}\n"
            f"📞 <b>Telefon:</b> {booking.client_phone}\n"
            f"📅 <b>Sana:</b> {booking.appointment_date.isoformat()}\n"
            f"⏰ <b>Vaqt:</b> {booking.appointment_time.strftime('%H:%M')}\n"
            f"🔑 <b>Bron kodi:</b> {booking.booking_code}\n\n"
            "💈 <i>Tayyor turing, mijoz kelmoqda!</i>"
        )
        return self.send_message(barber.telegram_chat_id, text)

    def send_booking_status_notification(self, booking: Booking) -> bool:
        customer = booking.customer
        if not customer or not customer.telegram_chat_id or not customer.telegram_notifications_enabled:
            return False

        status_label = {
            BookingStatus.PENDING: "⏳ Barber tasdiqlashi kutilmoqda",
            BookingStatus.CONFIRMED: "✅ Tasdiqlandi",
            BookingStatus.COMPLETED: "🏁 Yakunlandi",
            BookingStatus.CANCELLED: "❌ Bekor qilindi",
        }[booking.status]

        text = (
            "💈 <b>Bron holati yangilandi</b>\n\n"
            f"📌 <b>Holat:</b> {status_label}\n"
            f"🧔 <b>Barber:</b> {booking.barber_name}\n"
            f"📅 <b>Sana:</b> {booking.appointment_date.isoformat()}\n"
            f"⏰ <b>Vaqt:</b> {booking.appointment_time.strftime('%H:%M')}\n"
            f"🔑 <b>Bron kodi:</b> {booking.booking_code}\n\n"
            "🪮 <i>Style — bu ishonch!</i>"
        )
        return self.send_message(customer.telegram_chat_id, text)

    def send_promotion_to_barber_customers(
        self,
        barber: User,
        payload: TelegramPromotionCreate,
    ) -> dict[str, int]:
        recipients = self._get_barber_subscribers(barber)
        title = payload.title or "Yangi aksiya"

        text = (
            f"✨ <b>{title}</b>\n\n"
            f"💈 <b>Barber:</b> {barber.full_name}\n\n"
            f"🔥 {payload.message}\n\n"
            "📅 Qulay vaqtni tanlab, hoziroq bron qiling!\n"
            "🪮 <i>Yangi imij — yangi ishonch!</i>"
        )

        delivered = 0
        for recipient in recipients:
            if recipient.telegram_chat_id and self.send_message(recipient.telegram_chat_id, text):
                delivered += 1

        return {
            "total_recipients": len(recipients),
            "delivered_recipients": delivered,
            "failed_recipients": len(recipients) - delivered,
        }

    def send_service_promotion_update(
        self,
        barber: User,
        previous_services: list[dict[str, object]] | None,
        current_services: list[dict[str, object]] | None,
    ) -> dict[str, int]:
        recipients = self._get_barber_subscribers(barber)
        if not recipients:
            return {
                "total_recipients": 0,
                "delivered_recipients": 0,
                "failed_recipients": 0,
            }

        changed_promotions = self._collect_changed_promotions(previous_services, current_services)
        if not changed_promotions:
            return {
                "total_recipients": len(recipients),
                "delivered_recipients": 0,
                "failed_recipients": 0,
            }

        text = self._build_service_promotion_message(barber, changed_promotions)

        delivered = 0
        for recipient in recipients:
            if recipient.telegram_chat_id and self.send_message(recipient.telegram_chat_id, text):
                delivered += 1

        return {
            "total_recipients": len(recipients),
            "delivered_recipients": delivered,
            "failed_recipients": len(recipients) - delivered,
        }

    def count_barber_subscribers(self, barber: User) -> int:
        return len(self._get_barber_subscribers(barber))

    def send_message(self, chat_id: int, text: str) -> bool:
        if not self.bot_token:
            return False

        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )

            if response.status_code != 200:
                logger.warning(
                    "Telegram sendMessage failed: status=%s body=%s",
                    response.status_code,
                    response.text,
                )
                return False

            return True

        except requests.RequestException as exc:
            logger.warning("Telegram sendMessage failed: %s", exc)
            return False

    def _issue_link_token(self, user: User) -> None:
        user.telegram_link_token = secrets.token_urlsafe(24)
        user.telegram_link_expires_at = datetime.now(settings.app_timezone) + timedelta(
            minutes=settings.TELEGRAM_LINK_EXPIRE_MINUTES
        )
        self.db.add(user)
        self.commit()
        self.refresh(user)

    def _connect_chat(self, user: User, chat_id: int) -> None:
        existing_chat_owner = self.db.execute(
            select(User).where(User.telegram_chat_id == chat_id, User.id != user.id)
        ).scalar_one_or_none()

        if existing_chat_owner:
            existing_chat_owner.telegram_chat_id = None
            existing_chat_owner.telegram_notifications_enabled = False
            existing_chat_owner.telegram_marketing_enabled = False
            existing_chat_owner.telegram_connected_at = None
            self.db.add(existing_chat_owner)
            self.db.flush()

        user.telegram_chat_id = chat_id
        user.telegram_notifications_enabled = True
        user.telegram_marketing_enabled = user.role == UserRole.USER
        user.telegram_connected_at = datetime.now(settings.app_timezone)
        user.telegram_link_token = None
        user.telegram_link_expires_at = None

        self.db.add(user)
        self.commit()
        self.refresh(user)

    def _get_user_by_link_token(self, token: str) -> User | None:
        statement = select(User).where(User.telegram_link_token == token.strip())
        user = self.db.execute(statement).scalar_one_or_none()

        if not user or self._is_token_expired(user):
            return None

        return user

    def _get_barber_subscribers(self, barber: User) -> list[User]:
        statement = (
            select(User)
            .join(Booking, Booking.customer_id == User.id)
            .where(
                Booking.barber_id == barber.id,
                User.role == UserRole.USER,
                User.telegram_chat_id.is_not(None),
                User.telegram_marketing_enabled.is_(True),
            )
            .group_by(User.id)
            .order_by(func.max(Booking.created_at).desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def _is_token_expired(self, user: User) -> bool:
        return bool(
            user.telegram_link_expires_at
            and user.telegram_link_expires_at <= datetime.now(settings.app_timezone)
        )

    def _build_bot_url(self) -> str | None:
        if not self.bot_username:
            return None
        return f"https://t.me/{self.bot_username}"

    def _build_deep_link(self, token: str | None) -> str | None:
        if not token or not self.bot_username:
            return None
        return f"https://t.me/{self.bot_username}?start={token}"

    @staticmethod
    def _normalize_service_name(value: object) -> str:
        return " ".join(str(value or "").strip().split()).lower()

    @staticmethod
    def _normalize_promotion_text(value: object) -> str | None:
        normalized = " ".join(str(value or "").strip().split())
        return normalized or None

    @staticmethod
    def _normalize_price(value: object) -> int | None:
        if value is None or value == "":
            return None

        try:
            return int(Decimal(str(value)))
        except Exception:
            return None

    @classmethod
    def _collect_changed_promotions(
        cls,
        previous_services: list[dict[str, object]] | None,
        current_services: list[dict[str, object]] | None,
    ) -> list[dict[str, object]]:
        previous_by_name = {
            cls._normalize_service_name(item.get("name")): item
            for item in (previous_services or [])
            if cls._normalize_service_name(item.get("name"))
        }

        changed: list[dict[str, object]] = []

        for item in current_services or []:
            normalized_name = cls._normalize_service_name(item.get("name"))
            if not normalized_name:
                continue

            old_item = previous_by_name.get(normalized_name, {})
            old_discount = cls._normalize_price(old_item.get("discount_price"))
            new_discount = cls._normalize_price(item.get("discount_price"))
            old_promotion_text = cls._normalize_promotion_text(old_item.get("promotion_text"))
            new_promotion_text = cls._normalize_promotion_text(item.get("promotion_text"))

            has_new_promo = bool(new_promotion_text or new_discount is not None)
            promo_changed = old_discount != new_discount or old_promotion_text != new_promotion_text

            if has_new_promo and promo_changed:
                changed.append(item)

        return changed

    @staticmethod
    def _format_price(value: object) -> str | None:
        if value is None or value == "":
            return None

        try:
            amount = int(Decimal(str(value)))
        except Exception:
            return None

        return f"{amount:,}".replace(",", " ") + " so‘m"

    @classmethod
    def _build_service_promotion_message(cls, barber: User, services: list[dict[str, object]]) -> str:
        intro = [
            "✨ <b>Yangi aksiya bor!</b>",
            "",
            f"💈 <b>Barber:</b> {barber.full_name}",
            "🪮 <i>Premium style uchun maxsus taklif!</i>",
            "",
        ]

        if len(services) == 1:
            service = services[0]
            discount_price = cls._format_price(service.get("discount_price"))
            regular_price = cls._format_price(service.get("price"))
            promotion_text = cls._normalize_promotion_text(service.get("promotion_text"))

            lines = [
                f"✂️ <b>Xizmat:</b> {service.get('name')}",
            ]

            if discount_price and regular_price:
                lines.append(f"💰 <b>Narx:</b> <s>{regular_price}</s> → <b>{discount_price}</b>")
            elif regular_price:
                lines.append(f"💰 <b>Narx:</b> {regular_price}")

            if promotion_text:
                lines.append(f"🔥 <b>Aksiya:</b> {promotion_text}")

            lines.extend(
                [
                    "",
                    "📅 Ilovaga kirib qulay vaqtga bron qiling.",
                    "😎 <i>Yangi ko‘rinish — yangi ishonch!</i>",
                ]
            )

            return "\n".join(intro + lines)

        body = ["🔥 <b>Quyidagi xizmatlarda yangilanish bor:</b>", ""]

        for service in services[:5]:
            row = f"• ✂️ <b>{service.get('name')}</b>"

            discount_price = cls._format_price(service.get("discount_price"))
            regular_price = cls._format_price(service.get("price"))
            promotion_text = cls._normalize_promotion_text(service.get("promotion_text"))

            if discount_price and regular_price:
                row += f" — <s>{regular_price}</s> → <b>{discount_price}</b>"
            elif regular_price:
                row += f" — {regular_price}"

            if promotion_text:
                row += f"\n  🔥 {promotion_text}"

            body.append(row)

        body.extend(
            [
                "",
                "📅 Ilovaga kirib o‘zingizga mos xizmatni tanlang.",
                "💈 <i>Style — bu oddiy soch emas, bu imij!</i>",
            ]
        )

        return "\n".join(intro + body)

    @staticmethod
    def _build_connected_message(user: User) -> str:
        if user.role == UserRole.BARBER:
            return (
                "✅ <b>Bot muvaffaqiyatli ulandi!</b>\n\n"
                "💈 Endi yangi bron tushsa, Telegram orqali darhol xabar olasiz.\n"
                "📅 Mijozlar navbati va bronlar sizga tezkor yetib boradi.\n\n"
                "🔥 <i>Ishingizga omad, barber!</i>"
            )

        return (
            "✅ <b>Bot muvaffaqiyatli ulandi!</b>\n\n"
            "💈 Endi siz yangiliklar, aksiyalar va bron bo‘yicha xabarlarni "
            "birinchi bo‘lib olasiz.\n\n"
            "🪮 Soch turmagi, soqol parvarishi va premium style — hammasi shu yerda!\n"
            "📅 Qulay vaqtni tanlab, oson bron qiling.\n\n"
            "😎 <i>Yangi imij — yangi ishonch!</i>"
        )
