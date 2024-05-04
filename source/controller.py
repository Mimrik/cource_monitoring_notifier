"""Controller module."""
import logging
from dataclasses import dataclass

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.trigger import Trigger
from entities.notification_sink import NotificationSink
from entities.notification_sink_to_trigger import NotificationSinkToTrigger
from monitoring_systems.abstract_monitoring_system_controller import AbstractMonitoringSystemController, MonitoringEvent
from notifiers.abstract_notifier_controller import AbstractNotifierController, EventMessageComponents
from outer_resources.database_gateway import DatabaseGateway

logger = logging.getLogger(__name__)


class Controller:
    """Main logic class."""

    @dataclass
    class Context:
        """context."""

        database_gateway: DatabaseGateway
        monitoring_system_controller: AbstractMonitoringSystemController
        notifier_controller: AbstractNotifierController

    def __init__(self, context: Context) -> None:
        """init."""
        self.context = context
        logger.info(f"{type(self).__name__} inited")

    async def handle_monitoring_events(self, events: list[MonitoringEvent]) -> None:
        """Handle current monitoring events sequentially."""
        for event in events:
            try:
                await self._handle_monitoring_event(event)
            except Exception as e:
                logger.error(f"Monitoring event handling failed: {repr(e)}")

    async def get_unresolved_events(self, notification_sink: NotificationSink) -> list[MonitoringEvent]:
        """Get current raised events."""
        unresolved_events = await self.context.monitoring_system_controller.get_unresolved_events()
        trigger_id_to_event = {event.trigger_id: event for event in unresolved_events}
        notification_sink_triggers = await self.context.database_gateway.get_triggers_by_notification_sink_id(
            notification_sink.id
        )
        events = []
        for trigger in notification_sink_triggers:
            if (event := trigger_id_to_event.get(trigger.id)) is not None:
                events.append(event)
        return events

    async def subscribe_to_monitoring_system_triggers(self, recipient_id: str) -> int:
        """Subscribe user to all triggers from monitoring system."""
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)

        actual_triggers = await self.context.monitoring_system_controller.get_triggers()
        saved_triggers = await self.context.database_gateway.get_triggers_by_notification_sink_id(
            notification_sink.id,
        )
        notification_sink_to_triggers = [
            NotificationSinkToTrigger(notification_sink.id, trigger_id)
            for trigger_id in {trigger.id for trigger in actual_triggers} - {trigger.id for trigger in saved_triggers}
        ]
        await self.context.database_gateway.insert(notification_sink_to_triggers)
        return len(notification_sink_to_triggers)

    async def unsubscribe_to_monitoring_system_triggers(self, recipient_id: str) -> None:
        """Unsubscribe user from all monitoring system triggers."""
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        await self.context.database_gateway.delete_notification_sink_to_trigger(notification_sink.id)

    async def _handle_monitoring_event(self, event: MonitoringEvent) -> None:
        """Notify users about monitoring event."""
        logger.debug(f"Handling {event}")
        notification_sinks_to_notify = await self.context.database_gateway.get_notification_sinks_by_trigger_id(
            event.trigger_id,
        )
        if not notification_sinks_to_notify:
            return

        if event.resolved_at is None:
            await self._notify_about_raised_event(notification_sinks_to_notify, event)
        else:
            await self._notify_about_resolved_event(notification_sinks_to_notify, event)

    async def _get_event_message_components(self, event: MonitoringEvent) -> EventMessageComponents:
        """Collect event message components for notifier."""
        trigger = await self.context.database_gateway.get_entity_by_id(Trigger, event.trigger_id)
        host = await self.context.database_gateway.get_entity_by_id(Host, trigger.host_id)
        host_groups = await self.context.database_gateway.get_host_groups_by_host_id(host.id)

        return EventMessageComponents(event=event, trigger=trigger, host=host, host_groups=host_groups)

    async def _notify_about_raised_event(
            self,
            notification_sinks: list[NotificationSink],
            event: MonitoringEvent,
    ) -> None:
        """Notify all users about raised event."""
        event_message_components = await self._get_event_message_components(event)
        for notification_sink in notification_sinks:
            await self.context.notifier_controller.notify_event_raised(notification_sink, event_message_components)

    async def _notify_about_resolved_event(
            self,
            notification_sinks: list[NotificationSink],
            event: MonitoringEvent,
    ) -> None:
        """Notify all users about resolved event."""
        event_message_components = await self._get_event_message_components(event)
        for notification_sink in notification_sinks:
            await self.context.notifier_controller.notify_event_resolved(notification_sink, event_message_components)
