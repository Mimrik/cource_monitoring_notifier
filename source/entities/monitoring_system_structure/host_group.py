from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped

from sqlalchemy_tools.entity_helpers.sqlalchemy_base import sqlalchemy_mapper_registry

from utils.timestamp_converters import CURRENT_TIMESTAMP_SEC_SQL_CLAUSE, get_current_time_sec


@sqlalchemy_mapper_registry.mapped_as_dataclass
class HostGroup:
    __tablename__ = "host_group"

    id: Mapped[int] = mapped_column(primary_key=True, init=True)
    title: Mapped[str] = mapped_column(nullable=False)
    disabled_at: Mapped[int] = mapped_column(nullable=True, default=None)

    created_at: Mapped[int] = mapped_column(
        default_factory=get_current_time_sec,
        server_default=CURRENT_TIMESTAMP_SEC_SQL_CLAUSE,
        nullable=False,
    )


UniqueConstraint(HostGroup.external_id, HostGroup.monitoring_system_id)
