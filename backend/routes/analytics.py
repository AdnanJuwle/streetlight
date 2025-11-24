"""
API routes for advanced analytics
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from models.database import get_session
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def get_db():
    """Dependency for database session"""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/traffic/{device_id}")
async def get_traffic_patterns(
    device_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get traffic pattern analysis"""
    return AnalyticsService.analyze_traffic_patterns(db, device_id, days)


@router.get("/energy/{device_id}")
async def get_energy_consumption(
    device_id: str,
    days: int = 7,
    watts_per_light: float = 50.0,
    cost_per_kwh: float = 0.12,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get energy consumption analysis"""
    return AnalyticsService.calculate_energy_consumption(
        db, device_id, days, watts_per_light, cost_per_kwh
    )


@router.get("/optimization/{device_id}")
async def get_optimization_suggestions(
    device_id: str,
    days: int = 7,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get energy optimization suggestions"""
    return AnalyticsService.optimize_energy(db, device_id, days)


@router.get("/report/{device_id}")
async def generate_report(
    device_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Generate comprehensive analytics report"""
    return AnalyticsService.generate_report(db, device_id, days)

