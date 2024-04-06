from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy_tools.entity_helpers.fk_keys import RestrictForeignKey

from sqlalchemy_tools.entity_helpers.sqlalchemy_base import sqlalchemy_mapper_registry

from entities.monitoring_system_structure.host import Host
from entities.monitoring_system_structure.host_group import HostGroup
from utils.timestamp_converters import CURRENT_TIMESTAMP_SEC_SQL_CLAUSE, get_current_time_sec


@sqlalchemy_mapper_registry.mapped_as_dataclass
class HostToHostGroup:
    __tablename__ = "host_to_host_group"

    host_id: Mapped[int] = mapped_column(
        RestrictForeignKey(Host.id),
        composite_primary_key=True,
        nullable=False
    )
    host_group_id: Mapped[int] = mapped_column(
        RestrictForeignKey(HostGroup.id),
        composite_primary_key=True,
        nullable=False
    )

    created_at: Mapped[int] = mapped_column(
        default_factory=get_current_time_sec,
        server_default=CURRENT_TIMESTAMP_SEC_SQL_CLAUSE,
        nullable=False,
    )
