from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.models import Transaction, TransactionType, Category


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def total_balance(self, user_id: int) -> float:
        income = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.type == TransactionType.income)
            .scalar() or 0
        )
        expense = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.type == TransactionType.expense)
            .scalar() or 0
        )
        return float(income) - float(expense)

    def total_by_type(self, user_id: int, type: TransactionType) -> float:
        result = (
            self.db.query(func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.type == type)
            .scalar()
        )
        return float(result or 0)

    def total_by_type_and_month(self, user_id: int, type: TransactionType, year: int, month: int) -> float:
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

    def spending_breakdown(self, user_id: int) -> List[dict]:
        rows = (
            self.db.query(
                Transaction.category_id,
                Category.name.label("category_name"),
                func.sum(Transaction.amount).label("total"),
            )
            .join(Category, Category.id == Transaction.category_id, isouter=True)
            .filter(Transaction.user_id == user_id, Transaction.type == TransactionType.expense)
            .group_by(Transaction.category_id, Category.name)
            .all()
        )
        return [
            {
                "category_id": r.category_id,
                "category_name": r.category_name or "Uncategorised",
                "total": float(r.total),
            }
            for r in rows
        ]

    def monthly_trends(self, user_id: int, months: int = 6) -> List[dict]:
        rows = (
            self.db.query(
                func.extract("year", Transaction.date).label("year"),
                func.extract("month", Transaction.date).label("month"),
                Transaction.type,
                func.sum(Transaction.amount).label("total"),
            )
            .filter(Transaction.user_id == user_id)
            .group_by("year", "month", Transaction.type)
            .order_by("year", "month")
            .all()
        )
        return [
            {
                "year": int(r.year),
                "month": int(r.month),
                "type": r.type,
                "total": float(r.total),
            }
            for r in rows
        ]