import os
from datetime import date
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.database as db_module
from app.db.database import Base, get_db
from app.main import app
from app.models.import_job import ImportJob
from app.models.pricing import Pricing
from app.schemas.pricing import PricingCreate, PricingUpdate
from app.services.pricing import PricingService
import app.worker as worker_module


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return Session(bind=engine)


def test_create_and_search_pricing():
    db = _session()
    service = PricingService()

    payload = PricingCreate(
        store_id="1001",
        sku="SKU001",
        product_name="Widget",
        price=Decimal("10.99"),
        price_date=date(2026, 1, 15),
    )

    created = service.create(db=db, pricing_data=payload)
    assert created.id is not None
    assert created.version == 1

    results = service.search(db=db, store_id="1001", page=1, page_size=20)
    assert len(results) == 1
    assert results[0].product_name == "Widget"


def test_update_price_requires_matching_version():
    db = _session()
    service = PricingService()

    payload = PricingCreate(
        store_id="2002",
        sku="SKU002",
        product_name="Gadget",
        price=Decimal("19.50"),
        price_date=date(2026, 2, 10),
    )

    created = service.create(db=db, pricing_data=payload)

    updated = service.update_price(
        db=db,
        pricing_id=created.id,
        pricing_data=PricingUpdate(price=Decimal("21.00"), version=created.version),
    )
    assert updated is not None
    assert updated.price == Decimal("21.00")
    assert updated.version == 2

    stale = service.update_price(
        db=db,
        pricing_id=created.id,
        pricing_data=PricingUpdate(price=Decimal("22.00"), version=1),
    )
    assert stale is None


def test_csv_import_job_updates_status(tmp_path):
    db_path = tmp_path / "pricing_worker.sqlite"
    import_engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=import_engine)
    worker_module.SessionLocal = sessionmaker(bind=import_engine)

    sample_path = tmp_path / "pricing.csv"
    sample_path.write_text(
        "Store ID,SKU,Product Name,Price,Date\n"
        "1001,SKU001,Widget,10.99,2026-01-15\n"
        "1002,SKU002,Gadget,19.50,2026-02-10\n",
        encoding="utf-8",
    )

    with Session(bind=import_engine) as db:
        job = ImportJob(file_name="pricing.csv", file_path=str(sample_path), status="queued")
        db.add(job)
        db.commit()
        db.refresh(job)

        result = worker_module.process_csv_import(str(sample_path), job.id)
        assert result["status"] == "completed"
        assert result["processed_rows"] == 2

        with Session(bind=import_engine) as fresh_db:
            updated = fresh_db.get(ImportJob, job.id)
            assert updated.status == "completed"
            assert updated.total_rows == 2
            assert updated.processed_rows == 2


def test_import_status_route_supports_jobs_alias():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    db_module.engine = test_engine
    db_module.SessionLocal = sessionmaker(bind=test_engine)

    def override_get_db():
        db = Session(bind=test_engine)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with Session(bind=test_engine) as db:
            job = ImportJob(
                file_name="pricing.csv",
                file_path="/tmp/pricing.csv",
                status="queued",
                total_rows=0,
                processed_rows=0,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        with TestClient(app) as client:
            imports_response = client.get(f"/api/v1/pricing/imports/{job.id}")
            jobs_response = client.get(f"/api/v1/pricing/jobs/{job.id}")

        assert imports_response.status_code == 200
        assert jobs_response.status_code == 200
        assert imports_response.json()["status"] == "queued"
        assert jobs_response.json()["status"] == "queued"
    finally:
        app.dependency_overrides.clear()
