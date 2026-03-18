# -*- coding: utf-8 -*-
"""Fridge models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Text, DateTime, BigInteger
from sqlalchemy.orm import relationship
from ..database.base import Base


class Fridge(Base):
    """User's fridge."""
    __tablename__ = "fridges"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), default="Main Fridge")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    items = relationship("FridgeItem", back_populates="fridge", cascade="all, delete-orphan")


class FridgeZone(Base):
    """Storage zone within fridge."""
    __tablename__ = "fridge_zones"

    id = Column(BigInteger, primary_key=True, index=True)
    fridge_id = Column(BigInteger, ForeignKey("fridges.id"), nullable=False)
    name = Column(String(50), nullable=False)

    # Relationships
    items = relationship("FridgeItem", back_populates="zone")


class FridgeItem(Base):
    """Item stored in fridge."""
    __tablename__ = "fridge_items"

    id = Column(BigInteger, primary_key=True, index=True)
    fridge_id = Column(BigInteger, ForeignKey("fridges.id"), nullable=False)
    zone_id = Column(BigInteger, ForeignKey("fridge_zones.id"), nullable=True)
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=True)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    expiration_date = Column(Date, nullable=True)
    opened = Column(Boolean, default=False)
    note = Column(Text, nullable=True)

    # Relationships
    fridge = relationship("Fridge", back_populates="items")
    product = relationship("Product", backref="fridge_items")
    zone = relationship("FridgeZone", back_populates="items")
