import logging
from dataclasses import dataclass

import init_helpers
from async_tools import AsyncInitable, AsyncDeinitable
from init_helpers import init_logs

from controller import Controller

logger = logging.getLogger(__name__)


@dataclass
class Initer:
    @dataclass
    class Config:
        logging: init_helpers.LogsConfig

    config: Config

    @dataclass
    class Context(AsyncInitable, AsyncDeinitable):
        controller: Controller = None

        def __post_init__(self):
            AsyncInitable.__init__(self)
            AsyncDeinitable.__init__(self)

    context: Context

    def __init__(self) -> None:
        self.context = self.Context()
        self.config = init_helpers.parse_args(config_file=init_helpers.Arg.ini_file_to_dataclass(self.Config))
        init_logs(self.config.logging)
        logger.info(f"Config: {self.config}")

    async def __aenter__(self) -> Controller:
        self.context.controller = Controller(self.context)

        await self.context.async_init()
        logger.info("----===== Init done ====----")
        return self.context.controller

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.context.async_deinit()
        logger.info(f"----===== Deinit done ====----")
