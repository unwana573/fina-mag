from typing import Optional
from sqlalchemy.orm import Session
from api.models import Budget, BudgetItem
from api.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, db: Session):
        super().__init__(Budget, db)

    def get_by_month(self, user_id: int, year: int, month: int) -> Optional[Budget]:
        return (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.year == year, Budget.month == month)
            .first()
        )

    def get_with_items(self, budget_id: int) -> Optional[Budget]:
        return self.db.query(Budget).filter(Budget.id == budget_id).first()


class BudgetItemRepository(BaseRepository[BudgetItem]):
    def __init__(self, db: Session):
        super().__init__(BudgetItem, db)

    def get_by_category(self, budget_id: int, category_id: int) -> Optional[BudgetItem]:
        return (
            self.db.query(BudgetItem)
            .filter(BudgetItem.budget_id == budget_id, BudgetItem.category_id == category_id)
            .first()
        )

    def upsert(self, budget_id: int, category_id: int, limit: float) -> BudgetItem:
        item = self.get_by_category(budget_id, category_id)
        if item:
            return self.update(item, {"limit": limit})
        return self.create({"budget_id": budget_id, "category_id": category_id, "limit": limit})