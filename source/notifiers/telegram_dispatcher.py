import asyncio
import logging
from dataclasses import dataclass
from aiogram import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from notifiers.telegram_bot import TelegramBot

logger = logging.getLogger(__name__)


class TelegramDispatcher(Dispatcher):
    @dataclass
    class Context:
        telegram_bot: TelegramBot

    def __init__(self, context: Context):
        super().__init__(context.telegram_bot, storage=MemoryStorage())
        asyncio.create_task(self.start_polling())
        logger.info(f"{type(self).__name__} inited")
