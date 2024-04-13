import logging
from dataclasses import dataclass

import init_helpers
from aiohttp import ClientSession
from async_tools import AsyncInitable, AsyncDeinitable
from init_helpers import init_logs
from sqlalchemy_tools.database_connector.database_connector import DatabaseConnector
from sqlalchemy_tools.database_connector.database_session_maker import DatabaseSessionMaker

from controller import Controller
from outer_resources.database_gateway import DatabaseGateway
from outer_resources.zabbix_connector import ZabbixConnector

logger = logging.getLogger(__name__)


@dataclass
class Initer:
    @dataclass
    class Config:
        logging: init_helpers.LogsConfig
        database_connector: DatabaseConnector.Config
        zabbix_connector: ZabbixConnector.Config

    config: Config

    @dataclass
    class Context(AsyncInitable, AsyncDeinitable):
        client_session: ClientSession = None
        database_connector: DatabaseConnector = None
        database_gateway: DatabaseGateway = None
        database_session_maker: DatabaseSessionMaker = None
        zabbix_connector: ZabbixConnector = None
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
        self._init_database_components()
        self.context.client_session = ClientSession()
        self._init_zabbix_components()

        self.context.controller = Controller(self.context)

        await self.context.async_init()
        return self.context.controller

    def _init_database_components(self) -> None:
        self.context.database_connector = DatabaseConnector(self.config.database_connector)
        self.context.database_session_maker = DatabaseSessionMaker(self.context)
        self.context.database_gateway = DatabaseGateway(self.context)

    def _init_zabbix_components(self) -> None:
        self.context.zabbix_connector = ZabbixConnector(self.config.zabbix_connector, self.context)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.context.async_deinit()
        logger.info(f"----===== Deinit done ====----")
