from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.core.audit import log
from api.models import User
from api.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetSummaryResponse
from api.services.budget_service import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("/summary", response_model=BudgetSummaryResponse)
def get_budget_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).get_summary(current_user.id)


@router.get("", response_model=BudgetResponse)
def get_budget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).get_current(current_user.id)


@router.get("/month", response_model=BudgetResponse)
def get_budget_by_month(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).get_by_month(current_user.id, year, month)


@router.post("", response_model=BudgetResponse, status_code=201)
def create_budget(
    body: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = BudgetService(db).create(current_user.id, body)
    log(db, action="budget.created", user_id=current_user.id,
        entity="budget", entity_id=budget.id,
        detail=f"month={body.month} year={body.year}")
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    body: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = BudgetService(db).update(current_user.id, budget_id, body)
    log(db, action="budget.updated", user_id=current_user.id,
        entity="budget", entity_id=budget_id)
    return budget


@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = BudgetService(db)
    budget = service.budget_repo.get(budget_id)
    if not budget or budget.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Budget not found")
    service.budget_repo.delete(budget)
    log(db, action="budget.deleted", user_id=current_user.id,
        entity="budget", entity_id=budget_id)


@router.patch("/categories/{budget_id}/{category_id}")
def update_category_limit(
    budget_id: int,
    category_id: int,
    limit: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).update_category(current_user.id, budget_id, category_id, limit)