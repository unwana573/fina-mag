from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from api.repositories.budget_repo import BudgetRepository, BudgetItemRepository
from api.repositories.transaction_repo import TransactionRepository
from api.models import TransactionType
from api.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetItemResponse


class BudgetService:
    def __init__(self, db: Session):
        self.budget_repo = BudgetRepository(db)
        self.item_repo = BudgetItemRepository(db)
        self.txn_repo = TransactionRepository(db)

    def get_current(self, user_id: int) -> BudgetResponse:
        now = datetime.utcnow()
        budget = self.budget_repo.get_by_month(user_id, now.year, now.month)
        if not budget:
            raise HTTPException(status_code=404, detail="No budget set for this month")
        return self._build_response(budget)

    def create(self, user_id: int, body: BudgetCreate) -> BudgetResponse:
        existing = self.budget_repo.get_by_month(user_id, body.year, body.month)
        if existing:
            raise HTTPException(status_code=409, detail="Budget already exists for this month")

        budget = self.budget_repo.create({
            "user_id": user_id,
            "month": body.month,
            "year": body.year,
        })
        for item in body.items:
            self.item_repo.create({
                "budget_id": budget.id,
                "category_id": item.category_id,
                "limit": item.limit,
            })
        return self._build_response(budget)

    def update(self, user_id: int, budget_id: int, body: BudgetUpdate) -> BudgetResponse:
        budget = self.budget_repo.get(budget_id)
        if not budget or budget.user_id != user_id:
            raise HTTPException(status_code=404, detail="Budget not found")

        for item in body.items:
            self.item_repo.upsert(budget.id, item.category_id, item.limit)

        return self._build_response(budget)

    def update_category(self, user_id: int, budget_id: int, category_id: int, limit: float):
        budget = self.budget_repo.get(budget_id)
        if not budget or budget.user_id != user_id:
            raise HTTPException(status_code=404, detail="Budget not found")
        return self.item_repo.upsert(budget.id, category_id, limit)

    def _build_response(self, budget) -> BudgetResponse:
        item_responses = []
        total_budget = 0.0
        total_spent = 0.0

        for item in budget.items:
            spent = self.txn_repo.sum_by_type(
                budget.user_id, TransactionType.expense, budget.year, budget.month
            )
            cat_spent = float(
                sum(
                    t.amount
                    for t in budget.user.transactions
                    if t.category_id == item.category_id
                ) if hasattr(budget, "user") else 0
            )
            remaining = float(item.limit) - cat_spent
            total_budget += float(item.limit)
            total_spent += cat_spent
            item_responses.append(BudgetItemResponse(
                id=item.id,
                category_id=item.category_id,
                limit=float(item.limit),
                spent=cat_spent,
                remaining=remaining,
            ))

        return BudgetResponse(
            id=budget.id,
            month=budget.month,
            year=budget.year,
            total_budget=total_budget,
            total_spent=total_spent,
            remaining=total_budget - total_spent,
            items=item_responses,
        )