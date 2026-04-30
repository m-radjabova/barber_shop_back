from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class TelegramPollingRunner:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._stopped: asyncio.Event | None = None
        self._offset = 0
        self._conflict_logged = False

    def should_run(self) -> bool:
        return bool(settings.TELEGRAM_USE_POLLING and settings.TELEGRAM_BOT_TOKEN)

    async def start(self) -> None:
        if not self.should_run() or self._task is not None:
            if not self.should_run():
                logger.info("Telegram polling is disabled or bot token is not configured.")
            return
        self._stopped = asyncio.Event()
        self._stopped.clear()
        self._task = asyncio.create_task(self._run(), name="telegram-polling-runner")
        self._task.add_done_callback(self._handle_task_done)
        logger.info("Telegram polling started.")

    async def stop(self) -> None:
        if self._stopped:
            self._stopped.set()
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        self._stopped = None
        logger.info("Telegram polling stopped.")

    async def _run(self) -> None:
        base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
        api_url = f"{base_url}/getUpdates"
        async with httpx.AsyncClient(timeout=35.0) as client:
            await self._delete_webhook(client, base_url)
            while self._stopped and not self._stopped.is_set():
                try:
                    response = await client.get(
                        api_url,
                        params={"timeout": 25, "offset": self._offset},
                    )
                    response.raise_for_status()
                    self._conflict_logged = False
                    payload = response.json()
                    for update in payload.get("result", []):
                        update_id = update.get("update_id")
                        if isinstance(update_id, int):
                            self._offset = max(self._offset, update_id + 1)
                        await asyncio.to_thread(self._process_update, update)
                except asyncio.CancelledError:
                    raise
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 409:
                        if not self._conflict_logged:
                            logger.warning(
                                "Telegram polling conflict (409). Another bot instance or webhook is using this token. "
                                "Polling will retry quietly every 30 seconds."
                            )
                            self._conflict_logged = True
                        await asyncio.sleep(30)
                        continue
                    logger.exception("Telegram polling failed: %s", exc)
                    await asyncio.sleep(3)
                except Exception as exc:
                    logger.exception("Telegram polling failed: %s", exc)
                    await asyncio.sleep(3)

    def _handle_task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            task.result()
        except Exception:
            logger.exception("Telegram polling task stopped unexpectedly.")
        finally:
            if self._task is task:
                self._task = None
                self._stopped = None

    async def _delete_webhook(self, client: httpx.AsyncClient, base_url: str) -> None:
        try:
            response = await client.get(f"{base_url}/deleteWebhook", params={"drop_pending_updates": False})
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Telegram webhook cleanup failed before polling start: %s", exc)

    @staticmethod
    def _process_update(update: dict) -> None:
        db = SessionLocal()
        try:
            TelegramService(db).handle_webhook(update)
        finally:
            db.close()


telegram_polling_runner = TelegramPollingRunner()
