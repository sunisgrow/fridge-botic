"""Product model."""

from sqlalchemy import Column, Integer, String, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database.base import Base


class Product(Base):
    """Product in catalog."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True)
    default_shelf_life_days = Column(Integer, nullable=True)

    # Relationships
    category = relationship("Category", backref="products")
    brand = relationship("Brand", backref="products")


class ProductGTIN(Base):
    """GTIN codes for products."""
    __tablename__ = "product_gtins"
    __table_args__ = (
        UniqueConstraint('gtin', name='uq_gtin'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    gtin = Column(String(14), nullable=False, index=True)

    # Relationships
    product = relationship("Product", backref="gtins")
