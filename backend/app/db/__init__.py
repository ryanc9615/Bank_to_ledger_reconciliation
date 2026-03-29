from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy metadata registers them
from app.models.raw_import_file import RawImportFile # noqa: F401
from app.models.bank_transaction import BankTransaction #noqa: F401
from app.models.payment_record import PaymentRecord # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)