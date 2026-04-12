from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from api.models import Transaction, TransactionType
from api.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[int] = None,
        type: Optional[TransactionType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[Transaction], int]:
        q = self.db.query(Transaction).filter(Transaction.user_id == user_id)

        if category_id:
            q = q.filter(Transaction.category_id == category_id)
        if type:
            q = q.filter(Transaction.type == type)
        if date_from:
            q = q.filter(Transaction.date >= date_from)
        if date_to:
            q = q.filter(Transaction.date <= date_to)

        total = q.count()
        items = q.order_by(desc(Transaction.date)).offset(skip).limit(limit).all()
        return items, total

    def get_user_transaction(self, user_id: int, transaction_id: int) -> Optional[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
            .first()
        )

    def sum_by_type(self, user_id: int, type: TransactionType, year: int, month: int) -> float:
        result = (
            self.db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == type,
                func.extract("year", Transaction.date) == year,
                func.extract("month", Transaction.date) == month,
            )
            .scalar()
        )
        return float(result or 0)

    def sum_by_category(self, user_id: int, year: int, month: int) -> List[dict]:
        rows = (
            self.db.query(Transaction.category_id, func.sum(Transaction.amount).label("total"))
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == TransactionType.expense,
                func.extract("year", Transaction.date) == year,
                func.extract("month", Transaction.date) == month,
            )
            .group_by(Transaction.category_id)
            .all()
        )
        return [{"category_id": r.category_id, "total": float(r.total)} for r in rows]

    def monthly_totals(self, user_id: int, months: int = 6) -> List[dict]:
        rows = (
            self.db.query(
                func.extract("year", Transaction.date).label("year"),
                func.extract("month", Transaction.date).label("month"),
                Transaction.type,
                func.sum(Transaction.amount).label("total"),
            )
            .filter(Transaction.user_id == user_id)
            .group_by("year", "month", Transaction.type)
            .order_by(desc("year"), desc("month"))
            .limit(months * 2)
            .all()
        )
        return [
            {"year": int(r.year), "month": int(r.month), "type": r.type, "total": float(r.total)}
            for r in rows
        ]