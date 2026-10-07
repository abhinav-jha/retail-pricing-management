import csv
from datetime import date
from decimal import Decimal
from typing import Optional

from celery import Celery

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.import_job import ImportJob
from app.models.pricing import Pricing


celery_app = Celery(
    "retail_pricing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="pricing.process_csv_import")
def process_csv_import(file_path: str, import_id: Optional[int] = None) -> dict:
    """Process a queued CSV import job asynchronously in batches."""
    session = SessionLocal()
    job = None

    if import_id is not None:
        job = session.get(ImportJob, import_id)
        if job is not None:
            job.status = "processing"
            job.error_message = None
            session.commit()

    try:
        with open(file_path, newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            expected_columns = ["Store ID", "SKU", "Product Name", "Price", "Date"]
            batch_size = 1000
            batch = []
            total_rows = 0
            processed = 0

            if not reader.fieldnames or any(
                column not in reader.fieldnames
                for column in expected_columns
            ):
                raise ValueError(
                    "CSV headers must include: Store ID, SKU, Product Name, Price, Date"
                )

            for row in reader:
                if not row or all(
                    (value is None or str(value).strip() == "")
                    for value in row.values()
                ):
                    continue

                pricing = Pricing(
                    store_id=str(row["Store ID"]).strip(),
                    sku=str(row["SKU"]).strip(),
                    product_name=str(row["Product Name"]).strip(),
                    price=Decimal(str(row["Price"]).strip()),
                    price_date=date.fromisoformat(str(row["Date"]).strip()),
                )
                batch.append(pricing)
                total_rows += 1

                if len(batch) >= batch_size:
                    session.add_all(batch)
                    session.commit()
                    processed += len(batch)
                    batch.clear()

                    if job is not None:
                        job.total_rows = total_rows
                        job.processed_rows = processed
                        session.commit()

            if batch:
                session.add_all(batch)
                session.commit()
                processed += len(batch)
                batch.clear()

                if job is not None:
                    job.total_rows = total_rows
                    job.processed_rows = processed
                    session.commit()

            if job is not None:
                job.status = "completed"
                job.total_rows = total_rows
                job.processed_rows = processed
                session.commit()

            return {
                "status": "completed",
                "file_path": file_path,
                "import_id": import_id,
                "processed_rows": processed,
            }
    except Exception as error:
        session.rollback()
        if job is not None:
            job.status = "failed"
            job.error_message = str(error)[:500]
            session.commit()
        return {
            "status": "failed",
            "file_path": file_path,
            "import_id": import_id,
            "error": str(error),
        }
    finally:
        session.close()
