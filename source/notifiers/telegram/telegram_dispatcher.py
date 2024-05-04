"""TelegramDispatcher module."""
import asyncio
import logging
from dataclasses import dataclass
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from notifiers.telegram.telegram_bot import TelegramBot

logger = logging.getLogger(__name__)


class TelegramDispatcher(Dispatcher):
    """Telegram dispatcher."""

    @dataclass
    class Context:
        """context."""

        telegram_bot: TelegramBot

    def __init__(self, context: Context):
        """init."""
        super().__init__(context.telegram_bot, storage=MemoryStorage())
        asyncio.create_task(self.start_polling())
        logger.info(f"{type(self).__name__} inited")
