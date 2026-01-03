"""
Create comprehensive demo data: devices, sensor data, ML predictions, and alerts
"""

import sys
import os
from datetime import datetime, timedelta
import random
import json

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.database import SessionLocal, Device, SensorData, MLPrediction, Alert, init_db

def create_devices():
    """Create multiple demo devices"""
    db = SessionLocal()
    
    devices_data = [
        {
            "id": "streetlight-001",
            "name": "Main Street Light 1",
            "location_name": "Main Street & 1st Avenue",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        {
            "id": "streetlight-002",
            "name": "Park Avenue Light",
            "location_name": "Park Avenue & 5th Street",
            "latitude": 40.7580,
            "longitude": -73.9855,
        },
        {
            "id": "streetlight-003",
            "name": "Highway Exit Light",
            "location_name": "Highway 101 Exit 15",
            "latitude": 40.7614,
            "longitude": -73.9776,
        },
        {
            "id": "streetlight-004",
            "name": "Residential Area Light",
            "location_name": "Oak Street Residential",
            "latitude": 40.7505,
            "longitude": -73.9934,
        },
    ]
    
    device_ids = []
    for device_data in devices_data:
        device = db.query(Device).filter(Device.id == device_data["id"]).first()
        if not device:
            device = Device(
                id=device_data["id"],
                name=device_data["name"],
                location_name=device_data["location_name"],
                latitude=device_data["latitude"],
                longitude=device_data["longitude"],
                status="active"
            )
            db.add(device)
        device_ids.append(device_data["id"])
    
    db.commit()
    print(f"[OK] Created/updated {len(device_ids)} devices")
    return device_ids


def create_recent_sensor_data(device_id: str, num_readings: int = 50):
    """Create recent sensor data (last few hours)"""
    db = SessionLocal()
    
    try:
        # Get device from database
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            print(f"  [ERROR] Device {device_id} not found")
            return
        
        base_time = datetime.utcnow()
        readings = []
        
        for i in range(num_readings):
            # Recent data - going back from now
            timestamp = base_time - timedelta(minutes=i * 5)  # 5 minute intervals
            
            # Simulate day/night cycle
            hour = timestamp.hour
            is_night = hour >= 20 or hour <= 6
            is_dark = is_night or random.random() < 0.2
            
            # Ambient light
            if is_night:
                ambient_light = random.uniform(30, 80)
            else:
                ambient_light = random.uniform(10, 30)
            
            ambient_light_raw = int(ambient_light * 10.3)
            
            # Generate data for 4 lights
            lights = []
            active_count = 0
            faulty_count = 0
            
            for light_id in range(1, 5):
                ir_detected = is_dark and random.random() < 0.4
                should_be_on = is_dark and ir_detected
                
                # Simulate some issues
                has_issue = (device_id == "streetlight-001" and light_id == 3) or \
                           (device_id == "streetlight-002" and light_id in [2, 4])
                
                if should_be_on:
                    if has_issue and random.random() < 0.7:
                        light_state = 1 if random.random() < 0.6 else 0  # Sometimes fails
                    else:
                        light_state = 1
                else:
                    light_state = 0
                
                # LDR2 reading
                if light_state == 1:
                    if has_issue:
                        # High LDR = dampness issue
                        ldr_value = random.uniform(50, 75)
                    else:
                        ldr_value = random.uniform(10, 30)
                else:
                    ldr_value = ambient_light + random.uniform(-5, 5)
                
                ldr_raw = int(ldr_value * 10.3)
                fault_detected = (light_state == 1 and ldr_value > 50)
                
                if light_state == 1:
                    active_count += 1
                if fault_detected:
                    faulty_count += 1
                
                lights.append({
                    "id": light_id,
                    "ldr_value": round(ldr_value, 2),
                    "ldr_raw": ldr_raw,
                    "ir_sensor": ir_detected,
                    "light_state": bool(light_state),
                    "fault_detected": fault_detected,
                    "sms_sent": False
                })
            
            sensor_data = SensorData(
                device_id=device.id,
                timestamp=timestamp,
                ambient_light=round(ambient_light, 2),
                ambient_light_raw=ambient_light_raw,
                gps_latitude=device.latitude,
                gps_longitude=device.longitude,
                gps_valid=True,
                lights_data=json.dumps(lights),
                is_dark=is_dark,
                active_lights_count=active_count,
                faulty_lights_count=faulty_count
            )
            
            readings.append(sensor_data)
        
        db.add_all(readings)
        db.commit()
        print(f"  [OK] Added {num_readings} recent sensor readings for {device_id}")
        
    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Failed to add data for {device_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def create_ml_predictions_and_alerts(device_id: str):
    """Create ML predictions and alerts"""
    db = SessionLocal()
    
    try:
        # Get device from database
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            print(f"  [ERROR] Device {device_id} not found")
            return
        
        # Create fault predictions with varying probabilities
        if device_id == "streetlight-001":
            # High fault probability - should create alert
            fault_prob = random.uniform(0.75, 0.95)
        elif device.id == "streetlight-002":
            # Medium fault probability
            fault_prob = random.uniform(0.50, 0.70)
        else:
            # Low fault probability
            fault_prob = random.uniform(0.10, 0.40)
        
        # Create fault prediction
        fault_pred = MLPrediction(
            device_id=device.id,
            prediction_type='fault',
            timestamp=datetime.utcnow(),
            prediction_value=fault_prob,
            prediction_label='fault' if fault_prob > 0.5 else 'normal',
            confidence=fault_prob,
            model_name='fault_predictor',
            model_version='1.0',
            features=json.dumps({
                'dampness': {'light_3_dampness': 65.5} if device.id == "streetlight-001" else {},
                'delay': {'light_2_turn_on_delay': 3.2} if device.id == "streetlight-002" else {}
            })
        )
        db.add(fault_pred)
        
        # Create failure prediction
        failure_prob = random.uniform(0.20, 0.60)
        failure_pred = MLPrediction(
            device_id=device.id,
            prediction_type='failure',
            timestamp=datetime.utcnow(),
            prediction_value=failure_prob,
            prediction_label='failure' if failure_prob > 0.5 else 'normal',
            confidence=failure_prob,
            model_name='failure_predictor',
            model_version='1.0'
        )
        db.add(failure_pred)
        
        # Create anomaly detection
        is_anomaly = random.random() < 0.3
        anomaly_pred = MLPrediction(
            device_id=device.id,
            prediction_type='anomaly',
            timestamp=datetime.utcnow(),
            prediction_value=-0.5 if is_anomaly else 0.2,
            prediction_label='anomaly' if is_anomaly else 'normal',
            confidence=abs(-0.5 if is_anomaly else 0.2),
            model_name='anomaly_detector',
            model_version='1.0'
        )
        db.add(anomaly_pred)
        
        # Create alert if fault probability is high
        if fault_prob > 0.7:
            existing_alert = db.query(Alert).filter(
                Alert.device_id == device.id,
                Alert.alert_type == 'fault_prediction',
                Alert.status == 'open'
            ).first()
            
            if not existing_alert:
                alert = Alert(
                    device_id=device.id,
                    alert_type='fault_prediction',
                    severity='high',
                    message=f"Fault predicted with {fault_prob:.1%} probability. "
                           f"High light dampness detected (LDR2: 65.5). "
                           f"Relay delay: 3.2s. Maintenance recommended.",
                    latitude=device.latitude,
                    longitude=device.longitude
                )
                db.add(alert)
                print(f"  [OK] Created fault prediction alert for {device.id}")
        
        # Create some regular fault alerts
        if device.id in ["streetlight-001", "streetlight-002"]:
            for light_id in [2, 3]:
                existing_alert = db.query(Alert).filter(
                    Alert.device_id == device.id,
                    Alert.light_id == light_id,
                    Alert.alert_type == 'fault',
                    Alert.status == 'open'
                ).first()
                
                if not existing_alert:
                    alert = Alert(
                        device_id=device.id,
                        alert_type='fault',
                        severity='high',
                        message=f"Fault detected in light {light_id}",
                        light_id=light_id,
                        latitude=device.latitude,
                        longitude=device.longitude
                    )
                    db.add(alert)
                    print(f"  [OK] Created fault alert for {device.id} light {light_id}")
        
        db.commit()
        print(f"  [OK] Created ML predictions for {device.id}")
        
    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Failed to create predictions for {device.id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main function"""
    print("=" * 60)
    print("Creating Demo Data for Frontend")
    print("=" * 60)
    
    print("\n1. Initializing database...")
    init_db()
    
    print("\n2. Creating devices...")
    devices = create_devices()
    
    print("\n3. Creating recent sensor data...")
    for device_id in devices:
        create_recent_sensor_data(device_id, num_readings=50)
    
    print("\n4. Creating ML predictions and alerts...")
    for device_id in devices:
        create_ml_predictions_and_alerts(device_id)
    
    print("\n" + "=" * 60)
    print("Demo data creation complete!")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"  - {len(devices)} devices")
    print(f"  - Recent sensor data for all devices")
    print(f"  - ML predictions (fault, failure, anomaly)")
    print(f"  - Alerts from ML predictions")
    print(f"\nYou can now:")
    print(f"  1. View devices in frontend: http://localhost:3000")
    print(f"  2. See ML predictions in the dashboard")
    print(f"  3. View alerts in the alerts panel")


if __name__ == "__main__":
    main()

