from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.imports import router as imports_router
from app.api.routes.decisions import router as decisions_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.reconciliation import router as reconciliation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(imports_router)
api_router.include_router(decisions_router)
api_router.include_router(metrics_router)
api_router.include_router(reconciliation_router)

