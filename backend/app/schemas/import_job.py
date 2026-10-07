from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ImportJobResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    status: str
    total_rows: int
    processed_rows: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
