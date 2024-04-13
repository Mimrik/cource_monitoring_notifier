import asyncio
import logging
from dataclasses import dataclass
from typing import NoReturn

logger = logging.getLogger(__name__)


@dataclass
class MonitoringEvent:
    external_id: str
    trigger_external_id: str
    opdata: str
    occurred_at: int
    resolved_at: int | None = None


class Controller:
    @dataclass
    class Config:
        ...

    @dataclass
    class Context:
        ...

    def __init__(self, context: Context):
        self.context = context
        logger.info(f"{type(self).__name__} inited")

    async def run(self) -> NoReturn:
        while True:
            await asyncio.sleep(1)
