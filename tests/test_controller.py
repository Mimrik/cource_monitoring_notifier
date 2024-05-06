import os
import sys
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "source")))

from controller import Controller
from entities.monitoring_system_structure.trigger import Trigger


class TestController(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.controller = Controller(
            context=Controller.Context(
                monitoring_system_controller=MagicMock(),
                notifier_controller=MagicMock(),
                database_gateway=MagicMock(),
            ),
        )

    async def test_handle_monitoring_event(self) -> None:
        with self.subTest("raised event"):
            self.controller.context.database_gateway.get_notification_sinks_by_trigger_id = AsyncMock(
                return_value=[MagicMock()]
            )
            self.controller._notify_about_raised_event = AsyncMock(return_value=None)
            self.controller._notify_about_resolved_event = AsyncMock(return_value=None)

            await self.controller._handle_monitoring_event(MagicMock(resolved_at=None))

            self.controller.context.database_gateway.get_notification_sinks_by_trigger_id.assert_awaited_once()
            self.controller._notify_about_raised_event.assert_awaited_once()
            self.controller._notify_about_resolved_event.assert_not_awaited()

        with self.subTest("resolved event"):
            self.controller.context.database_gateway.get_notification_sinks_by_trigger_id = AsyncMock(
                return_value=[MagicMock()]
            )
            self.controller._notify_about_raised_event = AsyncMock(return_value=None)
            self.controller._notify_about_resolved_event = AsyncMock(return_value=None)

            await self.controller._handle_monitoring_event(MagicMock(resolved_at=42))

            self.controller.context.database_gateway.get_notification_sinks_by_trigger_id.assert_awaited_once()
            self.controller._notify_about_raised_event.assert_not_awaited()
            self.controller._notify_about_resolved_event.assert_awaited_once()

    async def test_subscribe_to_monitoring_system_triggers(self) -> None:
        with self.subTest("valid"):
            self.controller.context.database_gateway.get_notification_sink = AsyncMock(id=42)
            self.controller.context.monitoring_system_controller.get_triggers = AsyncMock(
                return_value=[
                    Trigger(
                        id=19207,
                        title='/boot: Disk space is low (used > {$VFS.FS.PUSED.MAX.WARN:"/boot"}%)',
                        severity=2,
                        host_id=10417,
                        disabled_at=None,
                        created_at=1111,
                    ),
                    Trigger(
                        id=19208,
                        title='title',
                        severity=2,
                        host_id=10418,
                        disabled_at=None,
                        created_at=1111,
                    )
                ]
            )
            self.controller.context.database_gateway.get_triggers_by_notification_sink_id = AsyncMock(
                return_value=[
                    Trigger(id=19208, title='title', severity=2, host_id=10418, disabled_at=None, created_at=1111)
                ]
            )
            self.controller.context.database_gateway.insert = AsyncMock()

            triggers_len = await self.controller.subscribe_to_monitoring_system_triggers("42")

            self.controller.context.database_gateway.get_notification_sink.assert_awaited_once()
            self.controller.context.monitoring_system_controller.get_triggers.assert_awaited_once()
            self.controller.context.database_gateway.get_triggers_by_notification_sink_id.assert_awaited_once()
            self.controller.context.database_gateway.insert.assert_awaited_once()
            self.assertEqual(triggers_len, 1)
