from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from api.repositories.analytics_repo import AnalyticsRepository
from api.models import TransactionType


class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = AnalyticsRepository(db)

    def summary(self, user_id: int) -> dict:
        balance = self.repo.total_balance(user_id)
        income = self.repo.total_by_type(user_id, TransactionType.income)
        expenses = self.repo.total_by_type(user_id, TransactionType.expense)
        savings = income - expenses

        return {
            "total_balance": balance,
            "income": income,
            "expenses": expenses,
            "savings": savings,
        }

    def trends(self, user_id: int, months: int = 6) -> List[dict]:
        rows = self.repo.monthly_trends(user_id, months)
        result: dict = {}

        for row in rows:
            key = (row["year"], row["month"])
            if key not in result:
                result[key] = {"year": row["year"], "month": row["month"], "income": 0.0, "expenses": 0.0}
            if row["type"] == TransactionType.income:
                result[key]["income"] = row["total"]
            else:
                result[key]["expenses"] = row["total"]

        return sorted(result.values(), key=lambda x: (x["year"], x["month"]))

    def breakdown(self, user_id: int) -> List[dict]:
        return self.repo.spending_breakdown(user_id)

    def insights(self, user_id: int) -> List[dict]:
        summary = self.summary(user_id)
        trends = self.trends(user_id, months=6)
        insights = []

        if len(trends) >= 2:
            latest = trends[-1]["income"]
            previous = trends[-2]["income"]
            if previous > 0:
                growth = ((latest - previous) / previous) * 100
                if growth > 0:
                    insights.append({
                        "type": "positive",
                        "message": f"Your income grew {growth:.1f}% vs last month — keep it up!",
                    })
                else:
                    insights.append({
                        "type": "warning",
                        "message": f"Your income dropped {abs(growth):.1f}% vs last month.",
                    })

        breakdown = self.breakdown(user_id)
        total_expenses = summary["expenses"]
        if total_expenses > 0 and breakdown:
            top = max(breakdown, key=lambda x: x["total"])
            pct = (top["total"] / total_expenses) * 100
            if pct > 50:
                insights.append({
                    "type": "warning",
                    "message": f"Category {top['category_id']} takes {pct:.0f}% of your expenses. Consider reviewing.",
                })

        if summary["savings"] > 0:
            monthly_expenses = total_expenses / max(len(trends), 1)
            months_covered = summary["savings"] / monthly_expenses if monthly_expenses > 0 else 0
            insights.append({
                "type": "info",
                "message": f"You're saving ₦{summary['savings']:,.0f} — aim for 6 months emergency fund.",
            })

        return insights