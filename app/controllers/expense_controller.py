from __future__ import annotations

import os
import time
import random
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.expense_image import ExpenseImage
from app.models.money_source import MoneySource
from app.models.money_source_movement import MoneySourceMovement
from app.models.person import Person
from app.utils.budget_check import (
    check_budgets,
    get_period_range,
    parse_date_to_noon_utc,
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def resolve_tz(tz_query: str | None, tz_header: str | None) -> str:
    return tz_query or tz_header or "America/Bogota"


async def create_expense(
    db: Session,
    person_name: str,
    amount: float,
    description: str,
    date_str: str,
    category: str | None = None,
    money_source_id: int | None = None,
    money_source_name: str | None = None,
    images: list[UploadFile] | None = None,
    tz: str = "America/Bogota",
) -> dict:
    if not person_name or not amount or not description or not date_str:
        raise HTTPException(
            status_code=400,
            detail="personName, amount, description, and date are required",
        )

    person = db.query(Person).filter(Person.name == person_name).first()
    if not person:
        raise HTTPException(
            status_code=404, detail=f'Person "{person_name}" not found'
        )

    source: MoneySource | None = None
    if money_source_id:
        source = (
            db.query(MoneySource)
            .filter(
                MoneySource.id == money_source_id,
                MoneySource.person_id == person.id,
            )
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Money source not found")
    elif money_source_name:
        normalized = money_source_name.lower().strip()
        source = (
            db.query(MoneySource)
            .filter(
                MoneySource.person_id == person.id,
                MoneySource.name_normalized == normalized,
            )
            .first()
        )
        if not source:
            raise HTTPException(
                status_code=404,
                detail=f'Money source "{money_source_name}" not found for this person',
            )

    if source and not source.enabled:
        raise HTTPException(
            status_code=400, detail=f'Money source "{source.name}" is disabled'
        )

    saved_filenames: list[str] = []
    if images:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for img in images[:10]:
            if img.filename:
                ext = img.filename.rsplit(".", 1)[-1].lower() if "." in img.filename else ""
                if ext not in ALLOWED_EXTENSIONS:
                    continue
                content = await img.read()
                if len(content) > MAX_FILE_SIZE:
                    continue
                filename = f"{int(time.time() * 1000)}-{random.randint(100000000, 999999999)}.{ext}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(content)
                saved_filenames.append(filename)

    expense_date = parse_date_to_noon_utc(date_str)

    expense = Expense(
        person_id=person.id,
        amount=float(amount),
        description=description.strip(),
        category=category.strip() if category else None,
        date=expense_date,
        money_source_id=source.id if source else None,
    )
    db.add(expense)
    db.flush()

    for fname in saved_filenames:
        db.add(ExpenseImage(expense_id=expense.id, filename=fname))

    money_source_info = None
    if source:
        balance_before = source.balance
        balance_after = balance_before - float(amount)
        source.balance = balance_after
        movement = MoneySourceMovement(
            money_source_id=source.id,
            type="expense",
            amount=float(amount),
            balance_before=balance_before,
            balance_after=balance_after,
            expense_id=expense.id,
            date=expense_date,
        )
        db.add(movement)

        money_source_info = {
            "name": source.name,
            "balance_before": balance_before,
            "amount_deducted": float(amount),
            "balance_after": balance_after,
        }
        if balance_after < 0:
            money_source_info["warning"] = "Balance went negative"

    db.commit()
    db.refresh(expense)

    budget_alerts = check_budgets(db, person_name, tz)

    return {
        "expense": {
            "id": expense.id,
            "person_id": expense.person_id,
            "amount": expense.amount,
            "description": expense.description,
            "category": expense.category,
            "date": expense.date,
            "money_source_id": expense.money_source_id,
            "images": [img.filename for img in expense.images],
            "created_at": expense.created_at,
        },
        "budget_alerts": budget_alerts,
        "money_source": money_source_info,
    }


def list_expenses(
    db: Session,
    person_name: str | None = None,
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    tz: str = "America/Bogota",
) -> list[dict]:
    query = db.query(Expense)

    if person_name:
        person = db.query(Person).filter(Person.name == person_name).first()
        if not person:
            return []
        query = query.filter(Expense.person_id == person.id)

    range_start, range_end = get_period_range(period, start_date, end_date, tz)
    if range_start and range_end:
        query = query.filter(Expense.date >= range_start, Expense.date <= range_end)

    expenses = query.order_by(Expense.date.desc()).all()

    result = []
    for exp in expenses:
        ms = None
        if exp.money_source:
            ms = {
                "id": exp.money_source.id,
                "name": exp.money_source.name,
                "balance": exp.money_source.balance,
                "enabled": exp.money_source.enabled,
            }
        result.append(
            {
                "id": exp.id,
                "person": {"id": exp.person.id, "name": exp.person.name},
                "amount": exp.amount,
                "description": exp.description,
                "category": exp.category,
                "date": exp.date,
                "money_source": ms,
                "images": [img.filename for img in exp.images],
                "created_at": exp.created_at,
            }
        )

    return result


def get_expense(db: Session, expense_id: int) -> dict:
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    ms = None
    if exp.money_source:
        ms = {
            "id": exp.money_source.id,
            "name": exp.money_source.name,
            "balance": exp.money_source.balance,
            "enabled": exp.money_source.enabled,
        }

    return {
        "id": exp.id,
        "person": {"id": exp.person.id, "name": exp.person.name},
        "amount": exp.amount,
        "description": exp.description,
        "category": exp.category,
        "date": exp.date,
        "money_source": ms,
        "images": [img.filename for img in exp.images],
        "created_at": exp.created_at,
    }


def delete_expense(db: Session, expense_id: int) -> dict:
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    if exp.money_source_id:
        source = db.query(MoneySource).filter(MoneySource.id == exp.money_source_id).first()
        if source:
            balance_before = source.balance
            balance_after = balance_before + exp.amount
            source.balance = balance_after
            movement = MoneySourceMovement(
                money_source_id=source.id,
                type="adjustment",
                amount=exp.amount,
                balance_before=balance_before,
                balance_after=balance_after,
                note="Expense deleted \u2014 balance reverted",
                date=datetime.now(timezone.utc),
            )
            db.add(movement)

    for img in exp.images:
        filepath = os.path.join(UPLOAD_DIR, img.filename)
        try:
            os.unlink(filepath)
        except OSError:
            pass

    db.delete(exp)
    db.commit()

    return {"message": "Expense deleted"}


def get_expense_summary(
    db: Session,
    person_name: str | None = None,
    period: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    tz: str = "America/Bogota",
) -> dict:
    query = db.query(Expense)

    if person_name:
        person = db.query(Person).filter(Person.name == person_name).first()
        if not person:
            return {"total": 0, "by_category": []}
        query = query.filter(Expense.person_id == person.id)

    range_start, range_end = get_period_range(period, start_date, end_date, tz)
    if range_start and range_end:
        query = query.filter(Expense.date >= range_start, Expense.date <= range_end)

    base_filters = []
    if person_name:
        person = db.query(Person).filter(Person.name == person_name).first()
        if person:
            base_filters.append(Expense.person_id == person.id)
    if range_start and range_end:
        base_filters.append(Expense.date >= range_start)
        base_filters.append(Expense.date <= range_end)

    total = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(*base_filters)
        .scalar()
    )

    rows = (
        db.query(
            func.coalesce(Expense.category, "Sin categoría").label("category"),
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count"),
        )
        .filter(*base_filters)
        .group_by(func.coalesce(Expense.category, "Sin categoría"))
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    by_category = [
        {"category": r.category, "total": float(r.total), "count": r.count}
        for r in rows
    ]

    return {"total": float(total), "by_category": by_category}
