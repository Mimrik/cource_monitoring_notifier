"""AbstractMonitoringSystemController module."""
import abc
from dataclasses import dataclass

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger


@dataclass
class MonitoringEvent:
    """MonitoringEvent."""

    external_id: str
    trigger_id: int
    opdata: str
    occurred_at: int
    resolved_at: int | None = None


class AbstractMonitoringSystemController(abc.ABC):
    """Monitoring system skeleton for Controller."""

    name: str
    id: int

    @abc.abstractmethod
    async def get_host_groups(self) -> list[HostGroup]:
        """Get actual monitoring system host groups."""
        pass

    @abc.abstractmethod
    async def get_host_group_id_to_hosts(self) -> dict[int, list[Host]]:
        """Get actual monitoring system host groups and hosts."""
        pass

    @abc.abstractmethod
    async def get_triggers(self) -> list[Trigger]:
        """Get actual monitoring system triggers."""
        pass

    @abc.abstractmethod
    async def get_unresolved_events(self) -> list[MonitoringEvent]:
        """Get actual monitoring system unresolved events."""
        pass
