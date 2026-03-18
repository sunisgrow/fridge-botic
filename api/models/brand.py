"""Brand model."""

from sqlalchemy import Column, Integer, String
from ..database.base import Base


class Brand(Base):
    """Product brand."""
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    country = Column(String(50), nullable=True)
