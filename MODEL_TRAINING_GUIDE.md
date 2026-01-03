# Fault Prediction Model Training Guide

## Setup Complete! ✅

The system has been set up with:
- ✅ Dummy data added to database (500 sensor readings)
- ✅ Training data collected to `data/training_data.csv` (1000 records)
- ✅ Backend server ready

## Backend Server

The backend server should be running. If not, start it with:

```bash
cd C:\Users\adnan\Documents\repos\streetlight
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Training the Fault Prediction Model

### Step 1: Train the Focused Fault Prediction Model

**Recommended: Simplified Model (uses only dampness + delay)**

This model focuses on exactly what you need:
- **Light dampness** (LDR2 reading when light should be on)
- **Turn-on delay** (time between command and light turning on)

```bash
cd ml_pipeline
python fault_prediction_model.py --data ../data/training_data.csv --model-type logistic --look-ahead 24
```

**Alternative: Full Feature Model**

```bash
cd C:\Users\adnan\Documents\repos\streetlight
python ml_pipeline/model_training.py --data data/training_data.csv --model-type fault --fault-model-type logistic
```

### Step 2: Verify Model Training

After training, you should see:
- Model saved to `ml_pipeline/models/fault_predictor.pkl`
- Feature list saved to `ml_pipeline/models/fault_predictor_features.pkl`
- Scaler saved (for logistic regression) to `ml_pipeline/models/fault_predictor_scaler.pkl`
- Training metrics (accuracy, AUC, classification report)

### Step 3: Model is Ready!

Once trained, the model will automatically be used by the backend when:
- New sensor data is received via the API
- The ML service generates predictions
- Fault predictions are stored in the database
- Alerts are created when fault probability > 70%

## Training All Models

To train all models (failure, fault, and anomaly detection):

```bash
python ml_pipeline/model_training.py --data data/training_data.csv --model-type all
```

## Model Features

The fault prediction model uses these key features:

1. **Light Dampness** (`light_{id}_dampness`):
   - LDR2 readings when light should be on
   - Higher values = less light = more dampness/fault

2. **Turn-on Delay** (`light_{id}_turn_on_delay`):
   - Time between IR detection and light turning on
   - Increasing delays indicate relay aging

3. **Aggregated Features**:
   - Mean/max dampness across all lights
   - Mean/max turn-on delay across all lights
   - Rolling averages for trend analysis

## Testing the Model

After training, test predictions by:

1. **Send test data via API**:
```bash
curl -X POST "http://localhost:8000/api/v1/devices/streetlight-001/data" \
  -H "Content-Type: application/json" \
  -d @test_sensor_data.json
```

2. **Check predictions**:
```bash
curl "http://localhost:8000/api/v1/ml/predictions/streetlight-001/latest"
```

3. **View alerts** (if fault predicted):
```bash
curl "http://localhost:8000/api/v1/alerts"
```

## Troubleshooting

### Model Not Found Error
- Make sure you've trained the model first
- Check that `ml_pipeline/models/fault_predictor.pkl` exists

### Database Connection Error
- The system uses SQLite by default (file: `streetlight.db`)
- If using PostgreSQL, set `DATABASE_URL` environment variable

### Insufficient Data
- Add more dummy data: `python backend/add_dummy_data.py`
- Or collect more data from actual devices

## Next Steps

1. ✅ Train the fault prediction model
2. Monitor predictions via API
3. Adjust model parameters if needed
4. Deploy to production with real sensor data

