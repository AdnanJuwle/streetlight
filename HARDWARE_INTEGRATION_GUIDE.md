# Hardware Integration Guide

## System Architecture

```
Arduino (Sensors) → Serial/USB → Bridge Service → Backend API → ML Model → Frontend Dashboard
```

## Hardware Setup

### Sensors Connected to Arduino

1. **LDR1 (Ambient Light Sensor)**: Pin A0
   - Detects day/night
   - Used to determine if lights should operate

2. **LDR2 Sensors (Light Level)**: Pins A1, A2, A3, A4
   - One LDR2 per light (4 lights)
   - Measures actual light output when light is on
   - Higher value = less light = more dampness

3. **IR Sensors (Vehicle Detection)**: Pins 2, 3, 4, 5
   - One IR sensor per light
   - Detects vehicles approaching
   - Triggers light to turn on

4. **Relay/Light Control**: Pins 6, 7, 8, 9
   - Controls when lights turn on/off
   - Used to measure turn-on delay

## Step-by-Step Integration

### Step 1: Upload Arduino Code

1. Open `finalver.ino` in Arduino IDE
2. Connect your Arduino via USB
3. Select the correct board and port in Arduino IDE
4. Upload the code

**Note**: The code sends JSON data every 5 seconds via Serial (9600 baud)

### Step 2: Install Bridge Service Dependencies

```bash
cd bridge_service
pip install -r requirements.txt
```

### Step 3: Start Backend Server

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4: Start Bridge Service

**On Windows:**
```bash
cd bridge_service
python bridge_service.py --serial-port COM3 --api-url http://localhost:8000 --device-id streetlight-001
```

**On Linux/Raspberry Pi:**
```bash
cd bridge_service
python bridge_service.py --serial-port /dev/ttyUSB0 --api-url http://localhost:8000 --device-id streetlight-001
```

**Find your serial port:**
- Windows: Check Device Manager → Ports (COM & LPT)
- Linux: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
- Mac: `ls /dev/tty.usb*`

### Step 5: Train the ML Model (One-time)

```bash
cd ml_pipeline
python fault_prediction_model.py --data ../data/training_data.csv --model-type logistic --look-ahead 24
```

The model will be automatically used for real-time predictions.

## Data Flow

### 1. Arduino → Bridge Service

Arduino sends JSON every 5 seconds:
```json
{
  "timestamp": 1234567890,
  "ambient_light": 45.5,
  "lights": [
    {
      "id": 1,
      "ldr_value": 25.3,      // LDR2 reading (light level)
      "ir_sensor": true,      // Vehicle detected
      "light_state": true,    // Light is on
      "fault_detected": false
    }
  ]
}
```

### 2. Bridge Service → Backend API

Bridge service:
- Reads JSON from Serial
- Adds device_id and timestamp
- Sends to: `POST /api/v1/devices/{device_id}/data`

### 3. Backend → ML Model

When data arrives:
1. Data is stored in database
2. ML service automatically:
   - Extracts light dampness (LDR2 when light is on)
   - Calculates turn-on delay (from historical data)
   - Predicts failure probability
   - Creates alert if probability > 70%

### 4. Frontend Display

- Real-time data updates every 5-10 seconds
- Shows:
  - Current sensor readings
  - ML predictions with dampness/delay values
  - Alerts for high-risk predictions

## Real-Time Prediction Process

For each sensor reading:

1. **Extract Light Dampness**:
   - When `light_state = true`, use `ldr_value` as dampness
   - Higher value = more dampness = higher failure risk

2. **Calculate Turn-on Delay**:
   - Track when IR sensor detects vehicle
   - Track when light actually turns on (state changes or LDR drops)
   - Calculate time difference = delay
   - Longer delay = relay aging = higher failure risk

3. **Predict Failure**:
   - Model takes: `(dampness, delay)`
   - Outputs: `failure_probability` (0-1)
   - If > 0.7: Alert created automatically

## Testing the Integration

### Test 1: Verify Serial Communication

```bash
# Check if Arduino is sending data
# Windows: Use PuTTY or Arduino Serial Monitor
# Linux: screen /dev/ttyUSB0 9600
```

You should see JSON data every 5 seconds.

### Test 2: Verify Bridge Service

Check bridge service logs:
```
INFO - Connected to Arduino on COM3
INFO - Data sent successfully: 1234567890
```

### Test 3: Verify Backend Receives Data

```bash
curl http://localhost:8000/api/v1/devices/streetlight-001/data/latest
```

Should return the latest sensor data.

### Test 4: Verify ML Predictions

```bash
curl http://localhost:8000/api/v1/ml/predictions/streetlight-001/latest
```

Should return fault prediction with dampness and delay values.

### Test 5: Check Frontend

Open http://localhost:3000 and:
- See device in the list
- Click device → See ML predictions
- View dampness and delay values
- See alerts if probability > 70%

## Troubleshooting

### Arduino not sending data?
- Check Serial Monitor in Arduino IDE
- Verify baud rate is 9600
- Check wiring connections

### Bridge service can't connect?
- Verify serial port name (COM3, /dev/ttyUSB0, etc.)
- Check if another program is using the port
- Try different baud rates if needed

### No ML predictions?
- Make sure model is trained: `python ml_pipeline/fault_prediction_model.py ...`
- Check model file exists: `ml_pipeline/models/fault_predictor_simple.pkl`
- Verify backend logs for ML errors

### Predictions seem wrong?
- Model needs training data with actual fault patterns
- Collect more data over time
- Retrain model with new data

## Enhancing Turn-on Delay Tracking

The current Arduino code measures delay, but you can enhance it:

1. **Track command time**: Record when `digitalWrite(lightPin, HIGH)` is called
2. **Track actual turn-on**: Record when LDR2 detects light (value drops)
3. **Calculate delay**: Time difference in milliseconds

This gives more accurate delay measurements for the ML model.

## Production Deployment

For production:

1. **Use ESP32/Raspberry Pi** as bridge (more reliable than direct USB)
2. **Add WiFi/Ethernet** for remote monitoring
3. **Implement data buffering** for network outages
4. **Add authentication** for API endpoints
5. **Set up monitoring** for bridge service health
6. **Schedule model retraining** with new data

## Next Steps

1. ✅ Connect hardware sensors
2. ✅ Upload Arduino code
3. ✅ Start bridge service
4. ✅ Verify data flow
5. ✅ Train ML model
6. ✅ Monitor predictions in dashboard

