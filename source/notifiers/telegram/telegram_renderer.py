"""TelegramRenderer module."""
import datetime
import logging
from enum import StrEnum
from typing import Optional

from notifiers.abstract_notifier_controller import EventMessageComponents
from monitoring_systems.abstract_monitoring_system_controller import MonitoringEvent
from utils.special_symbols import HOST_GROUP_COMBINER, SpecialSymbol, SUBSECTION_INDENT
from utils.timestamp_converters import localize_and_cast_date_title
from utils.translation import _, LanguageCode, LanguageTitle

logger = logging.getLogger(__name__)


class TelegramCommand(StrEnum):
    """TelegramCommand."""

    START = "start"
    HELP = "help"
    GET_CURRENT_PROBLEMS = "currentproblems"
    SUBSCRIPTION_SETTINGS = "subscription"
    TIME_ZONE_SETTING = "timezone"


class TelegramRenderer:
    """Class for rendering all telegram messages."""

    def __init__(self) -> None:
        """init."""
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
            language_code: LanguageCode,
    ) -> Optional[str]:
        """Render event message text."""
        emoji = self._severity_id_to_emoji[event_message_components.trigger.severity]
        caption = self._render_caption(
            event_message_components.event, event_message_components.trigger.severity, language_code
        )
        event_origin = self._render_event_origin(
            trigger_title=event_message_components.trigger.title,
            host_title=event_message_components.host.title,
            host_group_titles=[host_group.title for host_group in event_message_components.host_groups],
            monitoring_system_title="Zabbix",
            language_code=language_code,
        )
        timing_answer = self._render_occurred_at(
            event_message_components.event.occurred_at, time_zone_code, language_code
        )
        message = f"{emoji} {caption}\n{timing_answer}\n{event_origin}\n"
        if event_message_components.event.opdata:
            message += _(
                "{} Description: {}\n",
                language_code
            ).format(SpecialSymbol.SECTION, event_message_components.event.opdata)
        message = message.replace("_", "\\_")
        return message

    @staticmethod
    def render_subscription_clarifying_question(monitoring_system_title: str, language_code: LanguageCode) -> str:
        """Render subscription clarifying question text."""
        return _(
            "Are you sure that you want to subscribe to all {} triggers? "
            "The number of triggers is too large for the average user",
            language_code
        ).format(monitoring_system_title)

    @staticmethod
    def render_unsubscription_clarifying_question(monitoring_system_title: str, language_code: LanguageCode) -> str:
        """Render unsubscription clarifying question text."""
        return _(
            "Are you sure that you want to unsubscribe from all {} triggers? "
            "This action will reset all your subscriptions in this monitoring system",
            language_code
        ).format(monitoring_system_title)

    @staticmethod
    def _render_event_origin(
            trigger_title: str,
            host_title: str,
            host_group_titles: list[str],
            monitoring_system_title: str,
            language_code: LanguageCode,
    ) -> str:
        """Render event message origin text."""
        result = _("{} Source:\n", language_code).format(SpecialSymbol.SECTION)
        prefix = f"{SUBSECTION_INDENT}{SpecialSymbol.SUBSECTION}"
        result += _("{} Monitoring system: {}\n", language_code).format(prefix, monitoring_system_title)
        result += _("{} Host groups: {)}\n", language_code).format(prefix, HOST_GROUP_COMBINER.join(host_group_titles))
        result += _("{} Host: {}\n", language_code).format(prefix, host_title)
        result += _("{} Trigger: {}", language_code).format(prefix, trigger_title)
        return result

    def _render_caption(self, event: MonitoringEvent, severity_id: int, language_code: LanguageCode) -> str:
        """Render event message caption text."""
        return _("{} event {}", language_code).format(
            self._severity_id_to_severity_name[severity_id], event.external_id
        )

    @staticmethod
    def _render_occurred_at(occurred_at: int, time_zone_code: str, language_code: LanguageCode) -> str:
        """Render occurred at date text."""
        return _(
            "{} Occurred at {}",
            language_code
        ).format(SpecialSymbol.SECTION, localize_and_cast_date_title(occurred_at, time_zone_code))

    @staticmethod
    def render_resolved_event_caption(event: MonitoringEvent, time_zone_code: str, language_code: LanguageCode) -> str:
        """Render resolved event caption text."""
        date = localize_and_cast_date_title(event.resolved_at, time_zone_code)
        return _(
            "✅ Event {} resolved at {} "
            "(in {})",
            language_code
        ).format(event.external_id, date, datetime.timedelta(seconds=event.resolved_at - event.occurred_at))

    @staticmethod
    def render_start_message_text(
            language_code: LanguageCode,
            is_group_chat: bool,
            is_language_chosen: bool = False,
            is_admin_promotion_finished: bool = False,
            is_time_zone_chosen: bool = False,
            is_subscription_finished: bool = False,
    ) -> str:
        """Render start message text."""
        message_text = _(
            "Greetings!\n"
            "I will send you monitoring events.\n\n"
            "Before we begin, let's make initial settings:\n",
            language_code
        )

        language_choose_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_language_chosen \
            else SpecialSymbol.UNFULFILLED_ITEM
        time_zone_choose_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_time_zone_chosen \
            else SpecialSymbol.UNFULFILLED_ITEM
        subscription_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_subscription_finished \
            else SpecialSymbol.UNFULFILLED_ITEM

        if is_group_chat:
            admin_promotion_item_symbol = SpecialSymbol.COMPLETED_ITEM if is_admin_promotion_finished \
                else SpecialSymbol.UNFULFILLED_ITEM
            message_text += _("{} Promote me to admin\n", language_code).format(admin_promotion_item_symbol)
        message_text += _(
            "{} Choose language\n"
            "(you'll be able to change it by /language command)\n",
            language_code
        ).format(language_choose_item_symbol)
        message_text += _(
            "{} Set up time zone\n"
            "(you'll be able to change it by /timezone command)\n",
            language_code
        ).format(time_zone_choose_item_symbol)
        message_text += _(
            "{} Set up trigger subscriptions\n"
            "(you'll be able to change it by /subscription command)\n",
            language_code
        ).format(subscription_item_symbol)

        if is_admin_promotion_finished and is_time_zone_chosen and is_subscription_finished:
            message_text += _(
                "\nInitial settings are complete!\nFor functional description you can use /help command",
                language_code
            )
        return message_text

    @staticmethod
    def render_time_zones_message_text(time_zone_title: str, language_code: LanguageCode) -> str:
        """Render current user time zone text."""
        return _("Your current time zone is {}", language_code).format(time_zone_title)

    @staticmethod
    def render_languages_message_text(language_title: LanguageTitle, language_code: LanguageCode) -> str:
        """Render current user time zone text."""
        return _("Your current language is {}", language_code).format(language_title)
