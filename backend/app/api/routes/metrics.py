from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.schemas.metrics import DashboardMetricsResponse, QueueMetricsResponse, RunMetricsResponse
from app.services.metrics.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    service = MetricsService()
    return DashboardMetricsResponse(**service.get_dashboard_metrics(db))


@router.get("/runs/{run_id}", response_model=RunMetricsResponse)
def get_run_metrics(run_id: UUID, db: Session = Depends(get_db)):
    service = MetricsService()
    return RunMetricsResponse(**service.get_run_metrics(db, run_id))


@router.get("/runs/{run_id}/queues", response_model=QueueMetricsResponse)
def get_queue_metrics(run_id: UUID, db: Session = Depends(get_db)):
    service = MetricsService()
    return QueueMetricsResponse(**service.get_queue_metrics(db, run_id))