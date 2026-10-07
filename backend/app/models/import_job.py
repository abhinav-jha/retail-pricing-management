from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="queued",
        index=True,
    )

    total_rows: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    processed_rows: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
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
