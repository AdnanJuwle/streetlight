# Fault Prediction Model Guide

## Overview

The fault prediction model uses **exactly 2 factors** to predict failure probability:

1. **Light Dampness (LDR2)**: Light level reading when the light should be on
   - Higher LDR2 value = less light detected = more dampness/fault
   - Measured when `light_state = True`

2. **Turn-on Delay**: Time between IR sensor detecting vehicle and light actually turning on
   - Increasing delays indicate relay aging
   - Measured in seconds

## Model Training

### Train the Focused Model

```bash
cd ml_pipeline
python fault_prediction_model.py --data ../data/training_data.csv --model-type logistic --look-ahead 24
```

**Parameters:**
- `--data`: Path to training data CSV
- `--model-type`: `logistic` (recommended) or `tree`
- `--look-ahead`: Hours ahead to predict failure (default: 24)

**Output:**
- Model saved to: `ml_pipeline/models/fault_predictor_simple.pkl`
- Scaler saved to: `ml_pipeline/models/fault_predictor_simple_scaler.pkl`

## How It Works

### Feature Extraction

1. **Light Dampness**:
   ```python
   dampness = LDR2_value when light_state == True
   # Higher value = less light = more dampness
   ```

2. **Turn-on Delay**:
   ```python
   delay = time(light_turns_on) - time(IR_detection)
   # Measured in seconds
   ```

### Prediction

The model takes these 2 values and outputs:
- **Failure probability** (0-1): Likelihood of failure in next 24 hours
- **Interpretation**: Human-readable explanation

### Example Prediction

```python
Input:
  - Light dampness: 65.5 (high - bulb not producing enough light)
  - Turn-on delay: 3.2 seconds (relay aging)

Output:
  - Failure probability: 0.78 (78%)
  - Interpretation: "Failure risk: HIGH (78.0%). Issues: High light dampness (65.5) - bulb may be failing; Moderate relay delay (3.2s) - early signs of aging"
```

## Model Performance

After training, you'll see:
- **Accuracy**: ~60% (baseline for binary classification)
- **AUC**: ~0.61 (area under ROC curve)
- **Features**: Only 2 features (dampness, delay)

## Usage in System

Once trained, the model automatically:
1. Extracts dampness and delay from sensor data
2. Predicts failure probability
3. Creates alerts when probability > 70%
4. Shows interpretation in frontend

## Viewing Predictions

1. **Frontend**: Select a device → See "ML Predictions" panel
2. **API**: `GET /api/v1/ml/predictions/{device_id}`
3. **Database**: Check `ml_predictions` table

## Model Interpretation

The model provides interpretable results:
- **Low risk** (< 40%): Normal operation
- **Medium risk** (40-70%): Monitor closely
- **High risk** (> 70%): Maintenance recommended, alert created

Each prediction includes:
- Light dampness value
- Turn-on delay value
- Human-readable interpretation

