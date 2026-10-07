from app.db.database import Base, engine
from app.models.import_job import ImportJob
from app.models.pricing import Pricing


def init_db() -> None:
    Base.metadata.create_all(bind=engine)