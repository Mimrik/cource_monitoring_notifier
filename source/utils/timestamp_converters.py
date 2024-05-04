"""Module for time utilities."""
import time
from datetime import datetime

import pytz
from sqlalchemy import text


CURRENT_TIMESTAMP_SEC_SQL_CLAUSE = text("EXTRACT(EPOCH FROM NOW())")


def get_current_time_sec() -> int:
    """Get current timestamp in seconds."""
    return int(time.time())


def localize_and_cast_date_title(timestamp: int, timezone_code: str) -> str:
    """Cast timestamp to localized date."""
    timezone = pytz.timezone(timezone_code)
    return datetime.fromtimestamp(timestamp).astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
