from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytz
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.expense import Expense
from app.models.person import Person


def get_offset_ms(tz: str, dt: datetime) -> int:
    """Calculate timezone offset in milliseconds for a given datetime."""
    tz_obj = pytz.timezone(tz)
    utc_dt = dt.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(tz_obj)
    offset = local_dt.utcoffset()
    if offset is None:
        return 0
    return int(offset.total_seconds() * 1000)


def today_in_tz(tz: str) -> str:
    """Returns YYYY-MM-DD string for today in given timezone."""
    tz_obj = pytz.timezone(tz)
    now = datetime.now(tz_obj)
    return now.strftime("%Y-%m-%d")


def local_day_start_utc(date_str: str, tz: str) -> datetime:
    """Converts local date's 00:00:00 to UTC datetime."""
    tz_obj = pytz.timezone(tz)
    local_dt = tz_obj.localize(datetime.strptime(date_str, "%Y-%m-%d"))
    return local_dt.astimezone(timezone.utc)


def local_day_end_utc(date_str: str, tz: str) -> datetime:
    """Converts local date's 23:59:59.999 to UTC datetime."""
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
    """Calculate date range based on period or explicit dates."""
    if start_date and end_date:
        return local_day_start_utc(start_date, tz), local_day_end_utc(end_date, tz)

    if not period:
        return None, None

    today = today_in_tz(tz)
    today_dt = datetime.strptime(today, "%Y-%m-%d")

    if period == "daily":
        return local_day_start_utc(today, tz), local_day_end_utc(today, tz)
    elif period == "weekly":
        weekday = today_dt.weekday()  # Monday = 0
        monday = today_dt - timedelta(days=weekday)
        monday_str = monday.strftime("%Y-%m-%d")
        return local_day_start_utc(monday_str, tz), local_day_end_utc(today, tz)
    elif period == "monthly":
        first_of_month = today_dt.replace(day=1)
        first_str = first_of_month.strftime("%Y-%m-%d")
        return local_day_start_utc(first_str, tz), local_day_end_utc(today, tz)

    return None, None


def parse_date_to_noon_utc(date_str: str) -> datetime:
    """Converts YYYY-MM-DD to noon UTC."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def check_budgets(
    db: Session, person_name: str, tz: str = "America/Bogota"
) -> list[dict]:
    """Check budgets and return alerts for those >= 80% spent."""
    person = db.query(Person).filter(Person.name == person_name).first()
    if not person:
        return []

    budgets = (
        db.query(Budget)
        .filter(Budget.person_id == person.id, Budget.enabled.is_(True))
        .all()
    )

    alerts: list[dict] = []

    for budget in budgets:
        start, end = get_period_range(budget.type, None, None, tz)
        if start is None or end is None:
            continue

        spent_result = (
            db.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.person_id == person.id,
                Expense.date >= start,
                Expense.date <= end,
            )
            .scalar()
        )
        spent = float(spent_result)

        if budget.amount <= 0:
            continue

        percentage = round((spent / budget.amount) * 100)
        if percentage >= 80:
            alerts.append(
                {
                    "type": budget.type,
                    "limit": budget.amount,
                    "spent": spent,
                    "remaining": budget.amount - spent,
                    "percentage": percentage,
                }
            )

    return alerts
