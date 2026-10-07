from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PricingBase(BaseModel):
    store_id: str = Field(min_length=1, max_length=50)
    sku: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0)
    price_date: date


class PricingCreate(PricingBase):
    pass


class PricingUpdate(BaseModel):
    price: Decimal = Field(gt=0)
    version: int = Field(ge=1)


class PricingResponse(PricingBase):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }