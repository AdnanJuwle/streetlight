# Frontend Setup & Testing Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Frontend

```bash
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### 3. Make Sure Backend is Running

The frontend connects to the backend API at `http://localhost:8000` by default.

Start the backend if not already running:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing the ML Predictions

### Step 1: Train the Model

First, train the fault prediction model:

```bash
cd ml_pipeline
python model_training.py --data ../data/training_data.csv --model-type fault --fault-model-type logistic
```

### Step 2: View Predictions in Frontend

1. Open http://localhost:3000 in your browser
2. You'll see the dashboard with:
   - **Device Map**: Shows all streetlight devices on a map
   - **Active Alerts**: Shows any fault alerts
   - **Devices List**: Table of all devices with their status
3. **Click on a device** (e.g., `streetlight-001`) to see:
   - **Statistics**: 24-hour statistics
   - **Real-time Data**: Live sensor data charts
   - **ML Predictions**: ⭐ NEW! Shows fault, failure, and anomaly predictions

### Step 3: Understanding ML Predictions Panel

The ML Predictions panel shows:
- **Fault Prediction**: Probability of fault based on light dampness and relay delay
  - Green: Low probability (< 40%)
  - Orange: Medium probability (40-70%)
  - Red: High probability (> 70%) - triggers alert
- **Failure Prediction**: General failure probability
- **Anomaly Detection**: Unusual patterns detected

### Step 4: Test with New Data

Send test sensor data to see predictions update:

```bash
# Example: Send sensor data via API
curl -X POST "http://localhost:8000/api/v1/devices/streetlight-001/data" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": 1704288000000,
    "ambient_light": 45.5,
    "ambient_light_raw": 468,
    "gps": {"valid": true, "latitude": 40.7128, "longitude": -74.0060},
    "lights": [
      {
        "id": 1,
        "ldr_value": 55.0,
        "ldr_raw": 567,
        "ir_sensor": true,
        "light_state": true,
        "fault_detected": false,
        "sms_sent": false
      }
    ],
    "system": {"is_dark": true, "active_lights": 1, "faulty_lights": 0}
  }'
```

The frontend will automatically refresh every 5-10 seconds to show new predictions.

## Frontend Features

### Dashboard Components

1. **Device Map** (`DeviceMap.tsx`)
   - Interactive map showing device locations
   - Click markers to select devices
   - Color-coded by status

2. **Device List** (`DeviceList.tsx`)
   - Table of all devices
   - Shows active lights, faulty lights, ambient light
   - Click row to select device

3. **Statistics Panel** (`StatisticsPanel.tsx`)
   - 24-hour statistics for selected device
   - Total readings, average ambient light
   - Max faulty lights, average active lights

4. **Real-time Chart** (`RealTimeChart.tsx`)
   - Live sensor data visualization
   - Updates every 5 seconds

5. **Alerts Panel** (`AlertsPanel.tsx`)
   - Shows active alerts
   - Can resolve alerts
   - Color-coded by severity

6. **ML Predictions Panel** (`MLPredictionsPanel.tsx`) ⭐ NEW
   - Shows latest ML predictions
   - Fault probability with color coding
   - Warning when high fault probability detected
   - Updates every 10 seconds

## API Integration

The frontend uses the API client in `frontend/src/lib/api.ts` which connects to:
- `http://localhost:8000` (default)
- Can be changed via `NEXT_PUBLIC_API_URL` environment variable

### Available API Methods

- `api.getDevices()` - Get all devices
- `api.getLatestData(deviceId)` - Get latest sensor data
- `api.getAlerts()` - Get alerts
- `api.getMLPredictions(deviceId)` - Get ML predictions ⭐ NEW
- `api.getLatestMLPrediction(deviceId)` - Get latest prediction ⭐ NEW

## Troubleshooting

### Frontend won't start
- Make sure Node.js is installed: `node --version`
- Install dependencies: `npm install`
- Check for port conflicts (default: 3000)

### No predictions showing
- Make sure the model is trained (see MODEL_TRAINING_GUIDE.md)
- Check backend is running and accessible
- Check browser console for errors
- Verify model files exist in `ml_pipeline/models/`

### API connection errors
- Verify backend is running on port 8000
- Check CORS settings in backend
- Verify `NEXT_PUBLIC_API_URL` if using custom URL

## Next Steps

1. ✅ Frontend is ready to test
2. Train the model (see MODEL_TRAINING_GUIDE.md)
3. View predictions in the dashboard
4. Monitor devices and alerts in real-time

