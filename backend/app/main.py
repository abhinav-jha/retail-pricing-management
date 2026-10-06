from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import engine

app = FastAPI(
    title="Retail Pricing Management API",
    version="1.0.0",
)


@app.get("/api/v1/health")
def health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": result.scalar(),
    }