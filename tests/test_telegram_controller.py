from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, AsyncMock

from entities.time_zone import TimeZone
from notifiers.telegram.telegram_controller import TelegramController


class TestTelegramController(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.telegram_controller = TelegramController(
            context=TelegramController.Context(
                controller=MagicMock(),
                telegram_dispatcher=MagicMock(),
                database_gateway=MagicMock(),
                telegram_renderer=MagicMock(),
                telegram_bot=MagicMock(),
                telegram_keyboard_creator=MagicMock(),
            ),
        )

    async def test_notify_event_raised(self) -> None:
        with self.subTest("valid"):
            self.telegram_controller.context.database_gateway.get_notification_sink_time_zone = AsyncMock(
                return_value=TimeZone(code="Etc/GMT-14", title="UTC+14")
            )
            self.telegram_controller.context.telegram_bot.send_message = AsyncMock(return_value=None)
            self.telegram_controller.context.telegram_renderer.render_event_message_text = AsyncMock(
                return_value="text",
            )

            await self.telegram_controller.notify_event_raised(MagicMock(), MagicMock())

            self.telegram_controller.context.database_gateway.get_notification_sink_time_zone.assert_awaited_once()
            self.telegram_controller.context.telegram_bot.send_message.assert_awaited_once()
            self.telegram_controller.context.telegram_renderer.render_event_message_text.assert_awaited_once()

    async def test_subscribe_to_monitoring_system(self) -> None:
        with self.subTest("valid"):
            callback_query = MagicMock(message=MagicMock(chat=MagicMock(id=42)))
            self.telegram_controller.context.controller.subscribe_to_monitoring_system_triggers = AsyncMock(
                return_value=4224
            )
            self.telegram_controller.context.telegram_bot.send_message = AsyncMock()

            await self.telegram_controller._subscribe_to_monitoring_system(callback_query)

            self.telegram_controller.context.controller.subscribe_to_monitoring_system_triggers.assert_awaited_once()
            self.telegram_controller.context.telegram_bot.send_message.assert_awaited_once()
