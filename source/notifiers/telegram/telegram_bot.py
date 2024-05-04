"""TelegramBot module."""
import logging
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)


class TelegramBot(Bot):
    """Telegram bot."""

    @dataclass
    class Config:
        """config."""

        token: str
        proxy: Optional[str] = None
        connections_limit: Optional[int] = None

    def __init__(self, config: Config):
        """init."""
        super().__init__(
            token=config.token,
            connections_limit=config.connections_limit,
            proxy=config.proxy,
        )
        logger.info(f"{type(self).__name__} inited")

    async def check_is_bot_administrator(self, chat_id: int) -> bool:
        """Check is bot administrator in current chat."""
        if chat_id > 0:
            return True

        chat_administrators = await self.get_chat_administrators(chat_id=chat_id)
        for administrator in chat_administrators:
            if administrator.user.id == (await self.get_me()).id:
                return True

        return False
