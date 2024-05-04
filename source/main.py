"""Main module."""
import asyncio
import logging
from typing import NoReturn
from initer import Initer


logger = logging.getLogger(__name__)


initer = Initer()


async def main() -> NoReturn:
    """Init components and work."""
    async with initer:
        while True:
            await asyncio.sleep(1)

try:
    asyncio.run(main())
except KeyboardInterrupt as e:
    logger.warning(f"Shutting down: {repr(e)}")
