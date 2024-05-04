"""TelegramRenderer module."""
import datetime
import logging
from enum import StrEnum
from typing import Optional

from aiogram.utils.markdown import text, bold

from notifiers.abstract_notifier_controller import EventMessageComponents
from monitoring_systems.abstract_monitoring_system_controller import MonitoringEvent
from utils.special_symbols import HOST_GROUP_COMBINER, SpecialSymbol, SUBSECTION_INDENT
from utils.timestamp_converters import localize_and_cast_date_title

logger = logging.getLogger(__name__)


class TelegramCommand(StrEnum):
    """TelegramCommand."""

    START = "start"
    HELP = "help"
    GET_CURRENT_PROBLEMS = "currentproblems"
    SUBSCRIPTION_SETTINGS = "subscription"
    TIME_ZONE_SETTING = "timezone"


TELEGRAM_COMMAND_TO_DESCRIPTION: dict[TelegramCommand, str] = {
    TelegramCommand.HELP: "functional description",
    TelegramCommand.GET_CURRENT_PROBLEMS: "detailed dashboard analogue",
    TelegramCommand.SUBSCRIPTION_SETTINGS: "subscription settings",
    TelegramCommand.TIME_ZONE_SETTING: "time zone setting",
}

TELEGRAM_HELP_MESSAGE = text(
    "Emoji to problem severity:\n",
    "ℹ - info\n",
    "😐 - warning\n",
    "🔥 - average\n",
    "👹 - high\n",
    "💀 - disaster\n",
    "✅ - problem resolved.\n",
    "\n",
    "You can mute problem messages.\n",
    "In this case, you won't know about problem resolved.\n\n",
    "Commands:\n",
    f"/{TelegramCommand.GET_CURRENT_PROBLEMS} - "
    f"{TELEGRAM_COMMAND_TO_DESCRIPTION[TelegramCommand.GET_CURRENT_PROBLEMS]}\n",
    f"/{TelegramCommand.SUBSCRIPTION_SETTINGS} - "
    f"{TELEGRAM_COMMAND_TO_DESCRIPTION[TelegramCommand.SUBSCRIPTION_SETTINGS]}\n",
    f"/{TelegramCommand.TIME_ZONE_SETTING} - "
    f"{TELEGRAM_COMMAND_TO_DESCRIPTION[TelegramCommand.TIME_ZONE_SETTING]}\n",
    bold("I need to be promoted to admin to perform all this functionality")
)


class TelegramRenderer:
    """Class for rendering all telegram messages."""

    def __init__(self) -> None:
        """init."""
        self.no_active_problems_answer = "No problems"
        self.no_permission_answer = "You don't have permission for this command"
        self.already_working_in_chat = "I'm already working in this chat"
        self._severity_id_to_emoji = {
            0: "ℹ ",
            1: "ℹ ",
            2: "😐",
            3: "🔥",
            4: "👹",
            5: "💀"
        }
        self._severity_id_to_severity_name = {
            0: "Info",
            1: "Info",
            2: "Warning",
            3: "Average",
            4: "Critical",
            5: "Disaster",
        }
        logger.info(f"{type(self).__name__} inited")

    async def render_event_message_text(
            self,
            event_message_components: EventMessageComponents,
            time_zone_code: str,
    ) -> Optional[str]:
        """Render event message text."""
        emoji = self._severity_id_to_emoji[event_message_components.trigger.severity]
        caption = self._render_caption(event_message_components.event, event_message_components.trigger.severity)
        event_origin = self._render_event_origin(
            trigger_title=event_message_components.trigger.title,
            host_title=event_message_components.host.title,
            host_group_titles=[host_group.title for host_group in event_message_components.host_groups],
            monitoring_system_title="Zabbix",
        )
        timing_answer = self._render_occurred_at(event_message_components.event.occurred_at, time_zone_code)
        message = f"{emoji} {caption}\n{timing_answer}\n{event_origin}\n"
        if event_message_components.event.opdata:
            message += f"{SpecialSymbol.SECTION} Description: {event_message_components.event.opdata}\n"
        message = message.replace("_", "\\_")
        return message

    @staticmethod
    def render_subscription_clarifying_question(monitoring_system_title: str):
        """Render subscription clarifying question text."""
        return f"Are you sure that you want to subscribe to all {monitoring_system_title} triggers? " \
               f"The number of triggers is too large for the average user"

    @staticmethod
    def render_unsubscription_clarifying_question(monitoring_system_title: str) -> str:
        """Render unsubscription clarifying question text."""
        return f"Are you sure that you want to unsubscribe from all {monitoring_system_title} triggers? " \
               f"This action will reset all your subscriptions in this monitoring system"

    @staticmethod
    def _render_event_origin(
            trigger_title: str,
            host_title: str,
            host_group_titles: list[str],
            monitoring_system_title: str
    ) -> str:
        """Render event message origin text."""
        result = f"{SpecialSymbol.SECTION} Source:\n"
        prefix = f"{SUBSECTION_INDENT}{SpecialSymbol.SUBSECTION}"
        result += f"{prefix} Monitoring system: {monitoring_system_title}\n"
        result += f"{prefix} Host groups: {HOST_GROUP_COMBINER.join(host_group_titles)}\n"
        result += f"{prefix} Host: {host_title}\n"
        result += f"{prefix} Trigger: {trigger_title}"
        return result

    def _render_caption(self, event: MonitoringEvent, severity_id: int) -> str:
        """Render event message caption text."""
        return f"{self._severity_id_to_severity_name[severity_id]} event {event.external_id}"

    @staticmethod
    def _render_occurred_at(occurred_at: int, time_zone_code: str) -> str:
        """Render occurred at date text."""
        return f"{SpecialSymbol.SECTION} Occurred at {localize_and_cast_date_title(occurred_at, time_zone_code)}"

    @staticmethod
    def render_resolved_event_caption(event: MonitoringEvent, time_zone_code: str) -> str:
        """Render resolved event caption text."""
        date = localize_and_cast_date_title(event.resolved_at, time_zone_code)
        return f"✅ Event {event.external_id} resolved at {date} " \
               f"(in {datetime.timedelta(seconds=event.resolved_at - event.occurred_at)})"

    @staticmethod
    def render_start_message_text(
            is_group_chat: bool,
            is_admin_promotion_finished: bool = False,
            is_time_zone_chosen: bool = False,
            is_subscription_finished: bool = False,
    ) -> str:
        """Render start message text."""
        message_text = "Greetings!\n" \
                       "I will send you monitoring events.\n\n" \
                       "Before we begin, let's make initial settings:\n"

        time_zone_choose_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_time_zone_chosen \
            else SpecialSymbol.UNFULFILLED_ITEM
        subscription_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_subscription_finished \
            else SpecialSymbol.UNFULFILLED_ITEM

        if is_group_chat:
            admin_promotion_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_admin_promotion_finished \
                else SpecialSymbol.UNFULFILLED_ITEM
            message_text += f"{admin_promotion_item_symbol} Promote me to admin\n"
        message_text += f"{time_zone_choose_item_symbol} Set up time zone\n" \
                        "(you'll be able to change it by /timezone command)\n"
        message_text += f"{subscription_item_symbol} Set up trigger subscriptions\n" \
                        "(you'll be able to change it by /subscription command)\n"

        if is_admin_promotion_finished and is_time_zone_chosen and is_subscription_finished:
            message_text += "\nInitial settings are complete!\nFor functional description you can use /help command"
        return message_text

    @staticmethod
    def render_time_zones_message_text(time_zone_title: str) -> str:
        """Render current user time zone text."""
        return f"Your current time zone is {time_zone_title}"
