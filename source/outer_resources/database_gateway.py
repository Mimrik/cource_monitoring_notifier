import logging
from dataclasses import dataclass

from typing import TypeVar

from sqlalchemy import select, update
from sqlalchemy_tools.database_connector.database_session_maker import DatabaseSessionMaker

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.host_to_host_group import HostToHostGroup
from utils.timestamp_converters import get_current_time_sec

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

    # SELECT

    async def select(self, entity_type: type[Entity]) -> list[Entity]:
        async with self.ensure_session() as session:
            query = select(entity_type)
            query = query.where(entity_type.id > 0)
            return (await session.execute(query)).scalars().all()

    async def get_hosts_by_host_group_id(self, host_group_id: int) -> list[Host]:
        async with self.ensure_session() as session:
            query = select(
                Host
            ).join(
                HostToHostGroup, HostToHostGroup.host_id == Host.id
            ).join(
                HostGroup, HostGroup.id == HostToHostGroup.host_group_id
            ).where(
                HostGroup.id == host_group_id
            )
            return (await session.execute(query)).scalars().all()

    # INSERT

    async def insert(self, entities: Entity | list[Entity]) -> None:
        if not isinstance(entities, list):
            entities = [entities]

        async with self.ensure_session() as session:
            for entity in entities:
                session.add(entity)
            await session.flush()

    # UPDATE

    async def enable_host_groups(self, host_group_ids: list[int]) -> None:
        async with self.ensure_session() as session:
            query = update(
                HostGroup
            ).where(
                HostGroup.id.in_(host_group_ids)
            ).values(
                {HostGroup.disabled_at: None}
            ).returning(
                HostGroup
            )
            await session.execute(query)

    async def disable_host_groups(self, host_group_ids: list[int]) -> None:
        async with self.ensure_session() as session:
            query = update(
                HostGroup
            ).where(
                HostGroup.id.in_(host_group_ids),
            ).values(
                {HostGroup.disabled_at: get_current_time_sec()}
            ).returning(
                HostGroup
            )
            await session.execute(query)
