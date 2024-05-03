from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_tools.entity_helpers.setter import set_ids
from sqlalchemy_tools.entity_helpers.sqlalchemy_base import sqlalchemy_mapper_registry, register_initial_values


from utils.timestamp_converters import CURRENT_TIMESTAMP_SEC_SQL_CLAUSE, get_current_time_sec


@sqlalchemy_mapper_registry.mapped_as_dataclass
class TimeZone:
    __tablename__ = "time_zone"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    code: Mapped[str] = mapped_column(nullable=False, unique=True)
    title: Mapped[str] = mapped_column(nullable=False, unique=True)

    created_at: Mapped[int] = mapped_column(
        default_factory=get_current_time_sec,
        server_default=CURRENT_TIMESTAMP_SEC_SQL_CLAUSE,
        nullable=False,
    )


time_zone_code_to_title = {
    "Etc/GMT-14": "UTC+14",
    "Etc/GMT-13": "UTC+13",
    "Etc/GMT-12": "UTC+12",
    "Etc/GMT-11": "UTC+11",
    "Etc/GMT-10": "UTC+10",
    "Etc/GMT-9": "UTC+9",
    "Etc/GMT-8": "UTC+8",
    "Etc/GMT-7": "UTC+7",
    "Etc/GMT-6": "UTC+6",
    "Etc/GMT-5": "UTC+5",
    "Etc/GMT-4": "UTC+4",
    "Etc/GMT-3": "UTC+3",
    "Etc/GMT-2": "UTC+2",
    "Etc/GMT-1": "UTC+1",
    "Etc/GMT": "UTC",
    "Etc/GMT+1": "UTC-1",
    "Etc/GMT+2": "UTC-2",
    "Etc/GMT+3": "UTC-3",
    "Etc/GMT+4": "UTC-4",
    "Etc/GMT+5": "UTC-5",
    "Etc/GMT+6": "UTC-6",
    "Etc/GMT+7": "UTC-7",
    "Etc/GMT+8": "UTC-8",
    "Etc/GMT+9": "UTC-9",
    "Etc/GMT+10": "UTC-10",
    "Etc/GMT+11": "UTC-11",
    "Etc/GMT+12": "UTC-12",
}

time_zones = [TimeZone(code=time_zone_code, title=time_zone_title)
              for time_zone_code, time_zone_title in time_zone_code_to_title.items()]

set_ids(*time_zones)

register_initial_values(
    sqlalchemy_mapper_registry,
    *time_zones
)

time_zone_id_to_time_zone_title = {time_zone.id: time_zone.title for time_zone in time_zones}
time_zone_id_to_time_zone_code = {time_zone.id: time_zone.code for time_zone in time_zones}
time_zone_code_to_time_zone_id = {time_zone.code: time_zone.id for time_zone in time_zones}
