# 🚀 Quick Start Guide

## Step 1: Start the Backend Server

**Option A: Using the batch file (Windows)**
```bash
start_backend.bat
```

**Option B: Manual start**
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 2: Start the Frontend

Open a **new terminal** and run:
```bash
cd frontend
npm run dev
```

## Step 3: Open the Dashboard

Open your browser to: **http://localhost:3000**

## ✅ Verify Everything Works

1. **Check Backend**: http://localhost:8000/health
   - Should return: `{"status":"healthy",...}`

2. **Check API**: http://localhost:8000/api/v1/devices
   - Should return a list of 4 devices

3. **Check Frontend**: http://localhost:3000
   - Should show 4 devices, alerts, and map

## 🐛 Troubleshooting

### No devices showing?
- Make sure backend is running (check http://localhost:8000/health)
- Check browser console (F12) for errors
- Verify data exists: `python backend/test_api.py`

### Backend won't start?
- Make sure dependencies are installed: `pip install -r backend/requirements.txt`
- Check if port 8000 is already in use
- Look for error messages in the terminal

### Frontend shows connection error?
- Backend must be running first
- Check that backend is on http://localhost:8000
- Verify CORS is enabled (it should be by default)

## 📊 Demo Data

If you need to recreate demo data:
```bash
python backend/create_demo_data.py
```

This creates:
- 4 devices with locations
- Recent sensor data (50 readings each)
- ML predictions (fault, failure, anomaly)
- Alerts from predictions

