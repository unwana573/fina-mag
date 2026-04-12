import hmac
import hashlib
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from api.core.database import get_db
from api.core.config import settings
from api.models import Transaction, TransactionType

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _verify_paystack(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _verify_flutterwave(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.FLUTTERWAVE_SECRET_KEY.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not _verify_paystack(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    event = data.get("event")

    if event == "charge.success":
        charge = data["data"]
        db.add(Transaction(
            user_id=charge.get("metadata", {}).get("user_id"),
            description=charge.get("narration", "Paystack payment"),
            amount=charge["amount"] / 100,
            type=TransactionType.income,
            date=datetime.utcnow(),
        ))
        db.commit()

    return {"status": "ok"}


@router.post("/flutterwave")
async def flutterwave_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("verif-hash", "")

    if signature != settings.FLUTTERWAVE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = await request.json()
    event = data.get("event")

    if event == "charge.completed" and data.get("data", {}).get("status") == "successful":
        charge = data["data"]
        db.add(Transaction(
            user_id=charge.get("meta", {}).get("user_id"),
            description=charge.get("narration", "Flutterwave payment"),
            amount=float(charge["amount"]),
            type=TransactionType.income,
            date=datetime.utcnow(),
        ))
        db.commit()

    return {"status": "ok"}