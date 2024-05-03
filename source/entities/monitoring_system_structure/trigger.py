from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy_tools.entity_helpers.fk_keys import RestrictForeignKey
from sqlalchemy_tools.entity_helpers.sqlalchemy_base import sqlalchemy_mapper_registry

from entities.monitoring_system_structure.host import Host
from utils.timestamp_converters import CURRENT_TIMESTAMP_SEC_SQL_CLAUSE, get_current_time_sec


@sqlalchemy_mapper_registry.mapped_as_dataclass
class Trigger:
    __tablename__ = "trigger"

    id: Mapped[int] = mapped_column(primary_key=True, init=True)
    title: Mapped[str] = mapped_column(nullable=False)
    severity: Mapped[int] = mapped_column(nullable=False)
    host_id: Mapped[int] = mapped_column(RestrictForeignKey(Host.id), nullable=False)
    disabled_at: Mapped[int] = mapped_column(nullable=True, default=None)

    created_at: Mapped[int] = mapped_column(
        default_factory=get_current_time_sec,
        server_default=CURRENT_TIMESTAMP_SEC_SQL_CLAUSE,
        nullable=False,
    )
