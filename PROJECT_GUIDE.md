# Complete Project Guide: AI-Enhanced Smart Streetlight System

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [File-by-File Explanation](#file-by-file-explanation)
4. [Models & Algorithms](#models--algorithms)
5. [Current Progress](#current-progress)
6. [What Needs to be Done](#what-needs-to-be-done)
7. [Timeline & Milestones](#timeline--milestones)
8. [Step-by-Step Completion Guide](#step-by-step-completion-guide)
9. [Technical Complexities](#technical-complexities)
10. [Testing & Validation](#testing--validation)

---

## Project Overview

### What This Project Does
This is an **AI-powered smart streetlight management system** that:
- Monitors streetlights in real-time using sensors (LDR, IR, GPS)
- Predicts failures before they happen using machine learning
- Detects anomalies in sensor readings
- Analyzes traffic patterns to optimize energy usage
- Provides a web dashboard for monitoring and control
- Sends alerts when faults are detected

### The Problem It Solves
Traditional streetlight systems:
- Only detect problems after they occur
- Waste energy by running at full brightness all night
- Require manual inspection to find issues
- Don't learn from patterns

This system:
- Predicts problems before they happen (predictive maintenance)
- Optimizes energy based on actual usage patterns
- Automatically detects and reports issues
- Learns and improves over time

---

## System Architecture

### High-Level Flow
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│   Arduino   │─────▶│ Bridge Service│─────▶│ Backend API │─────▶│   Database   │
│  (Sensors)  │      │ (ESP32/RPi)   │      │  (FastAPI)  │      │ (PostgreSQL) │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │ ML Pipeline  │
                                              │ (Predictions)│
                                              └──────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │ Web Dashboard│
                                              │  (Next.js)   │
                                              └──────────────┘
```

### Component Breakdown

1. **Hardware Layer (Arduino)**
   - Reads sensors (LDR, IR, GPS)
   - Controls lights (on/off)
   - Outputs JSON data via Serial

2. **Bridge Layer (ESP32/Raspberry Pi)**
   - Connects Arduino to internet
   - Reads serial data
   - Sends to backend via HTTP

3. **Backend Layer (FastAPI)**
   - Receives and stores sensor data
   - Runs ML inference
   - Provides REST API
   - Manages alerts

4. **ML Layer (Python)**
   - Trains models on historical data
   - Makes predictions in real-time
   - Detects anomalies

5. **Frontend Layer (Next.js)**
   - Displays real-time data
   - Shows maps and charts
   - Manages alerts

6. **Database Layer (PostgreSQL)**
   - Stores time-series sensor data
   - Stores predictions
   - Stores alerts and device info

---

## File-by-File Explanation

### Arduino Code

#### `finalver.ino`
**Purpose**: Main Arduino sketch that reads sensors and controls lights

**Key Functions**:
- `readLDR(pin)`: Reads light-dependent resistor (0-100 scale)
- `readLDRRaw(pin)`: Reads raw analog value
- `updateGPS()`: Gets GPS coordinates
- `sendJSONData()`: Creates and sends JSON with all sensor readings
- `countActiveLights()`: Counts how many lights are on
- `countFaultyLights()`: Counts lights with faults

**What it does**:
1. Every 5 seconds, reads all sensors
2. Checks if it's dark (ambient light > 20)
3. If dark, checks IR sensors for movement
4. Turns lights on/off based on movement
5. Detects faults (light on but LDR reading too low)
6. Outputs JSON data to Serial port

**Output Format**:
```json
{
  "timestamp": 1234567890,
  "ambient_light": 45.2,
  "gps": {"valid": true, "latitude": 19.0760, "longitude": 72.8777},
  "lights": [
    {"id": 1, "ldr_value": 30, "ir_sensor": true, "light_state": true, "fault_detected": false}
  ],
  "system": {"is_dark": true, "active_lights": 2, "faulty_lights": 0}
}
```

---

### Bridge Service

#### `bridge_service/bridge_service.py`
**Purpose**: Connects Arduino to backend API via WiFi

**Key Components**:
- `ArduinoBridge` class: Main service class
- `connect_serial()`: Opens serial connection to Arduino
- `read_serial_line()`: Reads JSON from Arduino
- `parse_json_data()`: Validates and parses JSON
- `send_to_api()`: POSTs data to backend
- `run()`: Main loop that continuously reads and sends data

**How it works**:
1. Connects to Arduino via serial port (USB)
2. Reads JSON lines from Arduino
3. Adds device metadata (device_id, timestamp)
4. Sends to backend API endpoint
5. Handles errors and reconnection

**Configuration**:
- Serial port: `/dev/ttyUSB0` (Linux) or `COM3` (Windows)
- Baud rate: 9600
- API URL: `http://localhost:8000`
- Device ID: `streetlight-001`

#### `bridge_service/requirements.txt`
Python dependencies: `pyserial`, `requests`

---

### Backend API

#### `backend/main.py`
**Purpose**: FastAPI application entry point

**What it does**:
- Initializes database on startup
- Sets up CORS (allows frontend to connect)
- Includes all route modules
- Provides health check endpoint

**Endpoints**:
- `GET /`: Root endpoint
- `GET /health`: Health check
- `GET /docs`: Auto-generated API documentation

#### `backend/models/database.py`
**Purpose**: Database schema definitions using SQLAlchemy

**Tables**:

1. **Device**: Streetlight device metadata
   - `id`: Unique device ID
   - `name`, `location_name`: Human-readable names
   - `latitude`, `longitude`: GPS coordinates
   - `status`: active/inactive/maintenance

2. **SensorData**: Time-series sensor readings
   - Stores every reading from Arduino
   - Includes ambient light, GPS, light states
   - Indexed by device_id and timestamp for fast queries

3. **Alert**: Fault notifications
   - `alert_type`: fault/maintenance/anomaly
   - `severity`: low/medium/high/critical
   - `status`: open/acknowledged/resolved

4. **MLPrediction**: ML model predictions
   - Stores failure predictions and anomaly scores
   - Links to device and timestamp

5. **MaintenanceLog**: Maintenance history
6. **EnergyConsumption**: Energy tracking

**Key Functions**:
- `init_db()`: Creates all tables
- `get_session_local()`: Creates database session factory

#### `backend/schemas.py`
**Purpose**: Pydantic models for API request/response validation

**Why it's important**: 
- Validates incoming data before processing
- Ensures type safety
- Auto-generates API documentation

**Key Schemas**:
- `SensorDataCreate`: Input from bridge service
- `SensorDataResponse`: Output to frontend
- `DeviceResponse`, `AlertResponse`: Other API responses

#### `backend/services/data_service.py`
**Purpose**: Business logic for sensor data operations

**Key Functions**:

1. **DataService.create_sensor_data()**
   - Receives sensor data from API
   - Stores in database
   - Checks for faults and creates alerts
   - Triggers ML predictions

2. **DataService.get_latest_data()**
   - Gets most recent reading for a device

3. **DataService.get_historical_data()**
   - Gets data for time range
   - Used for charts and analytics

4. **DataService.get_device_statistics()**
   - Calculates averages, totals
   - Used in dashboard

**DeviceService**: Manages device CRUD operations
**AlertService**: Manages alert operations

#### `backend/services/ml_service.py`
**Purpose**: Integrates ML predictions into backend

**Key Functions**:
- `generate_predictions()`: Calls ML inference service
- `_get_historical_data()`: Gets recent data for context
- `_store_predictions()`: Saves predictions to database

**How it works**:
1. When new sensor data arrives
2. Gets last hour of data for context
3. Calls ML inference service
4. Stores predictions in database
5. Can trigger alerts if prediction indicates failure

#### `backend/services/analytics_service.py`
**Purpose**: Advanced analytics and reporting

**Key Functions**:

1. **analyze_traffic_patterns()**
   - Analyzes IR sensor data
   - Finds peak hours
   - Creates hourly/daily patterns
   - Returns JSON with patterns

2. **calculate_energy_consumption()**
   - Calculates kWh used
   - Estimates costs
   - Tracks hourly consumption
   - Returns energy report

3. **optimize_energy()**
   - Analyzes traffic patterns
   - Suggests dimming during low-traffic hours
   - Calculates potential savings
   - Returns optimization suggestions

4. **generate_report()**
   - Combines all analytics
   - Creates comprehensive report
   - Includes uptime, faults, costs

#### `backend/routes/devices.py`
**Purpose**: API endpoints for device and sensor data

**Endpoints**:
- `POST /api/v1/devices/{device_id}/data`: Ingest sensor data
- `GET /api/v1/devices/{device_id}/data/latest`: Latest reading
- `GET /api/v1/devices/{device_id}/data/historical`: Historical data
- `GET /api/v1/devices/{device_id}/statistics`: Statistics
- `POST /api/v1/devices`: Create device
- `GET /api/v1/devices/{device_id}`: Get device info
- `GET /api/v1/devices`: List all devices

#### `backend/routes/alerts.py`
**Purpose**: Alert management endpoints

**Endpoints**:
- `GET /api/v1/alerts`: List alerts (with filters)
- `GET /api/v1/alerts/{alert_id}`: Get specific alert
- `POST /api/v1/alerts/{alert_id}/resolve`: Mark as resolved

#### `backend/routes/ml.py`
**Purpose**: ML prediction endpoints

**Endpoints**:
- `GET /api/v1/ml/predictions/{device_id}`: Get predictions
- `GET /api/v1/ml/predictions/{device_id}/latest`: Latest prediction

#### `backend/routes/analytics.py`
**Purpose**: Analytics endpoints

**Endpoints**:
- `GET /api/v1/analytics/traffic/{device_id}`: Traffic patterns
- `GET /api/v1/analytics/energy/{device_id}`: Energy consumption
- `GET /api/v1/analytics/optimization/{device_id}`: Optimization suggestions
- `GET /api/v1/analytics/report/{device_id}`: Full report

---

### Frontend (Next.js Dashboard)

#### `frontend/src/app/page.tsx`
**Purpose**: Main dashboard page

**What it does**:
- Loads all devices and their latest data
- Displays map, device list, alerts
- Refreshes every 5 seconds
- Handles device selection

**State Management**:
- `devices`: List of all devices
- `latestData`: Latest readings per device
- `alerts`: Active alerts
- `selectedDevice`: Currently selected device

#### `frontend/src/components/DeviceMap.tsx`
**Purpose**: Interactive map showing device locations

**Features**:
- Uses Leaflet for mapping
- Shows markers for each device
- Color-coded by status (green=good, red=faulty)
- Click marker to select device
- Popup shows device info

**Libraries**: `react-leaflet`, `leaflet`

#### `frontend/src/components/DeviceList.tsx`
**Purpose**: Table of all devices

**Features**:
- Shows device ID, name, status
- Displays active/faulty lights count
- Shows ambient light level
- Shows last update time
- Click row to select device
- Status indicators (green/red/yellow dots)

#### `frontend/src/components/StatisticsPanel.tsx`
**Purpose**: Shows statistics for selected device

**Displays**:
- Total readings (24h)
- Average ambient light
- Max faulty lights
- Average active lights

**Updates**: Every 10 seconds

#### `frontend/src/components/AlertsPanel.tsx`
**Purpose**: Shows active alerts

**Features**:
- Color-coded by severity
- Shows alert type, message, device
- "Resolve" button to close alerts
- Shows timestamp

#### `frontend/src/components/RealTimeChart.tsx`
**Purpose**: Real-time line chart

**Features**:
- Shows ambient light over time
- Shows active lights count
- Shows faulty lights count
- Updates every 10 seconds
- Uses Recharts library

#### `frontend/src/lib/api.ts`
**Purpose**: API client for backend communication

**Functions**:
- `getDevices()`: Fetch all devices
- `getLatestData()`: Get latest sensor reading
- `getHistoricalData()`: Get time-series data
- `getDeviceStatistics()`: Get stats
- `getAlerts()`: Get alerts
- `resolveAlert()`: Resolve alert

**Uses**: `axios` for HTTP requests

---

### ML Pipeline

#### `ml_pipeline/data_collection.py`
**Purpose**: Collects and prepares data for ML training

**Key Functions**:

1. **DataCollector.collect_device_data()**
   - Queries database for device data
   - Filters by date range
   - Parses JSON lights_data column
   - Returns pandas DataFrame

2. **DataCollector.create_training_dataset()**
   - Collects data for all devices
   - Combines into single dataset
   - Saves to CSV
   - Returns DataFrame

3. **DataCollector.get_failure_events()**
   - Gets historical failure events from alerts
   - Used for labeling training data

**Output**: CSV file with all sensor readings

#### `ml_pipeline/feature_engineering.py`
**Purpose**: Creates features from raw sensor data

**Key Functions**:

1. **FeatureEngineer.create_features()**
   - Main function that orchestrates feature creation
   - Calls all sub-functions
   - Returns DataFrame with features

**Feature Types Created**:

1. **Basic Features**:
   - `hour`: Hour of day (0-23)
   - `day_of_week`: Day (0-6)
   - `is_weekend`: Boolean
   - `is_night`: Boolean (8pm-6am)
   - `ambient_light_squared`: Non-linear feature
   - `ambient_light_log`: Log transform

2. **Temporal Features**:
   - `time_since_start`: Hours since first reading

3. **Rolling Statistics** (10-point window):
   - `ambient_light_rolling_mean`: Average of last 10 readings
   - `ambient_light_rolling_std`: Standard deviation
   - `ambient_light_rolling_min/max`: Min/max values
   - `ambient_light_diff`: Change from previous
   - `ambient_light_pct_change`: Percentage change

4. **Light-Specific Features**:
   - `mean_light_ldr`: Average LDR across all lights
   - `std_light_ldr`: Variance indicator
   - `min_light_ldr`, `max_light_ldr`: Range
   - `total_faults`: Count of faulty lights
   - `fault_rate`: Percentage of lights faulty
   - `total_active`: Count of active lights
   - `active_rate`: Percentage active

5. **Lag Features**:
   - `ambient_light_lag_1`: Value 1 reading ago
   - `ambient_light_lag_3`: Value 3 readings ago
   - `ambient_light_lag_6`: Value 6 readings ago

**Why These Features**:
- **Rolling stats**: Capture trends and patterns
- **Lag features**: Capture temporal dependencies
- **Time features**: Capture daily/weekly patterns
- **Light features**: Capture individual light behavior

#### `ml_pipeline/model_training.py`
**Purpose**: Trains ML models

**Models Trained**:

1. **Failure Prediction Model (Random Forest)**
   - **Type**: Classification (binary)
   - **Target**: Will there be a failure in next 6 hours?
   - **Algorithm**: Random Forest Classifier
   - **Parameters**:
     - `n_estimators=100`: 100 decision trees
     - `max_depth=10`: Limit tree depth
     - `random_state=42`: For reproducibility
   - **Output**: Probability of failure (0-1)
   - **Evaluation**: Accuracy, precision, recall

2. **Anomaly Detection Model (Isolation Forest)**
   - **Type**: Unsupervised anomaly detection
   - **Target**: Detect unusual patterns
   - **Algorithm**: Isolation Forest
   - **Parameters**:
     - `contamination=0.1`: Expect 10% anomalies
     - `random_state=42`
   - **Output**: -1 (anomaly) or 1 (normal), anomaly score

**Training Process**:
1. Load CSV data
2. Engineer features
3. Split train/test (80/20)
4. Train model
5. Evaluate on test set
6. Save model to `.pkl` file
7. Save feature list

**Output Files**:
- `models/failure_predictor.pkl`: Trained model
- `models/failure_predictor_features.pkl`: Feature list
- `models/anomaly_detector.pkl`: Trained model
- `models/anomaly_detector_features.pkl`: Feature list

#### `ml_pipeline/inference.py`
**Purpose**: Real-time ML predictions

**Key Functions**:

1. **MLInference.predict_failure()**
   - Takes current sensor reading
   - Gets last 10 readings for context
   - Engineers features
   - Runs model prediction
   - Returns probability and prediction

2. **MLInference.detect_anomaly()**
   - Similar process
   - Returns anomaly flag and score

3. **MLInference.predict()**
   - Runs both models
   - Returns combined results

**How it works**:
1. Loads saved models on initialization
2. When called with new data:
   - Converts to DataFrame
   - Engineers features
   - Extracts required features
   - Runs model
   - Returns prediction

---

## Models & Algorithms

### 1. Random Forest (Failure Prediction)

**What it is**: Ensemble learning method using multiple decision trees

**How it works**:
1. Creates 100 decision trees
2. Each tree votes on prediction
3. Final prediction = majority vote
4. Probability = percentage of trees voting for class

**Why Random Forest**:
- Handles non-linear relationships
- Robust to outliers
- Doesn't overfit easily
- Provides feature importance
- Works well with mixed data types

**Complexity**:
- Training: O(n × m × log(n) × k) where:
  - n = number of samples
  - m = number of features
  - k = number of trees (100)
- Prediction: O(k × log(m))

**Hyperparameters**:
- `n_estimators`: More trees = better but slower (100 is good)
- `max_depth`: Deeper = more complex patterns but overfitting risk (10)
- `min_samples_split`: Minimum samples to split node (default 2)

### 2. Isolation Forest (Anomaly Detection)

**What it is**: Unsupervised algorithm that isolates anomalies

**How it works**:
1. Randomly selects features and split values
2. Creates isolation trees
3. Anomalies are easier to isolate (fewer splits needed)
4. Anomaly score = average path length

**Why Isolation Forest**:
- Unsupervised (no labels needed)
- Fast on large datasets
- Works well with high-dimensional data
- Handles outliers naturally

**Complexity**:
- Training: O(n × log(n))
- Prediction: O(log(n))

**Hyperparameters**:
- `contamination`: Expected proportion of anomalies (0.1 = 10%)
- `n_estimators`: Number of trees (default 100)

### Feature Engineering Complexity

**Time Complexity**: O(n × f) where:
- n = number of samples
- f = number of features created

**Space Complexity**: O(n × f) for storing features

**Feature Count**: ~50-100 features per sample

---

## Current Progress

### ✅ Completed

1. **Arduino Code**
   - ✅ JSON output with all sensor data
   - ✅ Timestamp generation
   - ✅ Fault detection logic
   - ✅ GPS integration

2. **Bridge Service**
   - ✅ Serial communication
   - ✅ HTTP API client
   - ✅ Error handling
   - ✅ Reconnection logic

3. **Backend API**
   - ✅ Database schema
   - ✅ All API endpoints
   - ✅ Data ingestion
   - ✅ Alert management
   - ✅ ML integration
   - ✅ Analytics services

4. **Frontend Dashboard**
   - ✅ Device map
   - ✅ Device list
   - ✅ Real-time charts
   - ✅ Alerts panel
   - ✅ Statistics display

5. **ML Pipeline**
   - ✅ Data collection
   - ✅ Feature engineering
   - ✅ Model training code
   - ✅ Inference service

### ⚠️ Partially Complete

1. **ML Models**
   - ⚠️ Code written but models not trained (need data first)
   - ⚠️ Need 2-4 weeks of real data

2. **Testing**
   - ⚠️ No unit tests
   - ⚠️ No integration tests
   - ⚠️ Manual testing only

3. **Deployment**
   - ⚠️ No Docker configuration
   - ⚠️ No CI/CD pipeline
   - ⚠️ No production configs

### ❌ Not Started

1. **Hardware Integration**
   - ❌ ESP32/Raspberry Pi setup not done
   - ❌ WiFi configuration
   - ❌ Physical hardware testing

2. **Production Features**
   - ❌ Authentication/authorization
   - ❌ Rate limiting
   - ❌ Logging infrastructure
   - ❌ Monitoring/alerting

3. **Advanced ML**
   - ❌ Model retraining pipeline
   - ❌ Model versioning
   - ❌ A/B testing
   - ❌ Model monitoring

---

## What Needs to be Done

### Phase 1: Hardware Setup & Data Collection (Weeks 1-4)

#### 1.1 Hardware Setup
- [ ] Set up ESP32 or Raspberry Pi
- [ ] Connect to WiFi
- [ ] Connect Arduino to ESP32/RPi via USB
- [ ] Test serial communication
- [ ] Verify bridge service can read data
- [ ] Test data transmission to backend

**Estimated Time**: 1-2 weeks

#### 1.2 Backend Setup
- [ ] Install PostgreSQL
- [ ] Create database
- [ ] Run database migrations
- [ ] Configure environment variables
- [ ] Test API endpoints
- [ ] Verify data ingestion

**Estimated Time**: 2-3 days

#### 1.3 Data Collection
- [ ] Deploy bridge service
- [ ] Start collecting real sensor data
- [ ] Monitor for 2-4 weeks
- [ ] Verify data quality
- [ ] Check for missing data
- [ ] Validate sensor readings

**Estimated Time**: 2-4 weeks (passive)

### Phase 2: ML Model Training (Week 5)

#### 2.1 Data Preparation
- [ ] Run data collection script
- [ ] Export data to CSV
- [ ] Validate data quality
- [ ] Check for missing values
- [ ] Identify failure events

**Estimated Time**: 1 day

#### 2.2 Feature Engineering
- [ ] Run feature engineering
- [ ] Validate features
- [ ] Check feature distributions
- [ ] Remove highly correlated features
- [ ] Select best features

**Estimated Time**: 2-3 days

#### 2.3 Model Training
- [ ] Train failure prediction model
- [ ] Train anomaly detection model
- [ ] Evaluate model performance
- [ ] Tune hyperparameters
- [ ] Validate on test set
- [ ] Save models

**Estimated Time**: 2-3 days

#### 2.4 Model Integration
- [ ] Deploy models to backend
- [ ] Test inference service
- [ ] Verify predictions
- [ ] Monitor prediction quality

**Estimated Time**: 1-2 days

### Phase 3: Frontend Deployment (Week 6)

#### 3.1 Frontend Setup
- [ ] Install Node.js dependencies
- [ ] Configure API URL
- [ ] Test locally
- [ ] Fix any bugs
- [ ] Optimize performance

**Estimated Time**: 2-3 days

#### 3.2 Deployment
- [ ] Deploy backend to server
- [ ] Deploy frontend to hosting (Vercel/Netlify)
- [ ] Configure CORS
- [ ] Set up SSL certificates
- [ ] Test end-to-end

**Estimated Time**: 2-3 days

### Phase 4: Testing & Optimization (Week 7)

#### 4.1 Testing
- [ ] Unit tests for backend
- [ ] Integration tests
- [ ] Frontend component tests
- [ ] End-to-end testing
- [ ] Load testing

**Estimated Time**: 1 week

#### 4.2 Optimization
- [ ] Database query optimization
- [ ] API response time optimization
- [ ] Frontend performance optimization
- [ ] ML model optimization
- [ ] Caching implementation

**Estimated Time**: 3-5 days

### Phase 5: Production Features (Week 8)

#### 5.1 Security
- [ ] Add authentication (JWT)
- [ ] Add authorization (roles)
- [ ] Rate limiting
- [ ] Input validation
- [ ] SQL injection prevention

**Estimated Time**: 3-5 days

#### 5.2 Monitoring
- [ ] Set up logging
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring
- [ ] Uptime monitoring
- [ ] Alert notifications

**Estimated Time**: 2-3 days

---

## Timeline & Milestones

### Total Timeline: 8-10 weeks

| Week | Phase | Tasks | Deliverable |
|------|-------|-------|-------------|
| 1-2 | Hardware Setup | ESP32/RPi setup, WiFi, testing | Working hardware connection |
| 3-6 | Data Collection | Collect real sensor data | 2-4 weeks of data |
| 7 | ML Training | Train and deploy models | Trained models |
| 8 | Frontend Deployment | Deploy dashboard | Live dashboard |
| 9 | Testing | Comprehensive testing | Tested system |
| 10 | Production | Security, monitoring | Production-ready system |

### Critical Path
1. Hardware setup → Data collection (blocks everything)
2. Data collection → ML training (needs 2-4 weeks)
3. ML training → Full system testing

### Dependencies
- Backend can be set up independently
- Frontend depends on backend API
- ML depends on collected data
- Everything depends on hardware working

---

## Step-by-Step Completion Guide

### Step 1: Set Up Development Environment

```bash
# 1. Install Python 3.9+
python --version

# 2. Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Linux
# or download from postgresql.org for Windows/Mac

# 3. Install Node.js 18+
node --version
npm --version

# 4. Clone repository (if not already)
git clone git@github.com:AdnanJuwle/streetlight.git
cd streetlight
```

### Step 2: Set Up Database

```bash
# 1. Create database
sudo -u postgres psql
CREATE DATABASE streetlight_db;
CREATE USER streetlight WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE streetlight_db TO streetlight;
\q

# 2. Update backend/.env
DATABASE_URL=postgresql://streetlight:your_password@localhost:5432/streetlight_db

# 3. Initialize database
cd backend
pip install -r requirements.txt
python -c "from models.database import init_db; init_db()"
```

### Step 3: Set Up Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test backend
uvicorn main:app --reload

# 4. Test API
curl http://localhost:8000/health
```

### Step 4: Set Up Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. Run development server
npm run dev

# 4. Open browser
# http://localhost:3000
```

### Step 5: Hardware Setup

#### Option A: ESP32
```bash
# 1. Install ESP32 tools
# Follow ESP32 setup guide

# 2. Upload bridge service
# Or use Python on ESP32 with MicroPython

# 3. Configure WiFi
# Edit bridge_service.py with WiFi credentials

# 4. Connect Arduino
# Connect Arduino USB to ESP32
```

#### Option B: Raspberry Pi
```bash
# 1. Install Raspberry Pi OS
# 2. Install Python
sudo apt-get install python3-pip

# 3. Install bridge service
cd bridge_service
pip3 install -r requirements.txt

# 4. Configure
# Edit bridge_service.py

# 5. Run as service
sudo systemctl enable bridge_service
```

### Step 6: Test Data Flow

```bash
# 1. Start backend
cd backend
uvicorn main:app --reload

# 2. Start bridge service
cd bridge_service
python bridge_service.py --serial-port /dev/ttyUSB0

# 3. Verify data in database
psql -U streetlight -d streetlight_db
SELECT COUNT(*) FROM sensor_data;
```

### Step 7: Collect Training Data

```bash
# Wait 2-4 weeks for data collection

# Then collect data
cd ml_pipeline
python data_collection.py --days 30 --output data/training_data.csv
```

### Step 8: Train ML Models

```bash
cd ml_pipeline

# 1. Train models
python model_training.py --data data/training_data.csv --model-type both

# 2. Verify models created
ls models/
# Should see: failure_predictor.pkl, anomaly_detector.pkl

# 3. Test inference
python -c "from inference import MLInference; inf = MLInference(); print('Models loaded')"
```

### Step 9: Deploy

```bash
# Backend deployment (example with systemd)
# Create /etc/systemd/system/streetlight-api.service
[Unit]
Description=Streetlight API
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/streetlight/backend
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target

# Frontend deployment
cd frontend
npm run build
# Deploy to Vercel/Netlify
```

---

## Technical Complexities

### 1. Time-Series Data Management

**Challenge**: Storing and querying millions of sensor readings efficiently

**Solutions**:
- Use PostgreSQL with TimescaleDB extension (time-series optimized)
- Index on (device_id, timestamp)
- Partition tables by time (monthly partitions)
- Archive old data (>1 year)

**Complexity**: Medium-High

### 2. Real-Time Data Streaming

**Challenge**: Processing data as it arrives without blocking

**Solutions**:
- Use async/await in FastAPI
- Background tasks for ML inference
- Message queue (Redis/RabbitMQ) for high volume
- WebSockets for real-time frontend updates

**Complexity**: Medium

### 3. ML Model Deployment

**Challenge**: Running ML models in production with low latency

**Solutions**:
- Pre-load models in memory
- Batch predictions when possible
- Use lighter models (TensorFlow Lite)
- Cache predictions for similar inputs

**Complexity**: Medium

### 4. Feature Engineering at Scale

**Challenge**: Creating features in real-time for predictions

**Solutions**:
- Pre-compute rolling statistics
- Store feature values in database
- Use efficient pandas operations
- Vectorize operations with NumPy

**Complexity**: Medium

### 5. Handling Missing Data

**Challenge**: Devices may go offline, sensors may fail

**Solutions**:
- Impute missing values (forward fill, interpolation)
- Flag missing data in database
- Alert on extended outages
- Handle gracefully in ML models

**Complexity**: Low-Medium

### 6. GPS Coordinate Accuracy

**Challenge**: GPS may not always be available or accurate

**Solutions**:
- Store last known good coordinates
- Use device metadata for fixed locations
- Validate GPS readings
- Fallback to device location

**Complexity**: Low

### 7. Model Retraining

**Challenge**: Models need retraining as data patterns change

**Solutions**:
- Schedule weekly/monthly retraining
- Monitor model performance
- A/B test new models
- Version control models

**Complexity**: High

---

## Testing & Validation

### Unit Tests Needed

1. **Backend Services**
   - `test_data_service.py`: Test data operations
   - `test_ml_service.py`: Test ML inference
   - `test_analytics_service.py`: Test analytics

2. **ML Pipeline**
   - `test_feature_engineering.py`: Test feature creation
   - `test_model_training.py`: Test model training
   - `test_inference.py`: Test predictions

3. **Frontend**
   - Component tests
   - API client tests

### Integration Tests

1. **End-to-End Flow**
   - Arduino → Bridge → Backend → Database
   - Backend → ML → Predictions → Database
   - Frontend → API → Database → Frontend

2. **API Tests**
   - All endpoints
   - Error handling
   - Authentication (when added)

### Performance Tests

1. **Load Testing**
   - 1000 requests/second
   - Concurrent users
   - Database query performance

2. **ML Inference**
   - Prediction latency (<100ms)
   - Throughput (predictions/second)

### Validation Metrics

1. **ML Models**
   - Accuracy > 85%
   - Precision > 80%
   - Recall > 75%
   - F1-score > 0.75

2. **System**
   - API response time < 200ms
   - Data ingestion latency < 1s
   - Uptime > 99.5%

---

## Common Issues & Solutions

### Issue 1: Bridge Service Can't Connect to Arduino

**Symptoms**: No data in database

**Solutions**:
- Check serial port: `ls /dev/tty*`
- Check baud rate matches (9600)
- Check USB connection
- Check Arduino is sending data: `cat /dev/ttyUSB0`

### Issue 2: Database Connection Errors

**Symptoms**: Backend can't connect to database

**Solutions**:
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `.env`
- Check database exists: `psql -l`
- Check firewall rules

### Issue 3: ML Models Not Loading

**Symptoms**: Predictions fail

**Solutions**:
- Check models exist: `ls models/*.pkl`
- Check feature files exist
- Verify model version compatibility
- Check Python path includes ml_pipeline

### Issue 4: Frontend Can't Connect to API

**Symptoms**: Dashboard shows errors

**Solutions**:
- Check API URL in `.env.local`
- Check CORS settings in backend
- Check backend is running
- Check network connectivity

### Issue 5: Low ML Model Accuracy

**Symptoms**: Poor predictions

**Solutions**:
- Collect more training data
- Improve feature engineering
- Tune hyperparameters
- Check for data quality issues
- Try different algorithms

---

## Next Steps for You

### Immediate (This Week)

1. **Set up development environment**
   - Install PostgreSQL
   - Install Python and Node.js
   - Clone repository

2. **Test backend locally**
   - Set up database
   - Run backend
   - Test API endpoints

3. **Test frontend locally**
   - Install dependencies
   - Run development server
   - Verify UI loads

### Short-term (Next 2 Weeks)

1. **Hardware setup**
   - Get ESP32 or Raspberry Pi
   - Set up WiFi
   - Connect Arduino
   - Test bridge service

2. **Start data collection**
   - Deploy bridge service
   - Verify data flowing to database
   - Monitor for issues

### Medium-term (Next Month)

1. **Collect training data**
   - Run system for 2-4 weeks
   - Monitor data quality
   - Fix any issues

2. **Train ML models**
   - Export data
   - Train models
   - Evaluate performance
   - Deploy models

### Long-term (Next 2-3 Months)

1. **Deploy to production**
   - Set up servers
   - Deploy backend
   - Deploy frontend
   - Configure monitoring

2. **Add production features**
   - Authentication
   - Security hardening
   - Performance optimization
   - Monitoring and alerts

---

## Resources & Learning

### Documentation to Read

1. **FastAPI**: https://fastapi.tiangolo.com/
2. **Next.js**: https://nextjs.org/docs
3. **SQLAlchemy**: https://docs.sqlalchemy.org/
4. **scikit-learn**: https://scikit-learn.org/stable/
5. **PostgreSQL**: https://www.postgresql.org/docs/

### Key Concepts to Understand

1. **REST APIs**: HTTP methods, status codes, JSON
2. **Time-series data**: Indexing, queries, aggregation
3. **Machine Learning**: Features, training, evaluation
4. **React/Next.js**: Components, state, hooks
5. **Database design**: Normalization, indexes, queries

### Practice Exercises

1. **API Development**
   - Create a new endpoint
   - Add validation
   - Write tests

2. **ML**
   - Experiment with different features
   - Try different algorithms
   - Tune hyperparameters

3. **Frontend**
   - Add a new component
   - Create a new chart
   - Add filtering

---

## Summary

This is a **comprehensive IoT + AI system** that:
- Collects sensor data from Arduino
- Stores it in a database
- Makes AI predictions
- Displays everything in a web dashboard

**Current Status**: ~70% complete
- Code is written
- Architecture is designed
- Need: Hardware setup, data collection, model training, deployment

**Timeline**: 8-10 weeks to production-ready

**Your Role**: 
- Set up hardware
- Collect data
- Train models
- Deploy system
- Test and optimize

**Key Skills Needed**:
- Python (backend, ML)
- JavaScript/TypeScript (frontend)
- SQL (database)
- Basic electronics (Arduino)
- Linux/system administration (deployment)

Good luck! This is an impressive project that combines hardware, software, AI, and web development. Take it step by step, and you'll have a production-ready smart city system!

