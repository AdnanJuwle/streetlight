"""
Real-time ML Inference Service
Generate predictions for incoming sensor data
"""

import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from feature_engineering import FeatureEngineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLInference:
    """ML inference service for real-time predictions"""
    
    def __init__(self, model_dir: str = 'models'):
        """Initialize inference service"""
        self.model_dir = model_dir
        self.feature_engineer = FeatureEngineer()
        self.failure_model = None
        self.anomaly_model = None
        self.failure_features = None
        self.anomaly_features = None
        
        # Load models if available
        self._load_models()
    
    def _load_models(self):
        """Load trained models"""
        failure_model_path = os.path.join(self.model_dir, 'failure_predictor.pkl')
        anomaly_model_path = os.path.join(self.model_dir, 'anomaly_detector.pkl')
        
        if os.path.exists(failure_model_path):
            self.failure_model = joblib.load(failure_model_path)
            failure_feature_path = os.path.join(self.model_dir, 'failure_predictor_features.pkl')
            if os.path.exists(failure_feature_path):
                self.failure_features = joblib.load(failure_feature_path)
            logger.info("Failure prediction model loaded")
        else:
            logger.warning("Failure prediction model not found")
        
        if os.path.exists(anomaly_model_path):
            self.anomaly_model = joblib.load(anomaly_model_path)
            anomaly_feature_path = os.path.join(self.model_dir, 'anomaly_detector_features.pkl')
            if os.path.exists(anomaly_feature_path):
                self.anomaly_features = joblib.load(anomaly_feature_path)
            logger.info("Anomaly detection model loaded")
        else:
            logger.warning("Anomaly detection model not found")
    
    def predict_failure(self, sensor_data: Dict[str, Any], historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Predict failure probability"""
        if not self.failure_model:
            return {'error': 'Model not loaded'}
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([sensor_data])
            
            # Add historical context if available
            if historical_data is not None and not historical_data.empty:
                df = pd.concat([historical_data.tail(10), df], ignore_index=True)
            
            # Engineer features
            df = self.feature_engineer.create_features(df)
            
            # Extract features
            X = df[self.failure_features].fillna(0).iloc[-1:].values
            
            # Predict
            prediction = self.failure_model.predict(X)[0]
            probability = self.failure_model.predict_proba(X)[0]
            
            return {
                'prediction': int(prediction),
                'probability': float(max(probability)),
                'failure_probability': float(probability[1] if len(probability) > 1 else 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in failure prediction: {e}")
            return {'error': str(e)}
    
    def detect_anomaly(self, sensor_data: Dict[str, Any], historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Detect anomalies"""
        if not self.anomaly_model:
            return {'error': 'Model not loaded'}
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([sensor_data])
            
            # Add historical context if available
            if historical_data is not None and not historical_data.empty:
                df = pd.concat([historical_data.tail(10), df], ignore_index=True)
            
            # Engineer features
            df = self.feature_engineer.create_features(df)
            
            # Extract features
            X = df[self.anomaly_features].fillna(0).iloc[-1:].values
            
            # Predict
            prediction = self.anomaly_model.predict(X)[0]
            score = self.anomaly_model.score_samples(X)[0]
            
            return {
                'is_anomaly': int(prediction) == -1,
                'anomaly_score': float(score),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {'error': str(e)}
    
    def predict(self, sensor_data: Dict[str, Any], historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Get all predictions"""
        return {
            'failure': self.predict_failure(sensor_data, historical_data),
            'anomaly': self.detect_anomaly(sensor_data, historical_data)
        }


