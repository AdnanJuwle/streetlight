# Quick Start: Frontend Testing

## 🚀 Start the Frontend (3 Steps)

### Step 1: Install Dependencies
```bash
cd frontend
npm install
```

### Step 2: Start Frontend Server
```bash
npm run dev
```

### Step 3: Open Browser
Open **http://localhost:3000** in your browser

## ✅ What You'll See

1. **Device Map** - Interactive map with streetlight locations
2. **Active Alerts** - Any fault alerts from the system
3. **Devices List** - Table showing all devices
4. **ML Predictions Panel** - ⭐ NEW! Shows fault predictions when you select a device

## 📊 Testing ML Predictions

### Before Testing:
1. Make sure backend is running: `python -m uvicorn backend.main:app --port 8000`
2. Train the model (if not done):
   ```bash
   python ml_pipeline/model_training.py --data data/training_data.csv --model-type fault --fault-model-type logistic
   ```

### How to Test:
1. Click on a device in the list (e.g., `streetlight-001`)
2. Scroll down to see **ML Predictions Panel**
3. You'll see:
   - **Fault Probability** (color-coded: green/orange/red)
   - **Failure Probability**
   - **Anomaly Detection**
4. If fault probability > 70%, you'll see a warning alert

## 🎯 Features to Test

- ✅ Device selection and details
- ✅ Real-time sensor data charts
- ✅ Statistics panel
- ✅ ML predictions display
- ✅ Alert notifications
- ✅ Auto-refresh (updates every 5-10 seconds)

## 🔗 Repository

Code is pushed to: **https://github.com/AdnanJuwle/streetlight.git**

