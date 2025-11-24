"""
Database models for Smart Streetlight System
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class Device(Base):
    """Device/Streetlight metadata"""
    __tablename__ = 'devices'
    
    id = Column(String, primary_key=True)  # device_id
    name = Column(String, nullable=True)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default='active')  # active, inactive, maintenance
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    configuration = Column(Text, nullable=True)  # JSON configuration
    
    # Relationships
    sensor_data = relationship("SensorData", back_populates="device")
    alerts = relationship("Alert", back_populates="device")
    ml_predictions = relationship("MLPrediction", back_populates="device")


class SensorData(Base):
    """Time-series sensor data from devices"""
    __tablename__ = 'sensor_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    ambient_light = Column(Float, nullable=True)
    ambient_light_raw = Column(Integer, nullable=True)
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    gps_valid = Column(Boolean, default=False)
    
    # Light-specific data stored as JSON in database
    lights_data = Column(Text, nullable=True)  # JSON array of light data
    
    # System status
    is_dark = Column(Boolean, nullable=True)
    active_lights_count = Column(Integer, nullable=True)
    faulty_lights_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("Device", back_populates="sensor_data")
    
    # Index for time-series queries
    __table_args__ = (
        Index('idx_device_timestamp', 'device_id', 'timestamp'),
    )


class Alert(Base):
    """Alerts and notifications"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id'), nullable=False, index=True)
    alert_type = Column(String, nullable=False)  # fault, maintenance, anomaly, etc.
    severity = Column(String, default='medium')  # low, medium, high, critical
    message = Column(Text, nullable=False)
    light_id = Column(Integer, nullable=True)  # Which light (1-4) if applicable
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default='open')  # open, acknowledged, resolved
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")


class MLPrediction(Base):
    """ML model predictions and scores"""
    __tablename__ = 'ml_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id'), nullable=False, index=True)
    prediction_type = Column(String, nullable=False)  # failure, anomaly, maintenance
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Prediction results
    prediction_value = Column(Float, nullable=True)  # Probability or score
    prediction_label = Column(String, nullable=True)  # Class label
    confidence = Column(Float, nullable=True)
    
    # Feature values used for prediction
    features = Column(Text, nullable=True)  # JSON features
    
    # Model metadata
    model_version = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("Device", back_populates="ml_predictions")
    
    # Index for time-series queries
    __table_args__ = (
        Index('idx_device_pred_timestamp', 'device_id', 'timestamp'),
    )


class MaintenanceLog(Base):
    """Maintenance history"""
    __tablename__ = 'maintenance_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id'), nullable=False, index=True)
    maintenance_type = Column(String, nullable=False)  # scheduled, emergency, predictive
    description = Column(Text, nullable=True)
    performed_by = Column(String, nullable=True)
    cost = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)


class EnergyConsumption(Base):
    """Energy consumption tracking"""
    __tablename__ = 'energy_consumption'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey('devices.id'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    active_lights_count = Column(Integer, nullable=False)
    estimated_power_watts = Column(Float, nullable=True)  # Estimated power consumption
    estimated_energy_kwh = Column(Float, nullable=True)  # Energy in kWh for the period
    cost = Column(Float, nullable=True)  # Estimated cost
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Index for time-series queries
    __table_args__ = (
        Index('idx_device_energy_timestamp', 'device_id', 'timestamp'),
    )


# Database setup
def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://streetlight:streetlight@localhost:5432/streetlight_db'
    )


def create_engine_instance():
    """Create SQLAlchemy engine"""
    database_url = get_database_url()
    return create_engine(database_url, echo=False)


def get_session_local():
    """Get database session factory"""
    engine = create_engine_instance()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create session factory
SessionLocal = get_session_local()


def init_db():
    """Initialize database tables"""
    engine = create_engine_instance()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

