"""
ML Service for real-time inference
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ml_pipeline'))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import logging

from models.database import SensorData, MLPrediction
from ml_pipeline.inference import MLInference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLService:
    """Service for ML inference and predictions"""
    
    def __init__(self):
        """Initialize ML service"""
        self.inference = MLInference()
    
    def generate_predictions(
        self,
        db: Session,
        device_id: str,
        sensor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate ML predictions for sensor data"""
        try:
            # Get recent historical data for context
            historical_data = self._get_historical_data(db, device_id, hours=1)
            
            # Get predictions
            predictions = self.inference.predict(sensor_data, historical_data)
            
            # Store predictions in database
            self._store_predictions(db, device_id, predictions)
            
            return predictions
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {'error': str(e)}
    
    def _get_historical_data(
        self,
        db: Session,
        device_id: str,
        hours: int = 1
    ) -> Optional[pd.DataFrame]:
        """Get historical data for context"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = db.query(SensorData).filter(
                SensorData.device_id == device_id,
                SensorData.timestamp >= start_time
            ).order_by(SensorData.timestamp.asc()).all()
            
            if not query:
                return None
            
            # Convert to DataFrame
            data = []
            for row in query:
                data.append({
                    'timestamp': row.timestamp,
                    'ambient_light': row.ambient_light,
                    'ambient_light_raw': row.ambient_light_raw,
                    'active_lights_count': row.active_lights_count,
                    'faulty_lights_count': row.faulty_lights_count,
                    'is_dark': row.is_dark,
                })
            
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return None
    
    def _store_predictions(
        self,
        db: Session,
        device_id: str,
        predictions: Dict[str, Any]
    ):
        """Store predictions in database"""
        try:
            import json
            
            # Store failure prediction
            if 'failure' in predictions and 'error' not in predictions['failure']:
                failure_pred = predictions['failure']
                ml_pred = MLPrediction(
                    device_id=device_id,
                    prediction_type='failure',
                    timestamp=datetime.utcnow(),
                    prediction_value=failure_pred.get('failure_probability'),
                    prediction_label='failure' if failure_pred.get('prediction') == 1 else 'normal',
                    confidence=failure_pred.get('probability'),
                    model_name='failure_predictor',
                    model_version='1.0',
                    features=json.dumps(failure_pred.get('key_features', {}))
                )
                db.add(ml_pred)
            
            # Store anomaly detection
            if 'anomaly' in predictions and 'error' not in predictions['anomaly']:
                anomaly_pred = predictions['anomaly']
                ml_pred = MLPrediction(
                    device_id=device_id,
                    prediction_type='anomaly',
                    timestamp=datetime.utcnow(),
                    prediction_value=anomaly_pred.get('anomaly_score'),
                    prediction_label='anomaly' if anomaly_pred.get('is_anomaly') else 'normal',
                    confidence=abs(anomaly_pred.get('anomaly_score', 0)),
                    model_name='anomaly_detector',
                    model_version='1.0'
                )
                db.add(ml_pred)
            
            # Store fault prediction (new)
            if 'fault' in predictions and 'error' not in predictions['fault']:
                fault_pred = predictions['fault']
                ml_pred = MLPrediction(
                    device_id=device_id,
                    prediction_type='fault',
                    timestamp=datetime.utcnow(),
                    prediction_value=fault_pred.get('fault_probability'),
                    prediction_label='fault' if fault_pred.get('is_fault_predicted') else 'normal',
                    confidence=fault_pred.get('fault_probability', 0),
                    model_name='fault_predictor',
                    model_version='1.0',
                    features=json.dumps(fault_pred.get('key_features', {}))
                )
                db.add(ml_pred)
                
                # Create alert if fault is predicted with high probability
                if fault_pred.get('fault_probability', 0) > 0.7:
                    from models.database import Alert
                    existing_alert = db.query(Alert).filter(
                        Alert.device_id == device_id,
                        Alert.alert_type == 'fault_prediction',
                        Alert.status == 'open'
                    ).first()
                    
                    if not existing_alert:
                        alert = Alert(
                            device_id=device_id,
                            alert_type='fault_prediction',
                            severity='high',
                            message=f"Fault predicted with {fault_pred.get('fault_probability', 0):.2%} probability. "
                                   f"Check light dampness and relay delay.",
                            latitude=None,  # Could be extracted from sensor_data if available
                            longitude=None
                        )
                        db.add(alert)
            
            db.commit()
        except Exception as e:
            logger.error(f"Error storing predictions: {e}")
            db.rollback()


