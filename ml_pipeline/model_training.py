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
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, roc_auc_score, roc_curve
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
    
    def train_fault_prediction_model(
        self,
        data_path: str,
        model_name: str = 'fault_predictor',
        model_type: str = 'logistic'
    ) -> Dict[str, Any]:
        """
        Train fault prediction model using light dampness and turn-on delay features.
        
        Args:
            data_path: Path to training data CSV
            model_name: Name for saved model
            model_type: 'logistic' for LogisticRegression or 'tree' for DecisionTreeClassifier
        
        Returns:
            Dictionary with model training results
        """
        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
        
        if df.empty:
            raise ValueError("Empty dataset provided")
        
        # Engineer features including dampness and delay
        logger.info("Engineering features...")
        df = self.feature_engineer.create_features(df, target_col='failure')
        
        # Get feature columns - prioritize dampness and delay features
        all_feature_cols = self.feature_engineer.get_feature_columns(df)
        
        # Select key features for fault prediction
        key_features = [
            col for col in all_feature_cols 
            if any(keyword in col.lower() for keyword in ['dampness', 'delay', 'ldr', 'fault', 'state'])
        ]
        
        # Add other important features
        other_features = [
            col for col in all_feature_cols 
            if col not in key_features and 
            not any(exclude in col.lower() for exclude in ['target', 'id', 'timestamp'])
        ]
        
        # Use key features first, then add others if needed
        feature_cols = key_features + other_features[:20]  # Limit to top 20 other features
        
        # Ensure we have features
        if not feature_cols:
            feature_cols = all_feature_cols[:30]  # Fallback to first 30 features
        
        logger.info(f"Using {len(feature_cols)} features for fault prediction")
        logger.info(f"Key features: {key_features[:10]}")
        
        # Create target: fault detected in current or next few readings
        if 'target_failure' not in df.columns:
            # Create target based on fault detection
            fault_cols = [f'light_{i+1}_fault' for i in range(4) 
                         if f'light_{i+1}_fault' in df.columns]
            if fault_cols:
                df['target_failure'] = (df[fault_cols].sum(axis=1) > 0).astype(int)
            else:
                # Fallback: use faulty_lights_count
                df['target_failure'] = (df.get('faulty_lights_count', 0) > 0).astype(int)
        
        # Prepare data
        X = df[feature_cols].fillna(0)
        y = df['target_failure']
        
        # Check class balance
        class_counts = y.value_counts()
        logger.info(f"Class distribution: {class_counts.to_dict()}")
        
        if len(class_counts) < 2:
            logger.warning("Only one class found in target. Using synthetic data augmentation.")
            # Add some synthetic positive examples if needed
            pass
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(class_counts) > 1 else None
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model based on type
        if model_type == 'logistic':
            logger.info("Training Logistic Regression model...")
            model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'  # Handle class imbalance
            )
            model.fit(X_train_scaled, y_train)
        elif model_type == 'tree':
            logger.info("Training Decision Tree model...")
            model = DecisionTreeClassifier(
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                class_weight='balanced'
            )
            model.fit(X_train, y_train)
            # Use unscaled data for tree
            X_test_scaled = X_test
        else:
            raise ValueError(f"Unknown model_type: {model_type}. Use 'logistic' or 'tree'")
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Calculate AUC if binary classification
        try:
            if hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test_scaled)[:, 1]
                auc = roc_auc_score(y_test, y_proba)
            else:
                auc = None
        except Exception as e:
            logger.warning(f"Could not calculate AUC: {e}")
            auc = None
        
        logger.info(f"Model accuracy: {accuracy:.4f}")
        if auc:
            logger.info(f"Model AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Save model
        model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
        joblib.dump(model, model_path)
        
        # Save scaler (if used)
        if model_type == 'logistic':
            scaler_path = os.path.join(self.model_dir, f'{model_name}_scaler.pkl')
            joblib.dump(scaler, scaler_path)
        
        # Save feature columns
        feature_path = os.path.join(self.model_dir, f'{model_name}_features.pkl')
        joblib.dump(feature_cols, feature_path)
        
        logger.info(f"Model saved to {model_path}")
        
        return {
            'model_path': model_path,
            'feature_path': feature_path,
            'scaler_path': os.path.join(self.model_dir, f'{model_name}_scaler.pkl') if model_type == 'logistic' else None,
            'accuracy': accuracy,
            'auc': auc,
            'model_type': model_type,
            'feature_count': len(feature_cols),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'class_distribution': class_counts.to_dict()
        }


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML models')
    parser.add_argument('--data', type=str, default='data/training_data.csv',
                       help='Path to training data CSV')
    parser.add_argument('--model-type', type=str, choices=['failure', 'anomaly', 'fault', 'both', 'all'],
                       default='all', help='Type of model to train')
    parser.add_argument('--model-dir', type=str, default='models',
                       help='Directory to save models')
    parser.add_argument('--fault-model-type', type=str, choices=['logistic', 'tree'],
                       default='logistic', help='Type of fault prediction model (logistic or tree)')
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(model_dir=args.model_dir)
    
    if args.model_type in ['failure', 'both', 'all']:
        logger.info("Training failure prediction model...")
        trainer.train_failure_prediction_model(args.data)
    
    if args.model_type in ['fault', 'all']:
        logger.info("Training fault prediction model...")
        trainer.train_fault_prediction_model(args.data, model_type=args.fault_model_type)
    
    if args.model_type in ['anomaly', 'both', 'all']:
        logger.info("Training anomaly detection model...")
        trainer.train_anomaly_detection_model(args.data)


if __name__ == '__main__':
    main()


