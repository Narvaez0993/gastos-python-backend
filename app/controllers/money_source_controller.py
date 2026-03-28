from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.money_source import MoneySource
from app.models.money_source_movement import MoneySourceMovement
from app.models.person import Person
from app.schemas.money_source import DepositRequest, MoneySourceCreate, MoneySourceUpdate


def create_money_source(db: Session, data: MoneySourceCreate) -> MoneySource:
    if not data.personName or not data.name:
        raise HTTPException(
            status_code=400, detail="personName and name are required"
        )

    person = db.query(Person).filter(Person.name == data.personName).first()
    if not person:
        raise HTTPException(
            status_code=404, detail=f'Person "{data.personName}" not found'
        )

    name = data.name.strip()
    name_normalized = name.lower().strip()

    source = MoneySource(
        person_id=person.id,
        name=name,
        name_normalized=name_normalized,
        balance=data.balance,
    )

    try:
        db.add(source)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f'You already have a money source named "{data.name}"',
        )

    if data.balance and data.balance != 0:
        movement = MoneySourceMovement(
            money_source_id=source.id,
            type="adjustment",
            amount=abs(data.balance),
            balance_before=0,
            balance_after=data.balance,
            note="Initial balance",
            date=datetime.now(timezone.utc),
        )
        db.add(movement)

    db.commit()
    db.refresh(source)
    return source


def list_money_sources(db: Session, person_name: str) -> list[MoneySource]:
    if not person_name:
        raise HTTPException(
            status_code=400, detail="personName query parameter is required"
        )

    person = db.query(Person).filter(Person.name == person_name).first()
    if not person:
        return []

    return (
        db.query(MoneySource)
        .filter(MoneySource.person_id == person.id)
        .order_by(MoneySource.enabled.desc(), MoneySource.name.asc())
        .all()
    )


def update_money_source(
    db: Session, source_id: int, data: MoneySourceUpdate
) -> MoneySource:
    source = db.query(MoneySource).filter(MoneySource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Money source not found")

    if data.balance is not None and data.balance != source.balance:
        balance_before = source.balance
        balance_after = data.balance
        source.balance = balance_after
        movement = MoneySourceMovement(
            money_source_id=source.id,
            type="adjustment",
            amount=abs(balance_after - balance_before),
            balance_before=balance_before,
            balance_after=balance_after,
            note="Manual adjustment",
            date=datetime.now(timezone.utc),
        )
        db.add(movement)

    if data.enabled is not None:
        source.enabled = data.enabled

    if data.name is not None:
        new_name = data.name.strip()
        new_normalized = new_name.lower().strip()
        existing = (
            db.query(MoneySource)
            .filter(
                MoneySource.person_id == source.person_id,
                MoneySource.name_normalized == new_normalized,
                MoneySource.id != source.id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="You already have a money source with that name",
            )
        source.name = new_name
        source.name_normalized = new_normalized

    db.commit()
    db.refresh(source)
    return source


def delete_money_source(db: Session, source_id: int) -> dict:
    source = db.query(MoneySource).filter(MoneySource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Money source not found")

    has_movements = (
        db.query(MoneySourceMovement)
        .filter(MoneySourceMovement.money_source_id == source.id)
        .first()
    )
    if has_movements:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a money source with movements. Disable it instead.",
        )

    db.delete(source)
    db.commit()
    return {"message": "Money source deleted"}


def deposit(db: Session, source_id: int, data: DepositRequest) -> dict:
    if not data.amount or data.amount <= 0:
        raise HTTPException(
            status_code=400, detail="A positive amount is required"
        )

    source = db.query(MoneySource).filter(MoneySource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Money source not found")

    if not source.enabled:
        raise HTTPException(
            status_code=400,
            detail="Cannot deposit to a disabled money source",
        )

    balance_before = source.balance
    balance_after = balance_before + data.amount
    source.balance = balance_after

    deposit_date = datetime.now(timezone.utc)
    if data.date:
        try:
            deposit_date = datetime.strptime(data.date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            deposit_date = datetime.now(timezone.utc)

    movement = MoneySourceMovement(
        money_source_id=source.id,
        type="deposit",
        amount=data.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        note=data.note,
        date=deposit_date,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    db.refresh(source)

    return {"movement": movement, "source": source}


def get_movements(
    db: Session,
    source_id: int,
    movement_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    source = db.query(MoneySource).filter(MoneySource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Money source not found")

    page = max(1, page)
    limit = max(1, min(100, limit))

    query = db.query(MoneySourceMovement).filter(
        MoneySourceMovement.money_source_id == source_id
    )

    if movement_type:
        query = query.filter(MoneySourceMovement.type == movement_type)

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(MoneySourceMovement.date >= sd)
        except ValueError:
            pass

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999000, tzinfo=timezone.utc
            )
            query = query.filter(MoneySourceMovement.date <= ed)
        except ValueError:
            pass

    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 1

    movements = (
        query.order_by(
            MoneySourceMovement.date.desc(), MoneySourceMovement.created_at.desc()
        )
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    movements_out = []
    for m in movements:
        expense_data = None
        if m.expense:
            expense_data = {
                "id": m.expense.id,
                "description": m.expense.description,
                "amount": m.expense.amount,
                "category": m.expense.category,
            }
        movements_out.append(
            {
                "id": m.id,
                "money_source_id": m.money_source_id,
                "type": m.type,
                "amount": m.amount,
                "balance_before": m.balance_before,
                "balance_after": m.balance_after,
                "expense": expense_data,
                "note": m.note,
                "date": m.date,
                "created_at": m.created_at,
            }
        )

    return {
        "movements": movements_out,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": pages,
        },
    }
