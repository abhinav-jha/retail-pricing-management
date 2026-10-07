import shutil
import uuid
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.import_job import ImportJob
from app.schemas.import_job import ImportJobResponse
from app.schemas.pricing import PricingCreate, PricingResponse, PricingUpdate
from app.services.pricing import PricingService
from app.worker import process_csv_import


router = APIRouter(
    prefix="/api/v1/pricing",
    tags=["Pricing"],
)

pricing_service = PricingService()


@router.post(
    "",
    response_model=PricingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pricing(
    pricing_data: PricingCreate,
    db: Session = Depends(get_db),
):
    return pricing_service.create(
        db=db,
        pricing_data=pricing_data,
    )


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_pricing_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = file.filename.replace(" ", "_")
    storage_path = upload_dir / f"{Path(safe_name).stem}_{uuid.uuid4().hex}.csv"

    with storage_path.open("wb") as target_file:
        shutil.copyfileobj(file.file, target_file)

    job = ImportJob(
        file_name=file.filename,
        file_path=str(storage_path),
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    process_csv_import.apply_async(args=[job.file_path, job.id])

    return {
        "job_id": job.id,
        "status": job.status,
        "message": "CSV import queued for processing",
    }


@router.get(
    "/imports/{job_id}",
    response_model=ImportJobResponse,
)
@router.get(
    "/jobs/{job_id}",
    response_model=ImportJobResponse,
)
def get_import_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(ImportJob, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found",
        )

    return job


@router.get(
    "",
    response_model=list[PricingResponse],
)
def search_pricing(
    store_id: Optional[str] = None,
    sku: Optional[str] = None,
    product_name: Optional[str] = None,
    price_date: Optional[date] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return pricing_service.search(
        db=db,
        store_id=store_id,
        sku=sku,
        product_name=product_name,
        price_date=price_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{pricing_id}",
    response_model=PricingResponse,
)
def get_pricing(
    pricing_id: int,
    db: Session = Depends(get_db),
):
    pricing = pricing_service.repository.get_by_id(
        db=db,
        pricing_id=pricing_id,
    )

    if pricing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing record not found",
        )

    return pricing


@router.put(
    "/{pricing_id}",
    response_model=PricingResponse,
)
def update_pricing(
    pricing_id: int,
    pricing_data: PricingUpdate,
    db: Session = Depends(get_db),
):
    pricing = pricing_service.update_price(
        db=db,
        pricing_id=pricing_id,
        pricing_data=pricing_data,
    )

    if pricing is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pricing record was modified by another user or does not exist",
        )

    return pricing