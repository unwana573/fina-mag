from sqlalchemy.orm import Session
from fastapi import HTTPException
from api.models import NotificationPreference
from api.core.config import settings


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, user_id: int) -> NotificationPreference:
        pref = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
        if not pref:
            pref = NotificationPreference(user_id=user_id)
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
        return pref

    def update(self, user_id: int, data: dict) -> NotificationPreference:
        pref = self.get_or_create(user_id)
        for key, value in data.items():
            setattr(pref, key, value)
        self.db.commit()
        self.db.refresh(pref)
        return pref

    def send_budget_alert(self, user_email: str, category: str, spent: float, limit: float):
        if not settings.SENDGRID_API_KEY:
            return
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=user_email,
                subject="NairaFlow — Budget Alert",
                plain_text_content=(
                    f"You have spent ₦{spent:,.0f} of your ₦{limit:,.0f} "
                    f"budget for {category}."
                ),
            )
            SendGridAPIClient(settings.SENDGRID_API_KEY).send(message)
        except Exception:
            pass

    def send_weekly_digest(self, user_email: str, summary: dict):
        if not settings.SENDGRID_API_KEY:
            return
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            body = (
                f"Weekly NairaFlow Summary\n\n"
                f"Balance:  ₦{summary['total_balance']:,.0f}\n"
                f"Income:   ₦{summary['income']:,.0f}\n"
                f"Expenses: ₦{summary['expenses']:,.0f}\n"
                f"Savings:  ₦{summary['savings']:,.0f}\n"
            )
            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=user_email,
                subject="Your NairaFlow Weekly Digest",
                plain_text_content=body,
            )
            SendGridAPIClient(settings.SENDGRID_API_KEY).send(message)
        except Exception:
            pass