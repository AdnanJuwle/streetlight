"""
Service layer for data operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

from models.database import SensorData, Device, Alert
from schemas import SensorDataCreate, AlertCreate
from services.ml_service import MLService


class DataService:
    """Service for handling sensor data operations"""
    
    @staticmethod
    def create_sensor_data(db: Session, data: SensorDataCreate, device_id: str) -> SensorData:
        """Create and store sensor data"""
        # Convert timestamp from milliseconds to datetime
        timestamp = datetime.fromtimestamp(data.timestamp / 1000.0)
        
        # Convert lights data to JSON string
        lights_json = json.dumps([light.dict() for light in data.lights])
        
        sensor_data = SensorData(
            device_id=device_id,
            timestamp=timestamp,
            ambient_light=data.ambient_light,
            ambient_light_raw=data.ambient_light_raw,
            gps_latitude=data.gps.latitude if data.gps.valid else None,
            gps_longitude=data.gps.longitude if data.gps.valid else None,
            gps_valid=data.gps.valid,
            lights_data=lights_json,
            is_dark=data.system.is_dark,
            active_lights_count=data.system.active_lights,
            faulty_lights_count=data.system.faulty_lights
        )
        
        db.add(sensor_data)
        db.commit()
        db.refresh(sensor_data)
        
        # Check for faults and create alerts
        DataService._check_and_create_alerts(db, sensor_data, data)
        
        # Generate ML predictions
        try:
            ml_service = MLService()
            sensor_dict = {
                'ambient_light': data.ambient_light,
                'ambient_light_raw': data.ambient_light_raw,
                'active_lights_count': data.system.active_lights,
                'faulty_lights_count': data.system.faulty_lights,
                'is_dark': data.system.is_dark,
            }
            ml_service.generate_predictions(db, device_id, sensor_dict)
        except Exception as e:
            # Log but don't fail if ML service is unavailable
            import logging
            logging.getLogger(__name__).warning(f"ML prediction failed: {e}")
        
        return sensor_data
    
    @staticmethod
    def _check_and_create_alerts(db: Session, sensor_data: SensorData, data: SensorDataCreate):
        """Check for faults and create alerts if needed"""
        for light in data.lights:
            if light.fault_detected:
                # Check if alert already exists for this light
                existing_alert = db.query(Alert).filter(
                    Alert.device_id == sensor_data.device_id,
                    Alert.light_id == light.id,
                    Alert.status == 'open',
                    Alert.alert_type == 'fault'
                ).first()
                
                if not existing_alert:
                    alert = Alert(
                        device_id=sensor_data.device_id,
                        alert_type='fault',
                        severity='high',
                        message=f"Fault detected in light {light.id}",
                        light_id=light.id,
                        latitude=sensor_data.gps_latitude,
                        longitude=sensor_data.gps_longitude
                    )
                    db.add(alert)
        
        db.commit()
    
    @staticmethod
    def get_latest_data(db: Session, device_id: str) -> Optional[SensorData]:
        """Get latest sensor data for a device"""
        return db.query(SensorData).filter(
            SensorData.device_id == device_id
        ).order_by(desc(SensorData.timestamp)).first()
    
    @staticmethod
    def get_historical_data(
        db: Session,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[SensorData]:
        """Get historical sensor data"""
        query = db.query(SensorData).filter(SensorData.device_id == device_id)
        
        if start_time:
            query = query.filter(SensorData.timestamp >= start_time)
        if end_time:
            query = query.filter(SensorData.timestamp <= end_time)
        
        return query.order_by(desc(SensorData.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_device_statistics(db: Session, device_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get device statistics for the last N hours"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        stats = db.query(
            func.count(SensorData.id).label('total_readings'),
            func.avg(SensorData.ambient_light).label('avg_ambient_light'),
            func.max(SensorData.faulty_lights_count).label('max_faulty_lights'),
            func.avg(SensorData.active_lights_count).label('avg_active_lights')
        ).filter(
            SensorData.device_id == device_id,
            SensorData.timestamp >= start_time
        ).first()
        
        return {
            'total_readings': stats.total_readings or 0,
            'avg_ambient_light': float(stats.avg_ambient_light) if stats.avg_ambient_light else 0,
            'max_faulty_lights': stats.max_faulty_lights or 0,
            'avg_active_lights': float(stats.avg_active_lights) if stats.avg_active_lights else 0
        }


class DeviceService:
    """Service for device management"""
    
    @staticmethod
    def get_or_create_device(db: Session, device_id: str, **kwargs) -> Device:
        """Get existing device or create new one"""
        device = db.query(Device).filter(Device.id == device_id).first()
        
        if not device:
            device = Device(id=device_id, **kwargs)
            db.add(device)
            db.commit()
            db.refresh(device)
        
        return device
    
    @staticmethod
    def get_device(db: Session, device_id: str) -> Optional[Device]:
        """Get device by ID"""
        return db.query(Device).filter(Device.id == device_id).first()
    
    @staticmethod
    def get_all_devices(db: Session) -> List[Device]:
        """Get all devices"""
        return db.query(Device).all()
    
    @staticmethod
    def update_device(db: Session, device_id: str, **kwargs) -> Optional[Device]:
        """Update device information"""
        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            for key, value in kwargs.items():
                setattr(device, key, value)
            device.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(device)
        return device


class AlertService:
    """Service for alert management"""
    
    @staticmethod
    def get_alerts(
        db: Session,
        device_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alerts with optional filters"""
        query = db.query(Alert)
        
        if device_id:
            query = query.filter(Alert.device_id == device_id)
        if status:
            query = query.filter(Alert.status == status)
        
        return query.order_by(desc(Alert.created_at)).limit(limit).all()
    
    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Mark alert as resolved"""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        return alert

