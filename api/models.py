from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text, Numeric, Enum
)
from sqlalchemy.orm import relationship
import enum
from api.core.database import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    email            = Column(String(255), unique=True, index=True, nullable=False)
    full_name        = Column(String(255), nullable=False)
    hashed_password  = Column(String(255), nullable=False)
    currency         = Column(String(10), default="NGN")
    is_active        = Column(Boolean, default=True)
    two_fa_enabled   = Column(Boolean, default=False)
    totp_secret      = Column(String(64), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    refresh_tokens   = relationship("RefreshToken", back_populates="user", cascade="all, delete")
    transactions     = relationship("Transaction", back_populates="user", cascade="all, delete")
    budgets          = relationship("Budget", back_populates="user", cascade="all, delete")
    notification_pref = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(Text, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user       = relationship("User", back_populates="refresh_tokens")


class Category(Base):
    __tablename__ = "categories"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="category")
    budget_items = relationship("BudgetItem", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    description = Column(String(255), nullable=False)
    amount      = Column(Numeric(15, 2), nullable=False)
    type        = Column(Enum(TransactionType), nullable=False)
    date        = Column(DateTime, default=datetime.utcnow)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user        = relationship("User", back_populates="transactions")
    category    = relationship("Category", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month      = Column(Integer, nullable=False)
    year       = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user       = relationship("User", back_populates="budgets")
    items      = relationship("BudgetItem", back_populates="budget", cascade="all, delete")


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id          = Column(Integer, primary_key=True, index=True)
    budget_id   = Column(Integer, ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    limit       = Column(Numeric(15, 2), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    budget      = relationship("Budget", back_populates="items")
    category    = relationship("Category", back_populates="budget_items")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    budget_alerts         = Column(Boolean, default=True)
    transaction_alerts    = Column(Boolean, default=True)
    weekly_digest         = Column(Boolean, default=True)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user                  = relationship("User", back_populates="notification_pref")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action      = Column(String(100), nullable=False)
    entity      = Column(String(100), nullable=True)
    entity_id   = Column(Integer, nullable=True)
    detail      = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)