from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """
    Create database tables for local development.

    For now this is enough.
    Later we should move to Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)