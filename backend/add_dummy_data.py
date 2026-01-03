"""
Script to add dummy sensor data for testing and model training
"""

import sys
import os
from datetime import datetime, timedelta
import random
import json

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.database import SessionLocal, Device, SensorData, init_db

def generate_dummy_sensor_data(device_id: str, num_readings: int = 500):
    """Generate dummy sensor data with realistic patterns"""
    
    db = SessionLocal()
    
    try:
        # Create or get device
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            device = Device(
                id=device_id,
                name=f"Streetlight {device_id}",
                location_name="Test Location",
                latitude=40.7128 + random.uniform(-0.01, 0.01),
                longitude=-74.0060 + random.uniform(-0.01, 0.01),
                status="active"
            )
            db.add(device)
            db.commit()
            db.refresh(device)
        
        # Generate data for the past 7 days
        base_time = datetime.utcnow()
        readings = []
        
        for i in range(num_readings):
            # Time decreases as we go back in history
            timestamp = base_time - timedelta(seconds=i * 300)  # 5 minute intervals
            
            # Simulate day/night cycle
            hour = timestamp.hour
            is_night = hour >= 20 or hour <= 6
            is_dark = is_night or random.random() < 0.3  # Sometimes dark during day
            
            # Ambient light (LDR1) - lower at night
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
                # IR sensor detects vehicle (more likely at night)
                ir_detected = is_dark and random.random() < 0.4
                
                # Light should be on if dark and IR detected
                should_be_on = is_dark and ir_detected
                
                # Simulate relay aging - delay increases over time for some lights
                relay_age_factor = (num_readings - i) / num_readings  # Older data = more aging
                has_aging = light_id in [2, 3]  # Lights 2 and 3 have aging issues
                
                if should_be_on:
                    # Simulate delay for aging relays
                    if has_aging and random.random() < 0.6:
                        # Delayed turn-on
                        light_state = 1 if random.random() < 0.7 else 0
                    else:
                        # Normal turn-on
                        light_state = 1
                else:
                    light_state = 0
                
                # LDR2 reading (light intensity under the light)
                if light_state == 1:
                    # Light is on - LDR should be low (more light = lower value)
                    # But simulate dampness for some lights
                    has_dampness = light_id == 3  # Light 3 has dampness issue
                    if has_dampness and random.random() < 0.5:
                        # High LDR = less light detected = dampness
                        ldr_value = random.uniform(40, 70)
                    else:
                        # Normal light output
                        ldr_value = random.uniform(10, 30)
                else:
                    # Light is off - LDR reads ambient
                    ldr_value = ambient_light + random.uniform(-5, 5)
                
                ldr_raw = int(ldr_value * 10.3)
                
                # Fault detection: light should be on but LDR shows it's not bright enough
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
            
            # Create sensor data entry
            sensor_data = SensorData(
                device_id=device_id,
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
        
        # Add all readings to database
        db.add_all(readings)
        db.commit()
        
        print(f"[OK] Added {num_readings} sensor readings for device {device_id}")
        print(f"  Time range: {readings[-1].timestamp} to {readings[0].timestamp}")
        print(f"  Active lights: {active_count} (avg)")
        print(f"  Faulty lights: {faulty_count} (avg)")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Main function to add dummy data"""
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    
    print("\nGenerating dummy sensor data...")
    print("-" * 50)
    
    # Add data for a test device
    device_id = "streetlight-001"
    num_readings = 500  # ~7 days of data at 5-minute intervals
    
    generate_dummy_sensor_data(device_id, num_readings)
    
    print("-" * 50)
    print("Dummy data generation complete!")
    print(f"\nYou can now:")
    print(f"  1. Train the model: python ml_pipeline/model_training.py --data data/training_data.csv --model-type fault")
    print(f"  2. Or collect data first: python ml_pipeline/data_collection.py --device-id {device_id} --output data/training_data.csv")


if __name__ == "__main__":
    main()

