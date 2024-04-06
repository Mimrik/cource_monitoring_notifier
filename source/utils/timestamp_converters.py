import time
from sqlalchemy import text


CURRENT_TIMESTAMP_SEC_SQL_CLAUSE = text("EXTRACT(EPOCH FROM NOW())")


def get_current_time_sec() -> int:
    return int(time.time())
