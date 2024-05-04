"""Special symbols for telegram."""
from enum import StrEnum


class SpecialSymbol(StrEnum):
    """Special symbols for telegram."""

    SECTION = "🔸"
    SUBSECTION = "🔹"
    SUBSCRIBED = "✅"
    UNSUBSCRIBED = "🛑"
    UNFULFILLED_ITEM = "🔻"
    COMPLETED_ITEM = "✅"
    ATTENTION = "❗️"
    BACK = "↩️"
    DOWN_ARROW = "⬇️"
    LEFT_ARROW = "⬅️"
    RIGHT_ARROW = "➡️"
    FINISH = "🏁"


SUBSECTION_INDENT = " " * 3
HOST_GROUP_COMBINER = " | "
