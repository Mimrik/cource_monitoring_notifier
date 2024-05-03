from dataclasses import dataclass
import asyncio
import logging
from enum import StrEnum, unique

from async_tools import AsyncInitable

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger
from monitoring_systems.abstract_monitoring_system_controller import AbstractMonitoringSystemController, MonitoringEvent
from outer_resources.zabbix_connector import ZabbixConnector, ZabbixProblem
from controller import Controller
from utils.timestamp_converters import get_current_time_sec

logger = logging.getLogger(__name__)


@unique
class TriggerStatus(StrEnum):
    RAISED = "raised"
    RESOLVED = "resolved"


class ZabbixController(AbstractMonitoringSystemController, AsyncInitable):
    @dataclass
    class Config:
        collection_interval_sec: int

    @dataclass
    class Context:
        controller: Controller
        zabbix_connector: ZabbixConnector

    def __init__(self, config: Config, context: Context) -> None:
        AsyncInitable.__init__(self)
        self.config = config
        self.context = context
        logger.info(f"{type(self).__name__} inited")

    async def get_host_groups(self) -> list[HostGroup]:
        zabbix_host_groups = await self.context.zabbix_connector.get_host_groups()
        return [HostGroup(id=int(group.groupid), title=group.name) for group in zabbix_host_groups]

    async def get_host_group_id_to_hosts(self) -> dict[int, list[Host]]:
        zabbix_hosts = await self.context.zabbix_connector.get_hosts()
        host_group_id_to_hosts = {}
        for host in zabbix_hosts:
            for group_id in host.group_ids:
                host_group_id_to_hosts.setdefault(int(group_id), []).append(Host(id=int(host.hostid), title=host.name))
        return host_group_id_to_hosts

    async def get_triggers(self) -> list[Trigger]:
        zabbix_triggers = await self.context.zabbix_connector.get_triggers()
        return [
            Trigger(
                id=int(trigger.triggerid),
                title=trigger.description,
                severity=int(trigger.priority),
                host_id=int(trigger.host_id)
            )
            for trigger in zabbix_triggers
        ]

    async def get_unresolved_events(self) -> list[MonitoringEvent]:
        current_cycle_problems = await self.context.zabbix_connector.get_problems()
        events = []
        for problem in current_cycle_problems:
            events.append(
                MonitoringEvent(
                    external_id=problem.external_id,
                    trigger_id=int(problem.trigger_external_id),
                    opdata=problem.opdata,
                    occurred_at=int(problem.occurred_at),
                    resolved_at=get_current_time_sec()
                )
            )
        return events

    async def _async_init(self) -> None:
        asyncio.create_task(self._collect_monitoring_events())

    async def _collect_monitoring_events(self) -> None:
        logger.debug("Collecting monitoring events started")
        events: list[MonitoringEvent] = []
        current_cycle_problems = await self.context.zabbix_connector.get_problems()
        previous_cycle_problems = current_cycle_problems

        while True:
            try:
                events.clear()
                current_cycle_problems = await self.context.zabbix_connector.get_problems()

                raised_problems = self._construct_raised_problems(current_cycle_problems, previous_cycle_problems)
                if raised_problems:
                    logger.debug(f"Raised problems: {raised_problems}")
                for problem in raised_problems:
                    events.append(
                        MonitoringEvent(
                            external_id=problem.external_id,
                            trigger_id=int(problem.trigger_external_id),
                            opdata=problem.opdata,
                            occurred_at=int(problem.occurred_at),
                        )
                    )

                resolved_problems = self._construct_resolved_problems(current_cycle_problems, previous_cycle_problems)
                if resolved_problems:
                    logger.debug(f"Resolved problems: {resolved_problems}")
                for problem in resolved_problems:
                    events.append(
                        MonitoringEvent(
                            external_id=problem.external_id,
                            trigger_id=int(problem.trigger_external_id),
                            opdata=problem.opdata,
                            occurred_at=int(problem.occurred_at),
                            resolved_at=get_current_time_sec()
                        )
                    )

                await self.context.controller.handle_monitoring_events(events)
                previous_cycle_problems = current_cycle_problems

            except Exception as e:
                logger.error(f"Error while collecting new monitoring events: {repr(e)}")

            await asyncio.sleep(self.config.collection_interval_sec)

    @staticmethod
    def _construct_raised_problems(
        current_cycle_problems: set[ZabbixProblem],
        previous_cycle_problems: set[ZabbixProblem],
    ) -> set[ZabbixProblem]:
        previous_problem_external_ids = {problem.external_id for problem in previous_cycle_problems}
        current_problem_external_ids = {problem.external_id for problem in current_cycle_problems}
        raised_problem_external_ids = current_problem_external_ids - previous_problem_external_ids

        return {problem for problem in current_cycle_problems if problem.external_id in raised_problem_external_ids}

    @staticmethod
    def _construct_resolved_problems(
        current_cycle_problems: set[ZabbixProblem],
        previous_cycle_problems: set[ZabbixProblem],
    ) -> set[ZabbixProblem]:
        previous_problem_external_ids = {problem.external_id for problem in previous_cycle_problems}
        current_problem_external_ids = {problem.external_id for problem in current_cycle_problems}
        resolved_problem_external_ids = previous_problem_external_ids - current_problem_external_ids

        return {problem for problem in previous_cycle_problems if problem.external_id in resolved_problem_external_ids}
