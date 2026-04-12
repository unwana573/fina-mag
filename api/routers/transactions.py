from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models import User, TransactionType
from api.schemas.transaction import (
    TransactionCreate, TransactionUpdate,
    TransactionResponse, PaginatedTransactions,
)
from api.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=PaginatedTransactions)
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    category_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).list(
        current_user.id, skip, limit, category_id, type, date_from, date_to
    )


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).create(current_user.id, body)


@router.get("/export")
def export_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    csv_data = TransactionService(db).export_csv(current_user.id)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).get(current_user.id, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    body: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService(db).update(current_user.id, transaction_id, body)


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    TransactionService(db).delete(current_user.id, transaction_id)