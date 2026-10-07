from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.pricing import Pricing
from app.repositories.pricing import PricingRepository
from app.schemas.pricing import PricingCreate, PricingUpdate


class PricingService:

    def __init__(self):
        self.repository = PricingRepository()

    def create(
        self,
        db: Session,
        pricing_data: PricingCreate,
    ) -> Pricing:
        pricing = Pricing(
            store_id=pricing_data.store_id,
            sku=pricing_data.sku,
            product_name=pricing_data.product_name,
            price=pricing_data.price,
            price_date=pricing_data.price_date,
        )

        return self.repository.create(db, pricing)

    def search(
        self,
        db: Session,
        store_id: Optional[str] = None,
        sku: Optional[str] = None,
        product_name: Optional[str] = None,
        price_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Pricing]:
        return self.repository.search(
            db=db,
            store_id=store_id,
            sku=sku,
            product_name=product_name,
            price_date=price_date,
            page=page,
            page_size=page_size,
        )

    def update_price(
        self,
        db: Session,
        pricing_id: int,
        pricing_data: PricingUpdate,
    ) -> Optional[Pricing]:
        return self.repository.update_price(
            db=db,
            pricing_id=pricing_id,
            price=pricing_data.price,
            version=pricing_data.version,
        )