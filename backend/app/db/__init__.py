from app.db.base import Base
from app.db.session import engine

from app.models.raw_import_file import RawImportFile  # noqa: F401
from app.models.bank_transaction import BankTransaction  # noqa: F401
from app.models.payment_record import PaymentRecord  # noqa: F401
from app.models.reconciliation_run import ReconciliationRun  # noqa: F401
from app.models.match_candidate import MatchCandidate  # noqa: F401
from app.models.candidate_feature import CandidateFeature  # noqa: F401
from app.models.match_decision import MatchDecision  # noqa: F401
from app.models.decision_audit_log import DecisionAuditLog  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)