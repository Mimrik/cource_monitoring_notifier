"""Database module."""
import asyncio
import logging
from dataclasses import dataclass
from typing import NoReturn

from async_tools import AsyncInitable

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.host_to_host_group import HostToHostGroup
from entities.monitoring_system_structure.trigger import Trigger
from monitoring_systems.abstract_monitoring_system_controller import AbstractMonitoringSystemController

from outer_resources.database_gateway import DatabaseGateway

logger = logging.getLogger(__name__)


@dataclass
class HostGroupsDiff:
    """HostGroupsDiff."""

    new_host_groups: list[HostGroup]
    obsolete_host_groups: list[HostGroup]
    enabled_host_groups: list[HostGroup]


@dataclass
class HostSource:
    """HostSource."""

    host_group_id: int
    host: Host


@dataclass
class HostsDiff:
    """HostsDiff."""

    new_host_sources: list[HostSource]
    obsolete_host_sources: list[HostSource]
    enabled_host_sources: list[HostSource]


@dataclass
class TriggersDiff:
    """TriggersDiff."""

    appeared_triggers: list[Trigger]
    obsolete_triggers: list[Trigger]
    enabled_triggers: list[Trigger]


class DatabaseActualizer(AsyncInitable):
    """Update Zabbix entities in the database."""

    @dataclass
    class Config:
        """config."""

        actualization_interval_sec: int

    @dataclass
    class Context:
        """context."""

        database_gateway: DatabaseGateway
        monitoring_system_controller: AbstractMonitoringSystemController

    def __init__(self, config: Config, context: Context) -> None:
        """init."""
        AsyncInitable.__init__(self)
        self.config = config
        self.context = context
        logger.info(f"{type(self).__name__} inited")

    async def _async_init(self) -> None:
        """Start actualizing task on application start.."""
        await self._actualize_monitoring_system_structure()

    async def _actualize_monitoring_system_structure(self) -> NoReturn:
        """Update Zabbix entities in the database."""
        while True:
            try:
                await self._actualize_host_groups()
                await self._actualize_hosts()
                await self._actualize_triggers()
            except Exception as er:
                logger.error(f"Monitoring system structures update failed: {repr(er)}")
            await asyncio.sleep(self.config.actualization_interval_sec)

    async def _actualize_host_groups(self) -> None:
        """Update Zabbix host groups in the database."""
        actual_host_groups = await self.context.monitoring_system_controller.get_host_groups()
        saved_host_groups = await self.context.database_gateway.select(HostGroup)

        host_group_diff = await self._cast_host_groups_diff(
            actual_host_groups=actual_host_groups,
            saved_host_groups=saved_host_groups,
        )
        await self.context.database_gateway.insert(host_group_diff.new_host_groups)
        await self.context.database_gateway.enable_host_groups(
            [host_group.id for host_group in host_group_diff.enabled_host_groups]
        )
        await self.context.database_gateway.disable_host_groups(
            [host_group.id for host_group in host_group_diff.obsolete_host_groups]
        )

        logger.info(
            f"Inserted {len(host_group_diff.new_host_groups)} new host groups. "
            f"Enabled {len(host_group_diff.enabled_host_groups)} host groups. "
            f"Disabled {len(host_group_diff.obsolete_host_groups)} obsolete host groups"
        )

    @staticmethod
    async def _cast_host_groups_diff(
            *,
            actual_host_groups: list[HostGroup],
            saved_host_groups: list[HostGroup],
    ) -> HostGroupsDiff:
        """Collect group hosts difference with Zabbix and DB."""
        actual_host_group_id_to_host_group = {host_group.id: host_group for host_group in actual_host_groups}
        actual_host_group_ids = set(actual_host_group_id_to_host_group)

        saved_host_group_id_to_host_group = {host_group.id: host_group for host_group in saved_host_groups}
        saved_host_group_ids = set(saved_host_group_id_to_host_group)

        disabled_host_group_id_to_host_group = {
            host_group.id: host_group for host_group in saved_host_groups if host_group.disabled_at
        }
        disabled_host_group_ids = set(disabled_host_group_id_to_host_group)

        appeared_host_group_external_ids = actual_host_group_ids - saved_host_group_ids
        enabled_host_group_external_ids = disabled_host_group_ids & actual_host_group_ids
        obsolete_host_group_external_ids = saved_host_group_ids - disabled_host_group_ids - actual_host_group_ids

        return HostGroupsDiff(
            new_host_groups=[actual_host_group_id_to_host_group[host_group_external_id]
                             for host_group_external_id in appeared_host_group_external_ids],
            enabled_host_groups=[saved_host_group_id_to_host_group[host_group_external_id]
                                 for host_group_external_id in enabled_host_group_external_ids],
            obsolete_host_groups=[saved_host_group_id_to_host_group[host_group_external_id]
                                  for host_group_external_id in obsolete_host_group_external_ids],
        )

    async def _actualize_hosts(self) -> None:
        """Update Zabbix hosts in the database."""
        actual_host_group_id_to_hosts = await self.context.monitoring_system_controller.get_host_group_id_to_hosts()

        saved_host_group_id_to_hosts = await self._get_host_group_id_to_hosts()

        hosts_diff = await self._cast_hosts_diff(
            actual_host_group_id_to_hosts=actual_host_group_id_to_hosts,
            saved_host_group_id_to_hosts=saved_host_group_id_to_hosts,
        )

        await self._insert_host_sources(hosts_diff.new_host_sources)

        logger.info(f"Inserted {len(hosts_diff.new_host_sources)} new host sources. "
                    f"Enabled {len([])} host sources. "
                    f"Disabled {len([])} obsolete host sources")

    @staticmethod
    async def _cast_hosts_diff(
        *,
        actual_host_group_id_to_hosts: dict[int, list[Host]],
        saved_host_group_id_to_hosts: dict[int, list[Host]],
    ) -> HostsDiff:
        """Collect hosts difference with Zabbix and DB."""
        actual_host_group_id_to_host_ids: dict[int, set[int]] = {}
        actual_host_id_to_host = {}
        for group_id, hosts in actual_host_group_id_to_hosts.items():
            for host in hosts:
                actual_host_group_id_to_host_ids.setdefault(group_id, set()).add(host.id)
                actual_host_id_to_host[host.id] = host

        saved_host_group_id_to_host_ids: dict[int, set[int]] = {}
        saved_host_id_to_host = {}
        for group_id, hosts in saved_host_group_id_to_hosts.items():
            for host in hosts:
                saved_host_group_id_to_host_ids.setdefault(group_id, set()).add(host.id)
                saved_host_id_to_host[host.id] = host

        new_host_sources = []
        for group_id, actual_host_ids in actual_host_group_id_to_host_ids.items():
            saved_host_ids = saved_host_group_id_to_host_ids.get(group_id)
            new_host_ids = actual_host_ids - saved_host_ids if saved_host_ids is not None else actual_host_ids
            for host_id in new_host_ids:
                new_host_sources.append(HostSource(host_group_id=group_id, host=actual_host_id_to_host[host_id]))

        return HostsDiff(
            new_host_sources=new_host_sources,
            enabled_host_sources=[],
            obsolete_host_sources=[],
        )

    async def _insert_host_sources(self, host_sources: list[HostSource]) -> None:
        """Insert new hosts to DB."""
        if not host_sources:
            return

        for host_source in host_sources:
            await self.context.database_gateway.insert(host_source.host)
            await self.context.database_gateway.insert(
                HostToHostGroup(host_id=host_source.host.id, host_group_id=host_source.host_group_id)
            )

    async def _actualize_triggers(self) -> None:
        """Update Zabbix triggers in the database."""
        actual_triggers = await self.context.monitoring_system_controller.get_triggers()
        saved_triggers = await self.context.database_gateway.select(Trigger)

        triggers_diff = await self._cast_triggers_diff(
            actual_triggers=actual_triggers,
            saved_triggers=saved_triggers,
        )

        await self.context.database_gateway.insert(triggers_diff.appeared_triggers)

        logger.info(f"Inserted {len(triggers_diff.appeared_triggers)} new triggers. "
                    f"Enabled {len(triggers_diff.enabled_triggers)} triggers. "
                    f"Disabled {len(triggers_diff.obsolete_triggers)} obsolete triggers")

    @staticmethod
    async def _cast_triggers_diff(*, actual_triggers: list[Trigger], saved_triggers: list[Trigger]) -> TriggersDiff:
        """Collect triggers difference with Zabbix and DB."""
        actual_trigger_id_to_trigger = {trigger.id: trigger for trigger in actual_triggers}
        actual_trigger_ids = set(actual_trigger_id_to_trigger)
        saved_trigger_id_to_trigger = {trigger.id: trigger for trigger in saved_triggers}
        saved_trigger_ids = set(saved_trigger_id_to_trigger)

        saved_disabled_trigger_id_to_trigger = {
            trigger.id: trigger for trigger in saved_triggers if trigger.disabled_at
        }
        saved_disabled_trigger_ids = set(saved_disabled_trigger_id_to_trigger)

        new_trigger_ids = actual_trigger_ids - saved_trigger_ids
        obsolete_trigger_ids = saved_trigger_ids - saved_disabled_trigger_ids - actual_trigger_ids
        enabled_trigger_ids = saved_disabled_trigger_ids & actual_trigger_ids

        return TriggersDiff(
            appeared_triggers=[actual_trigger_id_to_trigger[trigger_id] for trigger_id in new_trigger_ids],
            enabled_triggers=[saved_trigger_id_to_trigger[trigger_id] for trigger_id in enabled_trigger_ids],
            obsolete_triggers=[saved_trigger_id_to_trigger[trigger_id] for trigger_id in obsolete_trigger_ids],
        )

    async def _get_host_group_id_to_hosts(self) -> dict[int, list[Host]]:
        """Get host groups and hosts from DB."""
        host_group_id_to_hosts: dict[int, list[Host]] = {}
        async with self.context.database_gateway.ensure_session():
            host_groups = await self.context.database_gateway.select(HostGroup)
            for host_group in host_groups:
                hosts = await self.context.database_gateway.get_hosts_by_host_group_id(host_group.id)
                host_group_id_to_hosts[host_group.id] = hosts

        return host_group_id_to_hosts
