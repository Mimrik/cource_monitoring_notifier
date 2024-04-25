import logging
from dataclasses import dataclass

from typing import TypeVar

from sqlalchemy import select, update, delete
from sqlalchemy_tools.database_connector.database_session_maker import DatabaseSessionMaker

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.host_to_host_group import HostToHostGroup
from entities.monitoring_system_structure.trigger import Trigger
from entities.notification_sink import NotificationSink
from entities.notification_sink_to_trigger import NotificationSinkToTrigger
from entities.time_zone import TimeZone
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

    async def get_entity_by_id(self, entity_type: type[Entity], entity_id: int) -> Entity:
        async with self.ensure_session() as session:
            query = select(
                entity_type
            ).where(
                entity_type.id == entity_id
            )
            return (await session.execute(query)).scalar()

    async def get_host_id_by_trigger_id(self, trigger_id: int) -> int:
        async with self.ensure_session() as session:
            query = select(
                Host.id
            ).join(
                Trigger, Trigger.host_id == Host.id
            ).where(
                Trigger.id == trigger_id
            )
            return (await session.execute(query)).scalar()

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

    async def get_host_groups_by_host_id(self, host_id: int) -> list[HostGroup]:
        async with self.ensure_session() as session:
            query = select(
                HostGroup
            ).join(
                HostToHostGroup, HostToHostGroup.host_group_id == HostGroup.id
            ).join(
                Host, Host.id == HostToHostGroup.host_id
            ).where(
                Host.id == host_id
            )
            return (await session.execute(query)).scalars().all()

    async def get_triggers_by_host_id(self, host_id: int) -> list[Trigger]:
        async with self.ensure_session() as session:
            query = select(
                Trigger
            ).where(
                Trigger.host_id == host_id
            )
            return (await session.execute(query)).scalars().all()

    async def get_triggers_by_notification_sink_id(self, notification_sink_id: int) -> list[Trigger]:
        async with self.ensure_session() as session:
            query = select(
                Trigger
            ).join(
                NotificationSinkToTrigger, NotificationSinkToTrigger.trigger_id == Trigger.id,
            ).where(
                NotificationSinkToTrigger.notification_sink_id == notification_sink_id
            )
            return (await session.execute(query)).scalars().all()

    async def get_notification_sinks_by_trigger_id(self, trigger_id: int) -> list[NotificationSink]:
        async with self.ensure_session() as session:
            query = select(
                NotificationSink
            ).join(
                NotificationSinkToTrigger, NotificationSinkToTrigger.notification_sink_id == NotificationSink.id,
            ).where(
                NotificationSinkToTrigger.trigger_id == trigger_id
            )
            return (await session.execute(query)).scalars().all()

    async def get_notification_sink(self, recipient_id: str) -> NotificationSink:
        async with self.ensure_session() as session:
            query = select(
                NotificationSink
            ).where(
                NotificationSink.recipient_id == recipient_id
            )
            return (await session.execute(query)).scalar()

    async def get_notification_sink_time_zone(self, notification_sink_id: int) -> TimeZone:
        async with self.ensure_session() as session:
            query = select(
                TimeZone
            ).join(
                NotificationSink, NotificationSink.time_zone_id == TimeZone.id
            ).where(
                NotificationSink.id == notification_sink_id
            )
            return (await session.execute(query)).scalar()

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

    async def update_notification_sink_time_zone_id(self, notification_sink_id: int, time_zone_id: int) -> None:
        async with self.ensure_session() as session:
            query = update(
                NotificationSink
            ).where(
                NotificationSink.id == notification_sink_id
            ).values(
                {NotificationSink.time_zone_id: time_zone_id}
            ).returning(
                NotificationSink.id
            )
            await session.execute(query)

    # DELETE:

    async def delete_notification_sink_to_trigger_by_id(self, notification_sink_id: int, trigger_id: int) -> None:
        async with self.ensure_session() as session:
            query = delete(
                NotificationSinkToTrigger
            ).where(
                NotificationSinkToTrigger.trigger_id == trigger_id,
                NotificationSinkToTrigger.notification_sink_id == notification_sink_id,
            ).execution_options(
                synchronize_session=False
            )
            await session.execute(query)

    async def delete_notification_sink_to_trigger(self, notification_sink_id: int) -> None:
        async with self.ensure_session() as session:
            query = delete(
                NotificationSinkToTrigger
            ).where(
                NotificationSinkToTrigger.notification_sink_id == notification_sink_id,
            ).execution_options(
                synchronize_session=False
            )
            await session.execute(query)
