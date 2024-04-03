import asyncio
import logging
from typing import NoReturn
from initer import Initer


logger = logging.getLogger(__name__)


initer = Initer()


async def main() -> NoReturn:
    async with initer as controller:
        await controller.run()

try:
    asyncio.run(main())
except KeyboardInterrupt as e:
    logger.warning(f"Shutting down: {repr(e)}")
