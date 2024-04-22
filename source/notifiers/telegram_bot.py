import logging
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)


class TelegramBot(Bot):
    @dataclass
    class Config:
        token: str
        proxy: Optional[str] = None
        connections_limit: Optional[int] = None

    def __init__(self, config: Config):
        super().__init__(
            token=config.token,
            connections_limit=config.connections_limit,
            proxy=config.proxy,
        )
        logger.info(f"{type(self).__name__} inited")
