from datetime import datetime, timezone, timedelta
from time import time_ns

class DateTimeHelper:

    def offset_to_utc(self, dt: datetime, offset: float) -> datetime:
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc + timedelta(hours=offset)
        
    def offset_datetime(self, dt: datetime, offset: float) -> datetime:
        dt_z = dt.replace(tzinfo=timezone(timedelta(hours=offset)))
        return dt_z + timedelta(hours=offset)
