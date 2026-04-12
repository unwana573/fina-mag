from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from api.repositories.analytics_repo import AnalyticsRepository
from api.models import TransactionType


class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = AnalyticsRepository(db)

    def summary(self, user_id: int) -> dict:
        now = datetime.utcnow()
        prev_month = now.month - 1 or 12
        prev_year = now.year if now.month > 1 else now.year - 1

        income = self.repo.total_by_type(user_id, TransactionType.income)
        expenses = self.repo.total_by_type(user_id, TransactionType.expense)
        balance = income - expenses
        savings = income - expenses

        cur_income = self.repo.total_by_type_and_month(user_id, TransactionType.income, now.year, now.month)
        cur_expense = self.repo.total_by_type_and_month(user_id, TransactionType.expense, now.year, now.month)
        prev_income = self.repo.total_by_type_and_month(user_id, TransactionType.income, prev_year, prev_month)
        prev_expense = self.repo.total_by_type_and_month(user_id, TransactionType.expense, prev_year, prev_month)
        prev_balance = prev_income - prev_expense

        def pct_change(current, previous):
            if previous == 0:
                return None
            return round(((current - previous) / previous) * 100, 1)

        return {
            "total_balance": balance,
            "total_balance_change_pct": pct_change(balance, prev_balance),
            "income": income,
            "income_change_pct": pct_change(cur_income, prev_income),
            "expenses": expenses,
            "expenses_change_pct": pct_change(cur_expense, prev_expense),
            "savings": savings,
            "savings_change_pct": pct_change(cur_income - cur_expense, prev_income - prev_expense),
        }

    def trends(self, user_id: int, months: int = 6) -> List[dict]:
        rows = self.repo.monthly_trends(user_id, months)
        result: dict = {}

        for row in rows:
            key = (row["year"], row["month"])
            if key not in result:
                result[key] = {
                    "year": row["year"],
                    "month": row["month"],
                    "income": 0.0,
                    "expenses": 0.0,
                    "savings": 0.0,
                }
            if row["type"] == TransactionType.income:
                result[key]["income"] = row["total"]
            else:
                result[key]["expenses"] = row["total"]

        for key in result:
            result[key]["savings"] = result[key]["income"] - result[key]["expenses"]

        return sorted(result.values(), key=lambda x: (x["year"], x["month"]))

    def breakdown(self, user_id: int) -> List[dict]:
        return self.repo.spending_breakdown(user_id)

    def insights(self, user_id: int) -> List[dict]:
        summary = self.summary(user_id)
        trends = self.trends(user_id, months=6)
        insights = []

        if summary.get("income_change_pct") is not None:
            pct = summary["income_change_pct"]
            if pct > 0:
                insights.append({
                    "type": "positive",
                    "icon": "trending_up",
                    "message": f"Your income grew {pct}% over the last 6 months — keep it up!",
                })
            else:
                insights.append({
                    "type": "warning",
                    "icon": "trending_down",
                    "message": f"Your income dropped {abs(pct)}% vs last month.",
                })

        breakdown = self.breakdown(user_id)
        total_expenses = summary["expenses"]
        if total_expenses > 0 and breakdown:
            top = max(breakdown, key=lambda x: x["total"])
            pct = round((top["total"] / total_expenses) * 100, 0)
            if pct > 50:
                insights.append({
                    "type": "warning",
                    "icon": "warning",
                    "message": f"{top['category_name']} takes {int(pct)}% of your expenses. Consider negotiating.",
                })

        if summary["savings"] > 0:
            insights.append({
                "type": "info",
                "icon": "lightbulb",
                "message": f"You're saving ₦{summary['savings']:,.0f} — aim for 6 months emergency fund.",
            })

        return insights