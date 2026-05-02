from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time
from uuid import UUID

from fastapi import WebSocket

from app.models.booking import Booking


class BookingConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, barber_id: UUID | str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[str(barber_id)].add(websocket)

    def disconnect(self, barber_id: UUID | str, websocket: WebSocket) -> None:
        connections = self._connections.get(str(barber_id))
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(str(barber_id), None)

    async def broadcast_booking_created(self, booking: Booking) -> None:
        await self._broadcast(str(booking.barber_id), "booking.created", booking)

    async def broadcast_booking_status_updated(self, booking: Booking) -> None:
        await self._broadcast(str(booking.barber_id), "booking.status_updated", booking)

    async def _broadcast(self, barber_id: str, event_type: str, booking: Booking) -> None:
        payload = {
            "type": event_type,
            "booking": serialize_booking(booking),
        }
        stale_connections: list[WebSocket] = []

        for websocket in list(self._connections.get(barber_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append(websocket)

        for websocket in stale_connections:
            self.disconnect(barber_id, websocket)


def _serialize_value(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    return value


def serialize_booking(booking: Booking) -> dict:
    return {
        "id": _serialize_value(booking.id),
        "booking_code": booking.booking_code,
        "barber_id": _serialize_value(booking.barber_id),
        "customer_id": _serialize_value(booking.customer_id) if booking.customer_id else None,
        "barber_name": booking.barber_name,
        "barber_avatar": booking.barber_avatar,
        "barber_specialty": booking.barber_specialty,
        "barber_rating": booking.barber_rating,
        "barber_reviews_count": booking.barber_reviews_count,
        "client_name": booking.client_name,
        "client_phone": booking.client_phone,
        "appointment_date": _serialize_value(booking.appointment_date),
        "appointment_time": _serialize_value(booking.appointment_time),
        "rating": booking.rating,
        "status": booking.status.value,
        "created_at": _serialize_value(booking.created_at),
    }


class CustomerBookingConnectionManager(BookingConnectionManager):
    async def broadcast_booking_created(self, booking: Booking) -> None:
        if not booking.customer_id:
            return
        await self._broadcast(str(booking.customer_id), "booking.created", booking)

    async def broadcast_booking_status_updated(self, booking: Booking) -> None:
        if not booking.customer_id:
            return
        await self._broadcast(str(booking.customer_id), "booking.status_updated", booking)


barber_booking_ws_manager = BookingConnectionManager()
customer_booking_ws_manager = CustomerBookingConnectionManager()
