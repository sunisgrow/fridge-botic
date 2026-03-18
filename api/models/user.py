"""User model."""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, DateTime, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from ..database.base import Base


class User(Base):
    """Telegram user."""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    timezone = Column(String(50), default="UTC")
    language_code = Column(String(10), default="ru")

    # Notification settings
    notifications_enabled = Column(Boolean, default=True)
    notifications_days_before = Column(Integer, default=3)
    notifications_time = Column(String(5), default="09:00")

    # Relationships
    fridges = relationship("Fridge", backref="user", cascade="all, delete-orphan")
