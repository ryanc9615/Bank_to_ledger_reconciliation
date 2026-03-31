from app.db.base import Base
from app.db.session import engine

# Import models so SQLAlchemy metadata registers them
from app.models.raw_import_file import RawImportFile # noqa: F401
from app.models.bank_transaction import BankTransaction #noqa: F401
from app.models.payment_record import PaymentRecord # noqa: F401
from app.models.reconciliation_run import ReconciliationRun # nopa: F401
from app.models.match_candidate import MatchCandidate # nopa: F401
from app.models.candidate_feature import CandidateFeature # nopa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)