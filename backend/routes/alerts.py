"""
API routes for alert management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from models.database import get_session
from schemas import AlertResponse
from services.data_service import AlertService

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


def get_db():
    """Dependency for database session"""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all alerts with optional filters"""
    return AlertService.get_alerts(db, device_id=device_id, status=status, limit=limit)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific alert"""
    alert = AlertService.get_alerts(db, limit=1)
    # In production, add get_alert_by_id method
    alerts = AlertService.get_alerts(db, limit=1000)
    alert = next((a for a in alerts if a.id == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Mark an alert as resolved"""
    alert = AlertService.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

