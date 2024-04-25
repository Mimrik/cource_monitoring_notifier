import asyncio
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Awaitable
from aiogram.types import CallbackQuery, Message, BotCommand
from async_tools import AsyncInitable
from aiogram.types import ParseMode

from controller import Controller
from monitoring_systems.abstract_monitoring_system_controller import MonitoringEvent
from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger
from entities.notification_sink import NotificationSink
from entities.notification_sink_to_trigger import NotificationSinkToTrigger
from notifiers.abstract_notifier_controller import AbstractNotifierController, EventMessageComponents
from notifiers.telegram.telegram_bot import TelegramBot
from notifiers.telegram.telegram_dispatcher import TelegramDispatcher
from notifiers.telegram.telegram_keyboard_creator import TelegramButtonAction, cast_button_data, TelegramButtonData, \
    TelegramKeyboardCreator
from notifiers.telegram.telegram_renderer import TELEGRAM_COMMAND_TO_DESCRIPTION, TelegramRenderer, \
    TELEGRAM_HELP_MESSAGE
from outer_resources.database_gateway import DatabaseGateway
from utils.special_symbols import SpecialSymbol

logger = logging.getLogger(__name__)


class TelegramCommand(StrEnum):
    START = "start"
    HELP = "help"
    GET_CURRENT_PROBLEMS = "currentproblems"
    SUBSCRIPTION_SETTINGS = "subscription"
    TIME_ZONE_SETTING = "timezone"


class TelegramController(AbstractNotifierController, AsyncInitable):
    @dataclass
    class Context:
        controller: Controller
        telegram_dispatcher: TelegramDispatcher
        database_gateway: DatabaseGateway
        telegram_renderer: TelegramRenderer
        telegram_bot: TelegramBot
        telegram_keyboard_creator: TelegramKeyboardCreator

    MAX_MESSAGE_LENGTH = 4096

    def __init__(self, context: Context) -> None:
        AsyncInitable.__init__(self)
        self.title = "Telegram"
        self.context = context
        self._button_action_to_handler: dict[TelegramButtonAction, Callable[[CallbackQuery], Awaitable[None]]] = {
            TelegramButtonAction.SUBSCRIBE_TRIGGER: self._subscribe_to_trigger,
            TelegramButtonAction.PRE_SUBSCRIBE_MONITORING_SYSTEM: self._pre_subscribe_to_monitoring_system,
            TelegramButtonAction.SUBSCRIBE_MONITORING_SYSTEM: self._subscribe_to_monitoring_system,
            TelegramButtonAction.PRE_UNSUBSCRIBE_MONITORING_SYSTEM: self._pre_unsubscribe_to_monitoring_system,
            TelegramButtonAction.UNSUBSCRIBE_MONITORING_SYSTEM: self._unsubscribe_from_monitoring_system,
            TelegramButtonAction.UNSUBSCRIBE_TRIGGER: self._unsubscribe_from_trigger,
            TelegramButtonAction.GO_TO_MONITORING_SYSTEMS: self._process_settings,
            TelegramButtonAction.GO_TO_HOST_GROUPS: self._process_host_group_choosing,
            TelegramButtonAction.GO_TO_HOSTS: self._process_host_choosing,
            TelegramButtonAction.GO_TO_TRIGGERS: self._process_trigger_choosing,
            TelegramButtonAction.GO_TO_TIME_ZONES: self._process_time_zone_choosing,
            TelegramButtonAction.SET_TIME_ZONE: self._set_time_zone,
            TelegramButtonAction.FINISH_SETTING: self._finish_settings,
            TelegramButtonAction.NO_ACTION: self._no_action_button_handler,
        }
        self.context.telegram_dispatcher.register_callback_query_handler(self._handle_button_press)
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_start_command, commands=[TelegramCommand.START]
        )
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_help_command, commands=[TelegramCommand.HELP]
        )
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_get_current_problems_command, commands=[TelegramCommand.GET_CURRENT_PROBLEMS]
        )
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_subscription_command, commands=[TelegramCommand.SUBSCRIPTION_SETTINGS]
        )
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_time_zone_command, commands=[TelegramCommand.TIME_ZONE_SETTING]
        )
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_new_chat_members, content_types=['new_chat_members']
        )
        self.context.telegram_dispatcher.register_message_handler(
            self._handle_kicked_from_chat, content_types=['left_chat_member']
        )
        logger.info(f"{type(self).__name__} inited")

    async def _async_init(self) -> None:
        await self._set_default_commands()

    async def notify_event_raised(
            self,
            notification_sink: NotificationSink,
            event_message_components: EventMessageComponents,
    ) -> None:
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)
        message_text = await self.context.telegram_renderer.render_event_message_text(
            event_message_components, time_zone.code,
        )
        try:
            await self.context.telegram_bot.send_message(
                chat_id=notification_sink.recipient_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as error:
            logger.error(f"Message not sent: {error}")

    async def notify_event_resolved(self,
                                    notification_sink: NotificationSink,
                                    event_message_components: EventMessageComponents,
                                    ) -> None:
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)

        await self.context.telegram_bot.send_message(
            text=self.context.telegram_renderer.render_resolved_event_caption(
                event_message_components.event, time_zone.code,
            ),
            chat_id=notification_sink.recipient_id,
        )

    # Telegram commands

    async def _handle_start_command(self, message: Message) -> None:
        notification_sink = await self.context.database_gateway.get_notification_sink(str(message.chat.id))
        if notification_sink is not None:
            await message.answer(self.context.telegram_renderer.already_working_in_chat)
            return

        message = await self.context.telegram_bot.send_message(
            chat_id=message.chat.id,
            text=self.context.telegram_renderer.render_start_message_text(
                is_group_chat=self._check_is_group_chat(message.chat.id)
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        if self._check_is_group_chat(message.chat.id):
            while not await self.context.telegram_bot.check_is_bot_administrator(message.chat.id):
                await asyncio.sleep(2)

            await self.context.telegram_bot.edit_message_text(
                message_id=message.message_id,
                chat_id=message.chat.id,
                text=self.context.telegram_renderer.render_start_message_text(
                    is_group_chat=self._check_is_group_chat(message.chat.id),
                    is_admin_promotion_finished=True,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        notification_sink = NotificationSink(recipient_id=str(message.chat.id))
        await self.context.database_gateway.insert(notification_sink)
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)
        await self.context.telegram_bot.send_message(
            chat_id=message.chat.id,
            text=self.context.telegram_renderer.render_time_zones_message_text(time_zone.title),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=await self.context.telegram_keyboard_creator.create_time_zones_keyboard(
                start_message_id=message.message_id
            ),
        )

    @staticmethod
    async def _handle_help_command(message: Message) -> None:
        await message.answer(TELEGRAM_HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN)

    async def _handle_get_current_problems_command(self, message: Message) -> None:
        chat_id: str = str(message.chat.id)
        notification_sink = await self.context.database_gateway.get_notification_sink(chat_id)
        unresolved_events = await self.context.controller.get_unresolved_events(notification_sink)
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)
        answer = await self._create_unresolved_events_answer(unresolved_events, time_zone.code)
        await self._send_current_problems_answer(chat_id, answer)

    async def _handle_subscription_command(self, message: Message) -> None:
        keyboard = await self.context.telegram_keyboard_creator.create_monitoring_systems_keyboard()
        await message.answer(text="Subscription settings", reply_markup=keyboard)

    async def _handle_time_zone_command(self, message: Message) -> None:
        notification_sink = await self.context.database_gateway.get_notification_sink(str(message.chat.id))
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)
        await message.answer(
            text=self.context.telegram_renderer.render_time_zones_message_text(time_zone.title),
            reply_markup=await self.context.telegram_keyboard_creator.create_time_zones_keyboard(),
        )

    # Button press handlers:

    async def _handle_button_press(self, callback_query: CallbackQuery) -> None:
        button_data = cast_button_data(callback_query.data)
        action = TelegramButtonAction(button_data.action)
        await self._button_action_to_handler[action](callback_query)
        await self.context.telegram_bot.answer_callback_query(callback_query.id)

    @staticmethod
    async def _no_action_button_handler(_: CallbackQuery) -> None:
        pass

    async def _finish_settings(self, callback_query: CallbackQuery) -> None:
        button_data = cast_button_data(callback_query.data)
        if button_data.start_message_id is not None:
            await self.context.telegram_bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=button_data.start_message_id,
                text=self.context.telegram_renderer.render_start_message_text(
                    is_group_chat=self._check_is_group_chat(callback_query.message.chat.id),
                    is_admin_promotion_finished=True,
                    is_time_zone_chosen=True,
                    is_subscription_finished=True,
                ),
            )
        await self.context.telegram_bot.delete_message(
            chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id
        )

    async def _process_host_group_choosing(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        button_data = cast_button_data(callback_query.data)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        await self.context.telegram_bot.edit_message_text(
            chat_id=notification_sink.recipient_id,
            message_id=callback_query.message.message_id,
            text=f"{SpecialSymbol.SUBSECTION} Monitoring system: Zabbix\n\n"
                 f"Available host groups:",
            reply_markup=await self.context.telegram_keyboard_creator.create_host_groups_keyboard(
                start_message_id=button_data.start_message_id,
            )
        )

    async def _process_host_choosing(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        button_data = cast_button_data(callback_query.data)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        host_group = await self.context.database_gateway.get_entity_by_id(HostGroup, button_data.entity_id)

        await self.context.telegram_bot.edit_message_text(
            chat_id=notification_sink.recipient_id,
            message_id=callback_query.message.message_id,
            text=f"{SpecialSymbol.SUBSECTION} Monitoring system: Zabbix\n"
                 f"{SpecialSymbol.SUBSECTION} Host group: {host_group.title}\n\n"
                 f"Available hosts:",
            reply_markup=await self.context.telegram_keyboard_creator.create_hosts_keyboard(
                host_group_id=button_data.entity_id,
                page_number=button_data.page_number if button_data.page_number else 0,
                start_message_id=button_data.start_message_id,
            ),
        )

    async def _process_trigger_choosing(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        button_data = cast_button_data(callback_query.data)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        host = await self.context.database_gateway.get_entity_by_id(Host, button_data.entity_id)
        host_groups = await self.context.database_gateway.get_host_groups_by_host_id(host.id)
        await self.context.telegram_bot.edit_message_text(
            chat_id=notification_sink.recipient_id,
            message_id=callback_query.message.message_id,
            text=f"{SpecialSymbol.SUBSECTION} Monitoring system: Zabbix\n"
                 f"{SpecialSymbol.SUBSECTION} Host group: "
                 f"{' | '.join([host_group.title for host_group in host_groups])}\n"
                 f"{SpecialSymbol.SUBSECTION} Host: {host.title}\n\n"
                 f"Available triggers:",
            reply_markup=await self.context.telegram_keyboard_creator.create_triggers_keyboard(
                notification_sink=notification_sink,
                host_id=button_data.entity_id,
                page_number=button_data.page_number if button_data.page_number else 0,
                start_message_id=button_data.start_message_id,
            )
        )

    async def _process_time_zone_choosing(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        button_data = cast_button_data(callback_query.data)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)
        await self.context.telegram_bot.edit_message_text(
            chat_id=recipient_id,
            message_id=callback_query.message.message_id,
            text=self.context.telegram_renderer.render_time_zones_message_text(time_zone.title),
            reply_markup=await self.context.telegram_keyboard_creator.create_time_zones_keyboard(
                page_number=button_data.page_number, start_message_id=button_data.start_message_id
            ),
        )

    async def _process_settings(self, callback_query: CallbackQuery) -> None:
        button_data = cast_button_data(callback_query.data)
        if button_data.start_message_id:
            await self.context.telegram_bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=button_data.start_message_id,
                text=self.context.telegram_renderer.render_start_message_text(
                    is_group_chat=self._check_is_group_chat(callback_query.message.chat.id),
                    is_admin_promotion_finished=True, is_time_zone_chosen=True,
                ),
            )
        await self.context.telegram_bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="Subscription settings",
            reply_markup=await self.context.telegram_keyboard_creator.create_monitoring_systems_keyboard(
                start_message_id=button_data.start_message_id
            )
        )

    # Other handlers:

    async def _handle_new_chat_members(self, message: Message):
        telegram_bot_id = (await self.context.telegram_bot.get_me()).id
        for chat_member in message.new_chat_members:
            if chat_member.id == telegram_bot_id:
                await self._handle_start_command(message)
                break

    async def _handle_kicked_from_chat(self, message: Message):
        telegram_bot_id = (await self.context.telegram_bot.get_me()).id
        if message.left_chat_member.id == telegram_bot_id:
            chat_id = str(message.chat.id)
            notification_sink = await self.context.database_gateway.get_notification_sink(chat_id)
            await self.context.controller.process_delete_notification_sink_usages(notification_sink)
            logger.info(f"Bot kicked from {notification_sink}")

    async def _create_unresolved_events_answer(
            self,
            events: list[MonitoringEvent],
            time_zone_code: str,
    ) -> str:
        if not events:
            return self.context.telegram_renderer.no_active_problems_answer
        answer = "Current problems:\n\n"
        for event in events:
            trigger = await self.context.database_gateway.get_entity_by_id(Trigger, event.trigger_id)
            host = await self.context.database_gateway.get_entity_by_id(Host, trigger.host_id)
            host_groups = await self.context.database_gateway.get_host_groups_by_host_id(host.id)
            event_message: str = await self.context.telegram_renderer.render_event_message_text(
                EventMessageComponents(
                    event=event,
                    trigger=trigger,
                    host=host,
                    host_groups=host_groups,
                ),
                time_zone_code,
            )
            answer += f"{event_message}\n"
        answer = answer.replace("_", "\_")
        return answer

    async def _send_current_problems_answer(self, chat_id: str, answer: str) -> None:
        if len(answer) > self.MAX_MESSAGE_LENGTH:
            event_messages = answer.split("\n\n")
            answer_part: str = ""
            for event_message in event_messages:
                if len(answer_part) + len(event_message) + len("\n\n") > self.MAX_MESSAGE_LENGTH:
                    await self.context.telegram_bot.send_message(
                        chat_id=chat_id,
                        text=answer_part,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    answer_part = ""
                answer_part += event_message + "\n\n"
        else:
            await self.context.telegram_bot.send_message(chat_id, answer, parse_mode=ParseMode.MARKDOWN)

    # utilities:

    async def _set_default_commands(self) -> None:
        bot_commands: list[BotCommand] = []
        for command, description in TELEGRAM_COMMAND_TO_DESCRIPTION.items():
            bot_commands.append(BotCommand(command=command, description=description))
        await self.context.telegram_dispatcher.bot.set_my_commands(bot_commands)

    # database utilities:

    async def _set_time_zone(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        button_data = cast_button_data(callback_query.data)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        await self.context.database_gateway.update_notification_sink_time_zone_id(
            notification_sink_id=notification_sink.id,
            time_zone_id=button_data.entity_id,
        )
        time_zone = await self.context.database_gateway.get_notification_sink_time_zone(notification_sink.id)
        await self.context.telegram_bot.edit_message_text(
            chat_id=recipient_id,
            message_id=callback_query.message.message_id,
            text=self.context.telegram_renderer.render_time_zones_message_text(time_zone.title),
            reply_markup=await self.context.telegram_keyboard_creator.create_time_zones_keyboard(
                page_number=button_data.page_number, start_message_id=button_data.start_message_id
            ),
        )

    async def update_triggers_message(self,
                                      notification_sink: NotificationSink,
                                      button_data: TelegramButtonData,
                                      message_id: str
                                      ) -> None:
        host_id = await self.context.database_gateway.get_host_id_by_trigger_id(button_data.entity_id)
        triggers_keyboard = await self.context.telegram_keyboard_creator.create_triggers_keyboard(
            notification_sink=notification_sink,
            host_id=host_id,
            page_number=button_data.page_number,
            start_message_id=button_data.start_message_id,
        )
        await self.context.telegram_bot.edit_message_reply_markup(
            chat_id=notification_sink.recipient_id,
            message_id=int(message_id),
            reply_markup=triggers_keyboard,
        )

    # insert

    async def _subscribe_to_trigger(self, callback_query: CallbackQuery) -> None:
        message_id = str(callback_query.message.message_id)
        recipient_id = str(callback_query.message.chat.id)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        button_data = cast_button_data(callback_query.data)
        await self.context.database_gateway.insert(
            NotificationSinkToTrigger(trigger_id=button_data.entity_id, notification_sink_id=notification_sink.id)
        )
        await self.update_triggers_message(notification_sink, button_data, message_id)

    async def _pre_subscribe_to_monitoring_system(self, callback_query: CallbackQuery) -> None:
        button_data = cast_button_data(callback_query.data)
        await self.context.telegram_bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=self.context.telegram_renderer.render_subscription_clarifying_question("Zabbix"),
            reply_markup=self.context.telegram_keyboard_creator.create_full_subscription_keyboard(
                monitoring_system_id=button_data.entity_id,
                start_message_id=button_data.start_message_id,
            )
        )

    async def _pre_unsubscribe_to_monitoring_system(self, callback_query: CallbackQuery) -> None:
        button_data = cast_button_data(callback_query.data)
        await self.context.telegram_bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=self.context.telegram_renderer.render_unsubscription_clarifying_question("Zabbix"),
            reply_markup=self.context.telegram_keyboard_creator.create_full_unsubscription_keyboard(
                monitoring_system_id=button_data.entity_id,
                start_message_id=button_data.start_message_id,
            )
        )

    async def _subscribe_to_monitoring_system(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        triggers_len = await self.context.controller.subscribe_to_monitoring_system_triggers(recipient_id)
        await self.context.telegram_bot.send_message(
            chat_id=recipient_id,
            text=f"subscribed to {triggers_len} Zabbix triggers",
        )

    async def _unsubscribe_from_monitoring_system(self, callback_query: CallbackQuery) -> None:
        recipient_id = str(callback_query.message.chat.id)
        await self.context.controller.unsubscribe_to_monitoring_system_triggers(recipient_id)
        await self.context.telegram_bot.send_message(
            chat_id=recipient_id,
            text=f"unsubscribed from all Zabbix triggers",
        )

    # delete:

    async def _unsubscribe_from_trigger(self, callback_query: CallbackQuery) -> None:
        message_id = str(callback_query.message.message_id)
        recipient_id = str(callback_query.message.chat.id)
        notification_sink = await self.context.database_gateway.get_notification_sink(recipient_id)
        button_data = cast_button_data(callback_query.data)
        await self.context.database_gateway.delete_notification_sink_to_trigger_by_id(
            notification_sink_id=notification_sink.id,
            trigger_id=button_data.entity_id,
        )
        await self.update_triggers_message(notification_sink, button_data, message_id)

    @staticmethod
    def _check_is_group_chat(chat_id: int) -> bool:
        return chat_id < 0
