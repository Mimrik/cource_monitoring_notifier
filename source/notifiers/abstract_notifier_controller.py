import abc
from dataclasses import dataclass

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger

from entities.notification_sink import NotificationSink
from monitoring_systems.abstract_monitoring_system_controller import MonitoringEvent


@dataclass
class EventMessageComponents:
    event: MonitoringEvent
    trigger: Trigger
    host: Host
    host_groups: list[HostGroup]
    raised_event_message_id: str | None = None


class AbstractNotifierController(abc.ABC):
    @abc.abstractmethod
    async def notify_event_raised(
        self,
        notification_sink: NotificationSink,
        event_message_components: EventMessageComponents,
    ) -> None:
        pass

    @abc.abstractmethod
    async def notify_event_resolved(
        self,
        notification_sink: NotificationSink,
        event_message_components: EventMessageComponents,
    ) -> None:
        pass
