from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.dependencies.auth import _resolve_user_from_token
from app.models.enums import UserRole
from app.services.booking_ws import barber_booking_ws_manager, customer_booking_ws_manager

router = APIRouter(tags=["Booking WebSocket"])


@router.websocket("/ws/bookings/barber")
async def barber_bookings_socket(websocket: WebSocket, token: str | None = None):
    db: Session = SessionLocal()
    user = None
    try:
        user = _resolve_user_from_token(token, db)
        if not user or user.role != UserRole.BARBER:
            await websocket.close(code=1008)
            return

        await barber_booking_ws_manager.connect(user.id, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        if user is None:
            await websocket.close(code=1008)
    finally:
        if user is not None:
            barber_booking_ws_manager.disconnect(user.id, websocket)
        db.close()


@router.websocket("/ws/bookings/customer")
async def customer_bookings_socket(websocket: WebSocket, token: str | None = None):
    db: Session = SessionLocal()
    user = None
    try:
        user = _resolve_user_from_token(token, db)
        if not user or user.role != UserRole.USER:
            await websocket.close(code=1008)
            return

        await customer_booking_ws_manager.connect(user.id, websocket)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        if user is None:
            await websocket.close(code=1008)
    finally:
        if user is not None:
            customer_booking_ws_manager.disconnect(user.id, websocket)
        db.close()
