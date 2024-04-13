import abc

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger


class AbstractMonitoringSystemController(abc.ABC):

    name: str
    id: int

    @abc.abstractmethod
    async def get_host_groups(self) -> list[HostGroup]:
        pass

    @abc.abstractmethod
    async def get_host_group_id_to_hosts(self) -> dict[str, list[Host]]:
        pass

    @abc.abstractmethod
    async def get_triggers(self) -> list[Trigger]:
        pass
