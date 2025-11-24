# AI-Enhanced Smart Streetlight System

A comprehensive smart city solution for intelligent streetlight monitoring, predictive maintenance, and energy optimization.

## Project Overview

This project transforms a basic Arduino-based streetlight monitoring system into an AI-powered smart city solution with:

- **Real-time Monitoring**: Live sensor data collection and visualization
- **Predictive Maintenance**: ML models to predict failures before they occur
- **Anomaly Detection**: Identify unusual patterns in sensor readings
- **Traffic Analysis**: Analyze usage patterns from IR sensors
- **Energy Optimization**: Smart recommendations for energy savings
- **Web Dashboard**: Modern React/Next.js dashboard with maps and analytics

## Architecture

```
Arduino → ESP32/RPi Bridge → Backend API → Database
                                    ↓
                              ML Inference
                                    ↓
                              Web Dashboard
```

## Project Structure

```
streetlight/
├── finalver.ino              # Enhanced Arduino code with JSON output
├── bridge_service/           # ESP32/Raspberry Pi bridge service
├── backend/                  # FastAPI backend
│   ├── models/              # Database models
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   └── main.py              # FastAPI application
├── frontend/                # Next.js web dashboard
│   └── src/
│       ├── app/             # Next.js pages
│       └── components/      # React components
└── ml_pipeline/             # ML training and inference
    ├── data_collection.py
    ├── feature_engineering.py
    ├── model_training.py
    └── inference.py
```

## Setup Instructions

### 1. Database Setup

Install PostgreSQL and create database:

```bash
createdb streetlight_db
```

Update `backend/.env` with your database credentials.

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m models.database init_db  # Initialize database tables
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000`

### 4. Bridge Service Setup

```bash
cd bridge_service
pip install -r requirements.txt
python bridge_service.py --serial-port /dev/ttyUSB0 --api-url http://localhost:8000 --device-id streetlight-001
```

### 5. ML Pipeline Setup

```bash
cd ml_pipeline
pip install -r requirements.txt

# Collect training data (after system has been running)
python data_collection.py --days 30 --output data/training_data.csv

# Train models
python model_training.py --data data/training_data.csv --model-type both
```

## API Endpoints

### Devices
- `POST /api/v1/devices/{device_id}/data` - Ingest sensor data
- `GET /api/v1/devices/{device_id}/data/latest` - Get latest data
- `GET /api/v1/devices/{device_id}/data/historical` - Get historical data
- `GET /api/v1/devices/{device_id}/statistics` - Get device statistics

### Alerts
- `GET /api/v1/alerts` - Get all alerts
- `POST /api/v1/alerts/{alert_id}/resolve` - Resolve an alert

### ML Predictions
- `GET /api/v1/ml/predictions/{device_id}` - Get predictions
- `GET /api/v1/ml/predictions/{device_id}/latest` - Get latest prediction

### Analytics
- `GET /api/v1/analytics/traffic/{device_id}` - Traffic patterns
- `GET /api/v1/analytics/energy/{device_id}` - Energy consumption
- `GET /api/v1/analytics/optimization/{device_id}` - Optimization suggestions
- `GET /api/v1/analytics/report/{device_id}` - Comprehensive report

## Features

### Real-time Monitoring
- Live sensor data visualization
- Interactive map with device locations
- Real-time charts and statistics

### Predictive Maintenance
- Failure prediction using Random Forest
- Anomaly detection using Isolation Forest
- Health scoring for each device

### Analytics
- Traffic pattern analysis (hourly/daily patterns)
- Energy consumption tracking
- Cost analysis and optimization suggestions
- Comprehensive reporting

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Next.js, React, TypeScript, Leaflet, Recharts
- **ML**: scikit-learn, pandas, numpy
- **Hardware**: Arduino, ESP32/Raspberry Pi

## Development

### Adding New Features

1. Backend: Add routes in `backend/routes/`, services in `backend/services/`
2. Frontend: Add components in `frontend/src/components/`
3. ML: Add models in `ml_pipeline/`

### Database Migrations

Currently using SQLAlchemy's `create_all()`. For production, consider Alembic for migrations.

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or submit a pull request.


