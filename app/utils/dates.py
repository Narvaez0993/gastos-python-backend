
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytz

def get_offset_ms(tz: str, dt: datetime) -> int:
    tz_obj = pytz.timezone(tz)
    utc_dt = dt.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(tz_obj)
    offset = local_dt.utcoffset()
    if offset is None:
        return 0
    return int(offset.total_seconds() * 1000)

def today_in_tz(tz: str) -> str:
    tz_obj = pytz.timezone(tz)
    now = datetime.now(tz_obj)
    return now.strftime("%Y-%m-%d")

def local_day_start_utc(date_str: str, tz: str) -> datetime:
    tz_obj = pytz.timezone(tz)
    local_dt = tz_obj.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    return local_dt.astimezone(timezone.utc)

def local_day_end_utc(date_str: str, tz: str) -> datetime:
    tz_obj = pytz.timezone(tz)
    local_dt = tz_obj.localize(
        datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=999000
        )
    )
    return local_dt.astimezone(timezone.utc)

def get_period_range(
    period: str | None,
    start_date: str | None,
    end_date: str | None,
    tz: str,
) -> tuple[datetime | None, datetime | None]:
    if start_date and end_date:
        return local_day_start_utc(start_date, tz), local_day_end_utc(end_date, tz)

    if not period:
        return None, None

    today = today_in_tz(tz)
    today_dt = datetime.strptime(today, "%Y-%m-%d")

    if period == "daily":
        return local_day_start_utc(today, tz), local_day_end_utc(today, tz)
    elif period == "weekly":
        weekday = today_dt.weekday()
        monday = today_dt - timedelta(days=weekday)
        sunday = monday + timedelta(days=6)
        return (
            local_day_start_utc(monday.strftime("%Y-%m-%d"), tz),
            local_day_end_utc(sunday.strftime("%Y-%m-%d"), tz),
        )
    elif period == "monthly":
        first_of_month = today_dt.replace(day=1)
        if first_of_month.month == 12:
            next_month = first_of_month.replace(
                year=first_of_month.year + 1, month=1
            )
        else:
            next_month = first_of_month.replace(month=first_of_month.month + 1)
        last_of_month = next_month - timedelta(days=1)
        return (
            local_day_start_utc(first_of_month.strftime("%Y-%m-%d"), tz),
            local_day_end_utc(last_of_month.strftime("%Y-%m-%d"), tz),
        )

    return None, None

def parse_date_to_noon_utc(date_str: str) -> datetime:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
