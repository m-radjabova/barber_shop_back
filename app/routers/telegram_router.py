from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_barber
from app.models.user import User
from app.schemas.user import TelegramLinkOut, TelegramPromotionCreate, TelegramPromotionResultOut
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.get("/me", response_model=TelegramLinkOut)
def get_my_telegram_link(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TelegramService(db).get_connection_info(current_user)


@router.post("/me/link", response_model=TelegramLinkOut, status_code=status.HTTP_201_CREATED)
def refresh_my_telegram_link(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TelegramService(db).get_connection_info(current_user, refresh_token=True)


@router.post("/promotions", response_model=TelegramPromotionResultOut)
def send_barber_promotion(
    payload: TelegramPromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_barber),
):
    return TelegramService(db).send_promotion_to_barber_customers(current_user, payload)
