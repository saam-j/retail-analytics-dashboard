"""Grain: `orders` = one row per ORDER LINE (order_id repeats). Count DISTINCT order_id.
Conventions: sales_amount = revenue AFTER discount (discount never subtracted again);
discount = fraction 0..1; profit = sales_amount - cost_amount."""
from datetime import date
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, Date, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base
M = Numeric(14, 2)
class Region(Base):
    __tablename__ = "regions"
    region_id: Mapped[int] = mapped_column(primary_key=True)
    region_name: Mapped[str] = mapped_column(String(50), unique=True)
    country: Mapped[str] = mapped_column(String(50))
class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(100))
    customer_segment: Mapped[str] = mapped_column(String(30), index=True)
    city: Mapped[str] = mapped_column(String(60))
    state: Mapped[str] = mapped_column(String(60))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.region_id"))
class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50), index=True)
    subcategory: Mapped[str] = mapped_column(String(50))
    unit_cost: Mapped[Decimal] = mapped_column(M)
class Order(Base):
    __tablename__ = "orders"
    line_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(20), index=True)
    order_date: Mapped[date] = mapped_column(Date, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.customer_id"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.region_id"), index=True)
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(M)
    discount: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0)
    sales_amount: Mapped[Decimal] = mapped_column(M)
    cost_amount: Mapped[Decimal] = mapped_column(M)
    profit: Mapped[Decimal] = mapped_column(M)
    order_status: Mapped[str] = mapped_column(String(20), default="completed")
    __table_args__ = (CheckConstraint("quantity > 0"), CheckConstraint("discount >= 0 AND discount <= 1"),
                      Index("ix_orders_cust", "customer_id"), Index("ix_orders_prod", "product_id"))
