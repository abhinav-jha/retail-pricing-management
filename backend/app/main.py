from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.pricing import router as pricing_router
from app.db.database import engine
from app.db.init_db import init_db


app = FastAPI(
    title="Retail Pricing Management API",
    version="1.0.0",
)

candidates = [
    Path(__file__).resolve().parents[2] / "frontend",
    Path(__file__).resolve().parents[1] / "frontend",
    Path("/app/frontend"),
]
frontend_dir = next((path for path in candidates if path.exists()), Path(__file__).resolve().parents[1])
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def serve_frontend():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Retail pricing frontend not found"}


@app.get("/api/v1/health")
def health_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": result.scalar(),
        }
    except Exception as exc:  # pragma: no cover - runtime environment check
        return {
            "status": "degraded",
            "database": str(exc),
        }


app.include_router(pricing_router)