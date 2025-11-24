"""
API routes for device management and data ingestion
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from models.database import get_session
from schemas import (
    SensorDataCreate, SensorDataResponse,
    DeviceCreate, DeviceResponse,
    AlertResponse
)
from services.data_service import DataService, DeviceService, AlertService

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


def get_db():
    """Dependency for database session"""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{device_id}/data", response_model=SensorDataResponse, status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data(
    device_id: str,
    data: SensorDataCreate,
    db: Session = Depends(get_db)
):
    """Ingest sensor data from a device"""
    # Ensure device exists
    DeviceService.get_or_create_device(db, device_id)
    
    # Store sensor data
    sensor_data = DataService.create_sensor_data(db, data, device_id)
    
    return sensor_data


@router.get("/{device_id}/data/latest", response_model=SensorDataResponse)
async def get_latest_data(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get latest sensor data for a device"""
    data = DataService.get_latest_data(db, device_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for device")
    return data


@router.get("/{device_id}/data/historical", response_model=List[SensorDataResponse])
async def get_historical_data(
    device_id: str,
    hours: int = 24,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get historical sensor data"""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    data = DataService.get_historical_data(db, device_id, start_time=start_time, limit=limit)
    return data


@router.get("/{device_id}/statistics")
async def get_device_statistics(
    device_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get device statistics"""
    stats = DataService.get_device_statistics(db, device_id, hours)
    return stats


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db)
):
    """Create or update a device"""
    device_obj = DeviceService.get_or_create_device(
        db,
        device.id,
        name=device.name,
        location_name=device.location_name,
        latitude=device.latitude,
        longitude=device.longitude,
        status=device.status
    )
    return device_obj


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get device information"""
    device = DeviceService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("", response_model=List[DeviceResponse])
async def get_all_devices(
    db: Session = Depends(get_db)
):
    """Get all devices"""
    return DeviceService.get_all_devices(db)


@router.get("/{device_id}/alerts", response_model=List[AlertResponse])
async def get_device_alerts(
    device_id: str,
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get alerts for a device"""
    return AlertService.get_alerts(db, device_id=device_id, status=status, limit=limit)

