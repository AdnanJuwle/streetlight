"""Quick test to verify data and API endpoints"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from models.database import SessionLocal, Device, SensorData, Alert, MLPrediction

def test_data():
    """Test if data exists in database"""
    db = SessionLocal()
    
    try:
        devices = db.query(Device).all()
        print(f"Devices in database: {len(devices)}")
        for device in devices:
            print(f"  - {device.id}: {device.name}")
        
        sensor_data = db.query(SensorData).count()
        print(f"\nSensor data records: {sensor_data}")
        
        alerts = db.query(Alert).filter(Alert.status == 'open').all()
        print(f"Open alerts: {len(alerts)}")
        for alert in alerts:
            print(f"  - {alert.alert_type}: {alert.message}")
        
        predictions = db.query(MLPrediction).count()
        print(f"\nML predictions: {predictions}")
        
        latest_predictions = db.query(MLPrediction).order_by(MLPrediction.timestamp.desc()).limit(5).all()
        print(f"Latest predictions:")
        for pred in latest_predictions:
            print(f"  - {pred.device_id}: {pred.prediction_type} = {pred.prediction_value}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_data()

