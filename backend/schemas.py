"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LightData(BaseModel):
    """Individual light sensor data"""
    id: int
    ldr_value: float
    ldr_raw: int
    ir_sensor: bool
    light_state: bool
    fault_detected: bool
    sms_sent: bool


class GPSData(BaseModel):
    """GPS location data"""
    valid: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SystemStatus(BaseModel):
    """System status information"""
    is_dark: bool
    active_lights: int
    faulty_lights: int


class SensorDataCreate(BaseModel):
    """Schema for incoming sensor data from devices"""
    timestamp: int
    time_string: Optional[str] = None
    ambient_light: float
    ambient_light_raw: int
    gps: GPSData
    lights: List[LightData]
    system: SystemStatus
    device_id: Optional[str] = None
    received_at: Optional[str] = None


class SensorDataResponse(BaseModel):
    """Schema for sensor data response"""
    id: int
    device_id: str
    timestamp: datetime
    ambient_light: Optional[float]
    ambient_light_raw: Optional[int]
    gps_latitude: Optional[float]
    gps_longitude: Optional[float]
    gps_valid: bool
    is_dark: Optional[bool]
    active_lights_count: Optional[int]
    faulty_lights_count: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    """Schema for creating a device"""
    id: str = Field(..., description="Unique device identifier")
    name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = "active"
    configuration: Optional[Dict[str, Any]] = None


class DeviceResponse(BaseModel):
    """Schema for device response"""
    id: str
    name: Optional[str]
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    """Schema for creating an alert"""
    device_id: str
    alert_type: str
    severity: str = "medium"
    message: str
    light_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: int
    device_id: str
    alert_type: str
    severity: str
    message: str
    light_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class MLPredictionResponse(BaseModel):
    """Schema for ML prediction response"""
    id: int
    device_id: str
    prediction_type: str
    timestamp: datetime
    prediction_value: Optional[float]
    prediction_label: Optional[str]
    confidence: Optional[float]
    model_version: Optional[str]
    model_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    version: str = "1.0.0"


