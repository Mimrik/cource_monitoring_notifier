"""TelegramKeyboardCreator module."""
import logging
from dataclasses import dataclass
from enum import unique, StrEnum
from math import ceil
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from controller import Controller
from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from entities.monitoring_system_structure.trigger import Trigger
from entities.notification_sink import NotificationSink
from entities.time_zone import TimeZone
from outer_resources.database_gateway import DatabaseGateway
from utils.special_symbols import SpecialSymbol
from utils.translation import _, LanguageCode, LanguageTitle

logger = logging.getLogger(__name__)


@unique
class TelegramButtonAction(StrEnum):
    """TelegramButtonAction."""

    MUTE_TRIGGER = "mute_trigger"
    UNMUTE_TRIGGER = "unmute_trigger"

    GET_TRIGGER_LABEL_TYPES = "get_trigger_label_types"
    GET_TRIGGER_LABELS_BY_TYPE = "get_trigger_labels"

    SUBSCRIBE_TRIGGER = "subscribe_trigger"
    SUBSCRIBE_TRIGGERS_WITH_LABEL = "subscribe_label"
    SUBSCRIBE_MONITORING_SYSTEM = "subscribe_monitoring_system"
    PRE_SUBSCRIBE_MONITORING_SYSTEM = "pre_subscribe_monitoring_system"

    SET_TIME_ZONE = "set_time_zone"
    SET_LANGUAGE = "set_language"

    UNSUBSCRIBE_TRIGGER = "unsubscribe_trigger"
    UNSUBSCRIBE_TRIGGERS_WITH_LABEL = "unsubscribe_label"
    UNSUBSCRIBE_MONITORING_SYSTEM = "unsubscribe_monitoring_system"
    PRE_UNSUBSCRIBE_MONITORING_SYSTEM = "pre_unsubscribe_monitoring_system"

    GO_TO_MONITORING_SYSTEMS = "go_to_monitoring_systems"
    GO_TO_HOST_GROUPS = "go_to_host_groups"
    GO_TO_HOSTS = "go_to_hosts"
    GO_TO_TRIGGERS = "go_to_triggers"
    GO_TO_TIME_ZONES = "go_to_time_zones"

    FINISH_SETTING = "finish_setting"

    NO_ACTION = "no_action"


@dataclass(frozen=True)
class TelegramButtonData:
    """TelegramButtonData."""

    action: str
    entity_id: Optional[int | LanguageCode] = None
    mute_code: Optional[str] = None
    page_number: Optional[int] = None
    start_message_id: Optional[int] = None

    def __str__(self):
        """str."""
        return f"{self.action}|" \
               f"{self.entity_id if self.entity_id is not None else ''}|" \
               f"{self.mute_code if self.mute_code is not None else ''}|" \
               f"{self.page_number if self.page_number is not None else ''}|" \
               f"{self.start_message_id if self.start_message_id is not None else ''}"


def cast_button_data(unformed_button_data: str) -> TelegramButtonData:
    """Cast button data."""
    button_data_attributes = unformed_button_data.split("|")
    try:
        entity_id = int(button_data_attributes[1])
    except Exception:
        if isinstance(button_data_attributes[1], str):
            entity_id = button_data_attributes[1]
        else:
            entity_id = None

    return TelegramButtonData(
        action=button_data_attributes[0],
        entity_id=entity_id,
        mute_code=button_data_attributes[2] if button_data_attributes[2] else None,
        page_number=int(button_data_attributes[3]) if button_data_attributes[3] else None,
        start_message_id=int(button_data_attributes[4]) if button_data_attributes[4] else None,
    )


class TelegramKeyboardCreator:
    """Class for creating all telegram keyboards."""

    @dataclass
    class Context:
        """context."""

        controller: Controller
        database_gateway: DatabaseGateway

    MAX_KEYBOARD_HEIGHT = 14

    def __init__(self, context: Context):
        """init."""
        self.context = context

    async def create_monitoring_systems_keyboard(
            self,
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create subscription settings keyboard."""
        inline_keyboard = InlineKeyboardMarkup(row_width=1)
        inline_keyboard.add(
            InlineKeyboardButton(
                text=f"{SpecialSymbol.DOWN_ARROW} Zabbix {SpecialSymbol.DOWN_ARROW}",
                callback_data=str(
                    TelegramButtonData(action=TelegramButtonAction.NO_ACTION, start_message_id=start_message_id)
                ),
            )
        )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("manage subscriptions", language_code),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_HOST_GROUPS,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("subscribe to all triggers", language_code),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.PRE_SUBSCRIBE_MONITORING_SYSTEM,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("unsubscribe from all triggers", language_code),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.PRE_UNSUBSCRIBE_MONITORING_SYSTEM,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(self._create_separator_button(start_message_id))
        inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
        return inline_keyboard

    def create_full_subscription_keyboard(
            self,
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create all triggers subscription keyboard."""
        inline_keyboard = InlineKeyboardMarkup(row_width=1)
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("{} subscribe to all triggers {}", language_code).format(
                    SpecialSymbol.ATTENTION, SpecialSymbol.ATTENTION
                ),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.SUBSCRIBE_MONITORING_SYSTEM,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(self._create_back_to_subscription_settings_button(language_code, start_message_id))
        inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
        return inline_keyboard

    def create_full_unsubscription_keyboard(
            self,
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create all triggers unsubscription keyboard."""
        inline_keyboard = InlineKeyboardMarkup(row_width=1)
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("{} unsubscribe from all triggers {}", language_code).format(
                    SpecialSymbol.ATTENTION, SpecialSymbol.ATTENTION
                ),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.UNSUBSCRIBE_MONITORING_SYSTEM,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(self._create_back_to_subscription_settings_button(language_code, start_message_id))
        inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
        return inline_keyboard

    async def create_host_groups_keyboard(
            self,
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create host groups subscription keyboard."""
        host_groups = await self.context.database_gateway.select(HostGroup)
        inline_keyboard = InlineKeyboardMarkup(row_width=2)
        for host_group in host_groups:
            inline_keyboard.add(
                InlineKeyboardButton(
                    text=f"{host_group.title}",
                    callback_data=str(
                        TelegramButtonData(
                            action=TelegramButtonAction.GO_TO_HOSTS,
                            entity_id=host_group.id,
                            start_message_id=start_message_id,
                        )
                    ),
                ),
            )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("{} Back to monitoring systems", language_code).format(SpecialSymbol.BACK),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_MONITORING_SYSTEMS,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
        return inline_keyboard

    async def create_hosts_keyboard(
            self,
            host_group_id: int,
            page_number: int,
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create hosts subscription keyboard."""
        hosts = await self.context.database_gateway.select(Host)
        sorted_hosts = self._sort_hosts_by_host_titles(hosts)
        pages_amount = ceil(len(hosts) / self.MAX_KEYBOARD_HEIGHT)
        inline_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
        for host in sorted_hosts[page_number * self.MAX_KEYBOARD_HEIGHT: (page_number + 1) * self.MAX_KEYBOARD_HEIGHT]:
            inline_keyboard.add(
                InlineKeyboardButton(
                    text=f"{host.title}",
                    callback_data=str(
                        TelegramButtonData(
                            action=TelegramButtonAction.GO_TO_TRIGGERS,
                            entity_id=host.id,
                            start_message_id=start_message_id,
                        )
                    ),
                )
            )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=f"{SpecialSymbol.LEFT_ARROW}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_HOSTS,
                        entity_id=host_group_id,
                        start_message_id=start_message_id,
                        page_number=page_number - 1 if page_number > 0 else 0,
                    )
                ),

            ),
            InlineKeyboardButton(
                text=f"{page_number + 1 if page_number < pages_amount else pages_amount}/{pages_amount}",
                callback_data=str(
                    TelegramButtonData(action=TelegramButtonAction.NO_ACTION, start_message_id=start_message_id)
                ),
            ),
            InlineKeyboardButton(
                text=f"{SpecialSymbol.RIGHT_ARROW}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_HOSTS,
                        entity_id=host_group_id,
                        start_message_id=start_message_id,
                        page_number=page_number + 1 if page_number + 1 < pages_amount else page_number,
                    )
                ),
            )
        )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("{} Back to host groups", language_code).format(SpecialSymbol.BACK),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_HOST_GROUPS,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
        return inline_keyboard

    async def create_triggers_keyboard(
            self,
            notification_sink: NotificationSink,
            host_id: int,
            page_number: int = 0,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create triggers subscription keyboard."""
        triggers = await self.context.database_gateway.get_triggers_by_host_id(host_id)
        triggers.sort(key=lambda host: host.title)
        pages_amount = ceil(len(triggers) / self.MAX_KEYBOARD_HEIGHT)
        subscribed_triggers = await self.context.database_gateway.get_triggers_by_notification_sink_id(
            notification_sink.id
        )
        subscribed_trigger_ids = {subscribed_trigger.id for subscribed_trigger in subscribed_triggers}
        inline_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
        for trigger in triggers[page_number * self.MAX_KEYBOARD_HEIGHT: (page_number + 1) * self.MAX_KEYBOARD_HEIGHT]:
            inline_keyboard.add(
                self._create_subscribed_trigger_button(
                    trigger=trigger, page_number=page_number, start_message_id=start_message_id
                )
                if trigger.id in subscribed_trigger_ids
                else self._create_unsubscribed_trigger_button(
                    trigger=trigger, page_number=page_number, start_message_id=start_message_id
                )
            )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=f"{SpecialSymbol.LEFT_ARROW}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_TRIGGERS,
                        entity_id=host_id,
                        start_message_id=start_message_id,
                        page_number=page_number - 1 if page_number > 0 else 0,
                    )
                ),
            ),
            InlineKeyboardButton(
                text=f"{page_number + 1 if page_number < pages_amount else pages_amount}/{pages_amount}",
                callback_data=str(
                    TelegramButtonData(action=TelegramButtonAction.NO_ACTION, start_message_id=start_message_id)
                ),
            ),
            InlineKeyboardButton(
                text=f"{SpecialSymbol.RIGHT_ARROW}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_TRIGGERS,
                        entity_id=host_id,
                        start_message_id=start_message_id,
                        page_number=page_number + 1 if page_number + 1 < pages_amount else page_number,
                    )
                ),
            )
        )
        host_groups = await self.context.database_gateway.get_host_groups_by_host_id(host_id)
        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("{} Back to hosts", notification_sink.language_code).format(SpecialSymbol.BACK),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_HOSTS,
                        entity_id=host_groups[0].id,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(self._create_finish_button(notification_sink.language_code, start_message_id))
        return inline_keyboard

    async def create_time_zones_keyboard(
            self,
            language_code: LanguageCode,
            page_number: int = 0,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create time zone change keyboard."""
        time_zones = await self.context.database_gateway.select(TimeZone)
        pages_amount = ceil(len(time_zones) / self.MAX_KEYBOARD_HEIGHT)
        page = time_zones[page_number * self.MAX_KEYBOARD_HEIGHT: (page_number + 1) * self.MAX_KEYBOARD_HEIGHT]
        inline_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
        for time_zone in page:
            inline_keyboard.add(
                InlineKeyboardButton(
                    text=f"{time_zone.title}",
                    callback_data=str(
                        TelegramButtonData(
                            action=TelegramButtonAction.SET_TIME_ZONE,
                            entity_id=time_zone.id,
                            page_number=page_number,
                            start_message_id=start_message_id,
                        )
                    ),
                )
            )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=f"{SpecialSymbol.LEFT_ARROW}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_TIME_ZONES,
                        page_number=page_number - 1 if page_number > 0 else 0,
                        start_message_id=start_message_id,
                    )
                ),
            ),
            InlineKeyboardButton(
                text=f"{page_number + 1 if page_number < pages_amount else pages_amount}/{pages_amount}",
                callback_data=str(TelegramButtonData(action=TelegramButtonAction.NO_ACTION)),
            ),
            InlineKeyboardButton(
                text=f"{SpecialSymbol.RIGHT_ARROW}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_TIME_ZONES,
                        page_number=page_number + 1 if page_number + 1 < pages_amount else page_number,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        if start_message_id is None:
            inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
            return inline_keyboard

        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("next setting", language_code),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_MONITORING_SYSTEMS,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        return inline_keyboard

    async def create_languages_keyboard(
            self,
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardMarkup:
        """Create language change keyboard."""
        inline_keyboard = InlineKeyboardMarkup(resize_keyboard=True)
        inline_keyboard.add(
            InlineKeyboardButton(
                text=f"{LanguageTitle.EN}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.SET_LANGUAGE,
                        entity_id=LanguageCode.EN,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        inline_keyboard.add(
            InlineKeyboardButton(
                text=f"{LanguageTitle.RU}",
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.SET_LANGUAGE,
                        entity_id=LanguageCode.RU,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        if start_message_id is None:
            inline_keyboard.add(self._create_finish_button(language_code, start_message_id))
            return inline_keyboard

        inline_keyboard.add(
            InlineKeyboardButton(
                text=_("next setting", language_code),
                callback_data=str(
                    TelegramButtonData(
                        action=TelegramButtonAction.GO_TO_TIME_ZONES,
                        start_message_id=start_message_id,
                    )
                ),
            )
        )
        return inline_keyboard

    def _sort_hosts_by_host_titles(self, hosts: list[Host]) -> list[Host]:
        """Sort hosts for hosts keyboard."""
        host_title_to_host = {host.title: host for host in hosts}
        host_titles = set(host_title_to_host)
        not_ip_address_host_titles = {host_title for host_title in host_titles
                                      if not self._is_str_ip_address(host_title)}
        sorted_hosts = [host_title_to_host[host_title] for host_title in not_ip_address_host_titles]
        sorted_hosts.sort(key=lambda host: host.title)

        ip_address_host_titles = host_titles - not_ip_address_host_titles
        ip_address_hosts = [host_title_to_host[host_title] for host_title in ip_address_host_titles]
        ip_address_hosts.sort(key=lambda host: self._cast_ip_address_value(host.title))
        sorted_hosts += ip_address_hosts

        return sorted_hosts

    @staticmethod
    def _cast_ip_address_value(ip_address: str) -> int:
        """Cast ip address value for hosts sorting."""
        unformed_left_values = list(map(int, ip_address.split(":")[0].split(".")))
        first = unformed_left_values[0] * 256 ** 3
        second = unformed_left_values[1] * 256 ** 2
        third = unformed_left_values[2] * 256 ** 1 + unformed_left_values[3]
        return first + second + third

    @staticmethod
    def _is_str_ip_address(string_to_check: str) -> bool:
        """Check is sting is ip address like 0.0.0.0:0000."""
        if string_to_check.count(".") == 3 and string_to_check.count(":") == 1:
            return True
        return False

    @staticmethod
    def _create_unsubscribed_trigger_button(
            trigger: Trigger,
            page_number: int,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardButton:
        """Create unsubscribed trigger button."""
        return InlineKeyboardButton(
            text=f"{SpecialSymbol.UNSUBSCRIBED} {trigger.title}",
            callback_data=str(
                TelegramButtonData(
                    action=TelegramButtonAction.SUBSCRIBE_TRIGGER,
                    entity_id=trigger.id,
                    page_number=page_number,
                    start_message_id=start_message_id,
                )
            ),
        )

    @staticmethod
    def _create_subscribed_trigger_button(
            trigger: Trigger,
            page_number: int,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardButton:
        """Create subscribed trigger button."""
        return InlineKeyboardButton(
            text=f"{SpecialSymbol.SUBSCRIBED} {trigger.title}",
            callback_data=str(
                TelegramButtonData(
                    action=TelegramButtonAction.UNSUBSCRIBE_TRIGGER,
                    entity_id=trigger.id,
                    page_number=page_number,
                    start_message_id=start_message_id,
                )
            ),

        )

    @staticmethod
    def _create_finish_button(
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardButton:
        """Create finish button."""
        return InlineKeyboardButton(
            text=_("{} Finish {}", language_code).format(SpecialSymbol.FINISH, SpecialSymbol.FINISH),
            callback_data=str(
                TelegramButtonData(action=TelegramButtonAction.FINISH_SETTING, start_message_id=start_message_id)
            ),
        )

    @staticmethod
    def _create_separator_button(start_message_id: Optional[int] = None) -> InlineKeyboardButton:
        """Create empty button for separation."""
        return InlineKeyboardButton(
            text="➖",
            callback_data=str(
                TelegramButtonData(action=TelegramButtonAction.NO_ACTION, start_message_id=start_message_id)
            ),
        )

    @staticmethod
    def _create_back_to_subscription_settings_button(
            language_code: LanguageCode,
            start_message_id: Optional[int] = None,
    ) -> InlineKeyboardButton:
        """Create return button."""
        return InlineKeyboardButton(
            text=_("{} Back to subscription settings", language_code).format(SpecialSymbol.BACK),
            callback_data=str(
                TelegramButtonData(
                    action=TelegramButtonAction.GO_TO_MONITORING_SYSTEMS,
                    start_message_id=start_message_id,
                )
            ),
        )
