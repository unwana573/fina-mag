from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.repositories.transaction_repo import TransactionRepository
from api.models import TransactionType
from api.schemas.transaction import TransactionCreate, TransactionUpdate, PaginatedTransactions


class TransactionService:
    def __init__(self, db: Session):
        self.repo = TransactionRepository(db)

    def list(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        category_id: Optional[int] = None,
        type: Optional[TransactionType] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> PaginatedTransactions:
        items, total = self.repo.get_by_user(
            user_id, skip, limit, category_id, type, date_from, date_to
        )
        return PaginatedTransactions(items=items, total=total, skip=skip, limit=limit)

    def create(self, user_id: int, body: TransactionCreate):
        data = body.model_dump()
        data["user_id"] = user_id
        if not data.get("date"):
            data["date"] = datetime.utcnow()
        return self.repo.create(data)

    def get(self, user_id: int, transaction_id: int):
        txn = self.repo.get_user_transaction(user_id, transaction_id)
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return txn

    def update(self, user_id: int, transaction_id: int, body: TransactionUpdate):
        txn = self.get(user_id, transaction_id)
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        return self.repo.update(txn, data)

    def delete(self, user_id: int, transaction_id: int) -> None:
        txn = self.get(user_id, transaction_id)
        self.repo.delete(txn)

    def export_csv(self, user_id: int) -> str:
        import csv, io
        items, _ = self.repo.get_by_user(user_id, limit=10000)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "date", "description", "type", "category_id", "amount"])
        for t in items:
            writer.writerow([t.id, t.date, t.description, t.type, t.category_id, t.amount])
        return output.getvalue()