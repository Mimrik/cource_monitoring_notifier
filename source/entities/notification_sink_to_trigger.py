from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy_tools.entity_helpers.fk_keys import RestrictForeignKey
from sqlalchemy_tools.entity_helpers.sqlalchemy_base import sqlalchemy_mapper_registry

from entities.monitoring_system_structure.trigger import Trigger
from entities.notification_sink import NotificationSink
from utils.timestamp_converters import CURRENT_TIMESTAMP_SEC_SQL_CLAUSE, get_current_time_sec


@sqlalchemy_mapper_registry.mapped_as_dataclass
class NotificationSinkToTrigger:
    __tablename__ = "notification_sink_to_trigger"

    notification_sink_id: Mapped[int] = mapped_column(RestrictForeignKey(NotificationSink.id), primary_key=True, nullable=False)
    trigger_id: Mapped[int] = mapped_column(RestrictForeignKey(Trigger.id), primary_key=True, nullable=False)

    created_at: Mapped[int] = mapped_column(
        default_factory=get_current_time_sec,
        server_default=CURRENT_TIMESTAMP_SEC_SQL_CLAUSE,
        nullable=False,
    )
