import logging
from dataclasses import dataclass
from typing import TypeVar

from sqlalchemy_tools.database_connector.database_session_maker import DatabaseSessionMaker


logger = logging.getLogger(__name__)


Entity = TypeVar("Entity")


class DatabaseGateway:
    @dataclass
    class Context:
        database_session_maker: DatabaseSessionMaker

    def __init__(self, context: Context) -> None:
        self.context = context
        self.ensure_session = self.context.database_session_maker.ensure_session
        logger.info(f"{type(self).__name__} inited")
