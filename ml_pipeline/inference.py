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
from fault_prediction_model import FaultPredictionModel

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
        self.fault_model = None
        self.fault_model_simple = None  # New simplified model
        self.failure_features = None
        self.anomaly_features = None
        self.fault_features = None
        self.fault_scaler = None
        
        # Load models if available
        self._load_models()
    
    def _load_models(self):
        """Load trained models"""
        failure_model_path = os.path.join(self.model_dir, 'failure_predictor.pkl')
        anomaly_model_path = os.path.join(self.model_dir, 'anomaly_detector.pkl')
        fault_model_path = os.path.join(self.model_dir, 'fault_predictor.pkl')
        
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
        
        if os.path.exists(fault_model_path):
            self.fault_model = joblib.load(fault_model_path)
            fault_feature_path = os.path.join(self.model_dir, 'fault_predictor_features.pkl')
            if os.path.exists(fault_feature_path):
                self.fault_features = joblib.load(fault_feature_path)
            # Load scaler if it exists (for logistic regression)
            scaler_path = os.path.join(self.model_dir, 'fault_predictor_scaler.pkl')
            if os.path.exists(scaler_path):
                self.fault_scaler = joblib.load(scaler_path)
            logger.info("Fault prediction model loaded")
        else:
            logger.warning("Fault prediction model not found")
        
        # Try to load simplified model (focused on dampness and delay only)
        simple_model_path = os.path.join(self.model_dir, 'fault_predictor_simple.pkl')
        if os.path.exists(simple_model_path):
            self.fault_model_simple = FaultPredictionModel(self.model_dir)
            self.fault_model_simple.load(simple_model_path)
            logger.info("Simplified fault prediction model loaded (dampness + delay only)")
    
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
    
    def predict_fault(
        self, 
        sensor_data: Dict[str, Any], 
        historical_data: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        Predict fault probability based on light dampness and turn-on delay.
        
        Uses:
        1. Light dampness (LDR2 readings when light should be on)
        2. Turn-on delay (time between IR detection and light turning on)
        """
        # Try simplified model first (focused on just dampness and delay)
        if self.fault_model_simple and self.fault_model_simple.model:
            return self._predict_fault_simple(sensor_data, historical_data)
        
        if not self.fault_model:
            return {'error': 'Fault prediction model not loaded'}
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame([sensor_data])
            
            # Add historical context if available (needed for delay calculation)
            if historical_data is not None and not historical_data.empty:
                df = pd.concat([historical_data.tail(20), df], ignore_index=True)
            
            # Engineer features (this will calculate dampness and delay)
            df = self.feature_engineer.create_features(df)
            
            # Extract features
            X = df[self.fault_features].fillna(0).iloc[-1:].values
            
            # Scale if scaler exists (for logistic regression)
            if self.fault_scaler is not None:
                X = self.fault_scaler.transform(X)
            
            # Predict
            prediction = self.fault_model.predict(X)[0]
            
            # Get probabilities if available
            if hasattr(self.fault_model, 'predict_proba'):
                probability = self.fault_model.predict_proba(X)[0]
                fault_probability = float(probability[1] if len(probability) > 1 else probability[0])
            else:
                fault_probability = float(prediction)
            
            # Extract key feature values for interpretation
            feature_values = {}
            for i, feature_name in enumerate(self.fault_features):
                if i < len(X[0]):
                    feature_values[feature_name] = float(X[0][i])
            
            # Get dampness and delay values if available
            dampness_features = [f for f in self.fault_features if 'dampness' in f.lower()]
            delay_features = [f for f in self.fault_features if 'delay' in f.lower()]
            
            return {
                'prediction': int(prediction),
                'fault_probability': fault_probability,
                'is_fault_predicted': bool(prediction == 1),
                'timestamp': datetime.utcnow().isoformat(),
                'key_features': {
                    'dampness': {f: feature_values.get(f, 0) for f in dampness_features[:4]},
                    'delay': {f: feature_values.get(f, 0) for f in delay_features[:4]}
                }
            }
        except Exception as e:
            logger.error(f"Error in fault prediction: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def _predict_fault_simple(
        self,
        sensor_data: Dict[str, Any],
        historical_data: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        Use simplified model that only uses dampness and delay
        """
        try:
            # Convert sensor_data to DataFrame format for feature extraction
            # Need to parse lights_data if it exists
            import json
            
            # Create a DataFrame row from sensor_data
            df_row = pd.DataFrame([{
                'timestamp': sensor_data.get('timestamp', datetime.utcnow()),
                'ambient_light': sensor_data.get('ambient_light', 0),
            }])
            
            # Parse lights_data
            lights_data = sensor_data.get('lights_data', [])
            if isinstance(lights_data, str):
                lights_data = json.loads(lights_data)
            
            # Add light columns
            for i in range(1, 5):
                df_row[f'light_{i}_ldr'] = None
                df_row[f'light_{i}_state'] = None
                df_row[f'light_{i}_ir'] = None
                df_row[f'light_{i}_fault'] = None
            
            for light in lights_data:
                light_id = light.get('id', 0)
                if 1 <= light_id <= 4:
                    df_row[f'light_{light_id}_ldr'] = light.get('ldr_value', 0)
                    df_row[f'light_{light_id}_state'] = 1 if light.get('light_state', False) else 0
                    df_row[f'light_{light_id}_ir'] = 1 if light.get('ir_sensor', False) else 0
                    df_row[f'light_{light_id}_fault'] = 1 if light.get('fault_detected', False) else 0
                    # Store turn-on delay if provided by Arduino (in milliseconds)
                    turn_on_delay = light.get('turn_on_delay_ms', None)
                    if turn_on_delay is not None:
                        df_row[f'light_{light_id}_turn_on_delay_ms'] = turn_on_delay / 1000.0  # Convert to seconds
            
            # Combine with historical data for delay calculation
            if historical_data is not None and not historical_data.empty:
                # Parse historical lights_data if needed
                if 'lights_data' in historical_data.columns:
                    try:
                        from data_collection import DataCollector
                    except ImportError:
                        from ml_pipeline.data_collection import DataCollector
                    collector = DataCollector()
                    historical_data = collector._parse_lights_data(historical_data)
                
                df = pd.concat([historical_data.tail(20), df_row], ignore_index=True)
            else:
                df = df_row
            
            # Extract features using the simplified model
            features_df = self.fault_model_simple.prepare_features(df)
            
            if features_df.empty or 'light_dampness' not in features_df.columns:
                return {'error': 'Could not extract dampness/delay features'}
            
            # Get the latest values
            max_dampness = features_df['light_dampness'].iloc[-1] if len(features_df) > 0 else 0
            max_delay = features_df['turn_on_delay'].iloc[-1] if len(features_df) > 0 else 0
            
            # Predict using simplified model
            prediction = self.fault_model_simple.predict(max_dampness, max_delay)
            
            return {
                'prediction': 1 if prediction['will_fail'] else 0,
                'fault_probability': prediction['failure_probability'],
                'is_fault_predicted': prediction['will_fail'],
                'timestamp': datetime.utcnow().isoformat(),
                'key_features': {
                    'light_dampness': float(max_dampness),
                    'turn_on_delay': float(max_delay)
                },
                'interpretation': prediction['interpretation']
            }
        except Exception as e:
            logger.error(f"Error in simplified fault prediction: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def predict(self, sensor_data: Dict[str, Any], historical_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Get all predictions"""
        return {
            'failure': self.predict_failure(sensor_data, historical_data),
            'anomaly': self.detect_anomaly(sensor_data, historical_data),
            'fault': self.predict_fault(sensor_data, historical_data)
        }


