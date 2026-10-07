from datetime import date, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pricing import Pricing


class PricingRepository:

    def create(self, db: Session, pricing: Pricing) -> Pricing:
        db.add(pricing)
        db.commit()
        db.refresh(pricing)
        return pricing

    def get_by_id(self, db: Session, pricing_id: int) -> Optional[Pricing]:
        return db.get(Pricing, pricing_id)

    def search(
        self,
        db: Session,
        store_id: str = None,
        sku: str = None,
        product_name: str = None,
        price_date: date = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Pricing]:
        query = select(Pricing)
        filters = []

        if store_id is not None:
            filters.append(Pricing.store_id == store_id)
        if sku is not None:
            filters.append(Pricing.sku == sku)
        if product_name is not None:
            filters.append(Pricing.product_name.ilike(f"%{product_name}%"))
        if price_date is not None:
            filters.append(Pricing.price_date == price_date)

        if filters:
            query = query.where(*filters)

        query = query.order_by(Pricing.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        return list(db.scalars(query).all())

    def update_price(
        self,
        db: Session,
        pricing_id: int,
        price: float,
        version: int,
    ) -> Optional[Pricing]:
        pricing = self.get_by_id(db, pricing_id)

        if pricing is None or pricing.version != version:
            return None

        pricing.price = price
        pricing.version += 1
        pricing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(pricing)
        return pricing