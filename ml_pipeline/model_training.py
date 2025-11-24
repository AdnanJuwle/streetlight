"""
ML Model Training Pipeline
Train predictive maintenance and anomaly detection models
"""

import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime
from typing import Dict, Any, Tuple
import logging

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

from feature_engineering import FeatureEngineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train ML models for predictive maintenance"""
    
    def __init__(self, model_dir: str = 'models'):
        """Initialize model trainer"""
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.feature_engineer = FeatureEngineer()
    
    def train_failure_prediction_model(
        self,
        data_path: str,
        model_name: str = 'failure_predictor'
    ) -> Dict[str, Any]:
        """Train failure prediction model"""
        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
        
        if df.empty:
            raise ValueError("Empty dataset provided")
        
        # Engineer features
        logger.info("Engineering features...")
        df = self.feature_engineer.create_features(df, target_col='failure')
        
        # Get feature columns
        feature_cols = self.feature_engineer.get_feature_columns(df)
        
        if 'target_failure' not in df.columns:
            logger.warning("No target_failure column found, creating synthetic target")
            df['target_failure'] = (df['faulty_lights_count'] > 0).astype(int)
        
        # Prepare data
        X = df[feature_cols].fillna(0)
        y = df['target_failure']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        logger.info("Training Random Forest model...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Model accuracy: {accuracy:.4f}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Save model
        model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
        joblib.dump(model, model_path)
        
        # Save feature columns
        feature_path = os.path.join(self.model_dir, f'{model_name}_features.pkl')
        joblib.dump(feature_cols, feature_path)
        
        logger.info(f"Model saved to {model_path}")
        
        return {
            'model_path': model_path,
            'feature_path': feature_path,
            'accuracy': accuracy,
            'feature_count': len(feature_cols),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def train_anomaly_detection_model(
        self,
        data_path: str,
        model_name: str = 'anomaly_detector'
    ) -> Dict[str, Any]:
        """Train anomaly detection model"""
        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
        
        if df.empty:
            raise ValueError("Empty dataset provided")
        
        # Engineer features
        logger.info("Engineering features...")
        df = self.feature_engineer.create_features(df)
        
        # Get feature columns
        feature_cols = self.feature_engineer.get_feature_columns(df)
        
        # Prepare data
        X = df[feature_cols].fillna(0)
        
        # Train model
        logger.info("Training Isolation Forest model...")
        model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X)
        
        # Save model
        model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
        joblib.dump(model, model_path)
        
        # Save feature columns
        feature_path = os.path.join(self.model_dir, f'{model_name}_features.pkl')
        joblib.dump(feature_cols, feature_path)
        
        logger.info(f"Model saved to {model_path}")
        
        return {
            'model_path': model_path,
            'feature_path': feature_path,
            'feature_count': len(feature_cols),
            'training_samples': len(X)
        }


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML models')
    parser.add_argument('--data', type=str, default='data/training_data.csv',
                       help='Path to training data CSV')
    parser.add_argument('--model-type', type=str, choices=['failure', 'anomaly', 'both'],
                       default='both', help='Type of model to train')
    parser.add_argument('--model-dir', type=str, default='models',
                       help='Directory to save models')
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(model_dir=args.model_dir)
    
    if args.model_type in ['failure', 'both']:
        logger.info("Training failure prediction model...")
        trainer.train_failure_prediction_model(args.data)
    
    if args.model_type in ['anomaly', 'both']:
        logger.info("Training anomaly detection model...")
        trainer.train_anomaly_detection_model(args.data)


if __name__ == '__main__':
    main()


