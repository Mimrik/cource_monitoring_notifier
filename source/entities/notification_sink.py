"""NotificationSink module."""
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_tools.entity_helpers.fk_keys import RestrictForeignKey
from sqlalchemy_tools.entity_helpers.sqlalchemy_base import sqlalchemy_mapper_registry

from entities.time_zone import TimeZone, time_zone_code_to_time_zone_id
from utils.timestamp_converters import get_current_time_sec, CURRENT_TIMESTAMP_SEC_SQL_CLAUSE


DEFAULT_TIME_ZONE_ID = text(f"{time_zone_code_to_time_zone_id['Etc/GMT']}")


@sqlalchemy_mapper_registry.mapped_as_dataclass
class NotificationSink:
    """NotificationSink (user)."""

    __tablename__ = "notification_sink"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    recipient_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    time_zone_id: Mapped[int] = mapped_column(
        RestrictForeignKey(TimeZone.id),
        default=DEFAULT_TIME_ZONE_ID,
        server_default=DEFAULT_TIME_ZONE_ID,
    )

    created_at: Mapped[int] = mapped_column(
        default_factory=get_current_time_sec,
        server_default=CURRENT_TIMESTAMP_SEC_SQL_CLAUSE,
        nullable=False,
    )
