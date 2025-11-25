# Quick Start Guide

## 🚀 Get Started in 5 Steps

### 1. Prerequisites
```bash
# Install these first:
- Python 3.9+
- PostgreSQL
- Node.js 18+
- Git
```

### 2. Database Setup (5 minutes)
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE streetlight_db;
CREATE USER streetlight WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE streetlight_db TO streetlight;
\q

# Update backend/.env
DATABASE_URL=postgresql://streetlight:your_password@localhost:5432/streetlight_db
```

### 3. Backend Setup (5 minutes)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -c "from models.database import init_db; init_db()"
uvicorn main:app --reload
```

### 4. Frontend Setup (3 minutes)
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

### 5. Test It
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Health check: http://localhost:8000/health

## 📋 What Each Component Does

### Arduino (`finalver.ino`)
- Reads sensors every 5 seconds
- Outputs JSON to Serial port
- Controls lights based on motion

### Bridge Service (`bridge_service/`)
- Reads Arduino Serial
- Sends to backend API
- Runs on ESP32/Raspberry Pi

### Backend (`backend/`)
- Receives sensor data
- Stores in database
- Runs ML predictions
- Provides REST API

### Frontend (`frontend/`)
- Shows real-time dashboard
- Displays map and charts
- Manages alerts

### ML Pipeline (`ml_pipeline/`)
- Collects training data
- Engineers features
- Trains models
- Makes predictions

## 🎯 Current Status

✅ **Completed**: Code written, architecture designed
⚠️ **In Progress**: Need hardware setup, data collection
❌ **Not Started**: Model training, deployment

## 📅 Timeline

- **Week 1-2**: Hardware setup
- **Week 3-6**: Data collection (2-4 weeks)
- **Week 7**: ML model training
- **Week 8**: Frontend deployment
- **Week 9**: Testing
- **Week 10**: Production features

## 🔧 Next Steps

1. **This Week**: Set up database and test backend/frontend locally
2. **Next Week**: Get ESP32/Raspberry Pi and set up hardware
3. **Next Month**: Collect data and train ML models
4. **Month 2**: Deploy and optimize

## 📚 Full Documentation

See `PROJECT_GUIDE.md` for complete details on:
- Every file explained
- All algorithms and models
- Step-by-step completion guide
- Technical complexities
- Testing strategies

## 🆘 Common Issues

**Backend won't start?**
- Check PostgreSQL is running
- Check database credentials in `.env`

**Frontend shows errors?**
- Check backend is running on port 8000
- Check API URL in `.env.local`

**No data in database?**
- Check bridge service is running
- Check Arduino is connected
- Check serial port in bridge service

## 💡 Key Concepts

- **Time-series data**: Sensor readings over time
- **ML predictions**: Failure probability, anomaly detection
- **Real-time processing**: Data flows Arduino → Bridge → Backend → Dashboard
- **Feature engineering**: Creating ML features from raw sensor data

---

**Need help?** Check `PROJECT_GUIDE.md` for detailed explanations!

