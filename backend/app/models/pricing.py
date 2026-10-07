from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Pricing(Base):
    __tablename__ = "pricing"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    store_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    price_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "store_id",
            "sku",
            "price_date",
            name="uq_pricing_store_sku_date",
        ),
    )