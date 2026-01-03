# Quick Start: Hardware Integration

## 🚀 3-Step Setup

### Step 1: Upload Arduino Code

1. Open `finalver_enhanced.ino` in Arduino IDE
2. Connect Arduino via USB
3. Select: **Tools → Board → [Your Arduino Board]**
4. Select: **Tools → Port → [COM Port]**
5. Click **Upload**

**Verify**: Open Serial Monitor (9600 baud) - you should see JSON data every 5 seconds

### Step 2: Start Backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Start Bridge Service

**Find your COM port:**
- Windows: Device Manager → Ports → Look for "Arduino" or "USB Serial"
- Example: `COM3`, `COM4`, etc.

**Start bridge:**
```bash
cd bridge_service
pip install -r requirements.txt
python bridge_service.py --serial-port COM3 --api-url http://localhost:8000 --device-id streetlight-001
```

Replace `COM3` with your actual port.

## ✅ Verify It's Working

1. **Check Bridge Logs**: Should see "Data sent successfully"
2. **Check Backend**: http://localhost:8000/api/v1/devices/streetlight-001/data/latest
3. **Check Frontend**: http://localhost:3000 → See real-time data and ML predictions

## 📊 What Happens Automatically

1. **Arduino** sends sensor data every 5 seconds
2. **Bridge** forwards to backend API
3. **Backend** stores data and runs ML model
4. **ML Model** calculates:
   - Light dampness (LDR2 when light is on)
   - Turn-on delay (time between command and light on)
   - Failure probability
5. **Frontend** shows predictions in real-time
6. **Alerts** created if probability > 70%

## 🔧 Troubleshooting

**No data in frontend?**
- Check bridge service is running
- Verify COM port is correct
- Check backend is running
- Look at bridge service logs for errors

**Wrong COM port?**
- Windows: `COM3`, `COM4`, `COM5`, etc.
- Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`
- Mac: `/dev/tty.usbserial-*`

**ML predictions not showing?**
- Train the model first: `python ml_pipeline/fault_prediction_model.py ...`
- Check model file exists: `ml_pipeline/models/fault_predictor_simple.pkl`

