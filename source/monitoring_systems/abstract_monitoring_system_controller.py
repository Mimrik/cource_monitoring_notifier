import abc
from dataclasses import dataclass

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger


@dataclass
class MonitoringEvent:
    external_id: str
    trigger_id: int
    opdata: str
    occurred_at: int
    resolved_at: int | None = None


class AbstractMonitoringSystemController(abc.ABC):

    name: str
    id: int

    @abc.abstractmethod
    async def get_host_groups(self) -> list[HostGroup]:
        pass

    @abc.abstractmethod
    async def get_host_group_id_to_hosts(self) -> dict[int, list[Host]]:
        pass

    @abc.abstractmethod
    async def get_triggers(self) -> list[Trigger]:
        pass

    @abc.abstractmethod
    async def get_unresolved_events(self) -> list[MonitoringEvent]:
        pass
