from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    All SQLAlchemy models should inherit from this class.
    """
    pass