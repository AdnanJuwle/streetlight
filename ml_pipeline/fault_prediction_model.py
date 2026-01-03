"""
Focused Fault Prediction Model
Uses only light dampness (LDR2) and turn-on delay to predict failure probability
"""

import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaultPredictionModel:
    """
    Simplified fault prediction model using only:
    1. Light dampness (LDR2 reading when light should be on)
    2. Turn-on delay (time between command and light actually turning on)
    """
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.model = None
        self.scaler = None
        self.feature_names = ['light_dampness', 'turn_on_delay']
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract only the two key features: dampness and delay
        
        Args:
            df: DataFrame with sensor data (must have light data parsed)
        
        Returns:
            DataFrame with feature columns
        """
        features_df = pd.DataFrame()
        
        # For each light, extract dampness and delay
        for light_id in range(1, 5):
            ldr_col = f'light_{light_id}_ldr'
            state_col = f'light_{light_id}_state'
            ir_col = f'light_{light_id}_ir'
            delay_col = f'light_{light_id}_turn_on_delay_ms'  # Pre-calculated delay from Arduino
            
            if all(col in df.columns for col in [ldr_col, state_col, ir_col]):
                # Light dampness: LDR2 value when light should be on
                dampness = np.where(
                    df[state_col] == 1,  # Light is on
                    df[ldr_col],  # LDR2 reading (higher = less light = more dampness)
                    0  # No dampness when light is off
                )
                
                # Turn-on delay: Use Arduino-provided delay if available, otherwise calculate
                if delay_col in df.columns and not df[delay_col].isna().all():
                    # Use Arduino-provided delay (already in seconds)
                    delay = df[delay_col].fillna(0).values
                else:
                    # Calculate delay from historical data
                    delay = self._calculate_delay_for_light(
                        df, ir_col, state_col, ldr_col
                    )
                
                # Use maximum dampness and delay across all lights for this reading
                if f'light_dampness' not in features_df.columns:
                    features_df['light_dampness'] = dampness
                    features_df['turn_on_delay'] = delay
                else:
                    features_df['light_dampness'] = np.maximum(
                        features_df['light_dampness'], dampness
                    )
                    features_df['turn_on_delay'] = np.maximum(
                        features_df['turn_on_delay'], delay
                    )
        
        return features_df
    
    def _calculate_delay_for_light(
        self, 
        df: pd.DataFrame, 
        ir_col: str, 
        state_col: str, 
        ldr_col: str
    ) -> np.ndarray:
        """Calculate turn-on delay for a single light"""
        delay = np.zeros(len(df))
        
        if len(df) < 2:
            return delay
        
        # Convert timestamp if available
        if 'timestamp' in df.columns:
            try:
                timestamps = pd.to_datetime(df['timestamp']).astype('int64') / 1e9
            except:
                timestamps = pd.Series(df.index * 5, index=df.index)
        else:
            timestamps = pd.Series(df.index * 5, index=df.index)
        
        # Find IR detections (transition from 0 to 1)
        ir_detected = (df[ir_col] == 1) & (df[ir_col].shift(1).fillna(0) == 0)
        
        # Find when light turns on (state transition from 0 to 1)
        state_turned_on = (df[state_col] == 1) & (df[state_col].shift(1).fillna(0) == 0)
        
        # For each IR detection, find when light actually turns on
        for idx in df[ir_detected].index:
            if idx >= len(df) - 1:
                continue
            
            look_ahead = min(20, len(df) - idx - 1)
            initial_ldr = df.loc[idx, ldr_col] if pd.notna(df.loc[idx, ldr_col]) else 100
            
            for offset in range(1, look_ahead + 1):
                future_idx = idx + offset
                if future_idx >= len(df):
                    break
                
                future_state = df.loc[future_idx, state_col]
                future_ldr = df.loc[future_idx, ldr_col] if pd.notna(df.loc[future_idx, ldr_col]) else initial_ldr
                
                if future_state == 1 or (initial_ldr - future_ldr) > 10:
                    # Light turned on - calculate delay
                    time_diff = timestamps.iloc[future_idx] - timestamps.iloc[idx]
                    delay[idx] = max(0, time_diff)
                    break
        
        # Also check state transitions when IR was recently detected
        for idx in df[state_turned_on].index:
            if idx == 0:
                continue
            
            look_back = min(10, idx)
            for offset in range(1, look_back + 1):
                past_idx = idx - offset
                if df.loc[past_idx, ir_col] == 1:
                    time_diff = timestamps.iloc[idx] - timestamps.iloc[past_idx]
                    if delay[past_idx] == 0:
                        delay[past_idx] = max(0, time_diff)
                    break
        
        return delay
    
    def create_target(self, df: pd.DataFrame, look_ahead_hours: int = 24) -> pd.Series:
        """
        Create target: will there be a fault in the next N hours?
        
        Args:
            df: DataFrame with sensor data
            look_ahead_hours: How many hours ahead to predict
        
        Returns:
            Series with binary target (1 = fault in future, 0 = no fault)
        """
        target = pd.Series(0, index=df.index)
        
        # Convert hours to number of readings (assuming 5-minute intervals)
        look_ahead_readings = int(look_ahead_hours * 60 / 5)
        
        # Check for faults in the future
        fault_cols = [f'light_{i+1}_fault' for i in range(4) 
                     if f'light_{i+1}_fault' in df.columns]
        
        if fault_cols:
            for idx in df.index:
                if idx + look_ahead_readings < len(df):
                    future_window = df.loc[idx+1:idx+look_ahead_readings]
                    if (future_window[fault_cols].sum(axis=1) > 0).any():
                        target.loc[idx] = 1
        else:
            # Fallback: use faulty_lights_count
            if 'faulty_lights_count' in df.columns:
                for idx in df.index:
                    if idx + look_ahead_readings < len(df):
                        future_window = df.loc[idx+1:idx+look_ahead_readings]
                        if (future_window['faulty_lights_count'] > 0).any():
                            target.loc[idx] = 1
        
        return target
    
    def train(
        self, 
        data_path: str, 
        model_type: str = 'logistic',
        look_ahead_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Train the fault prediction model
        
        Args:
            data_path: Path to training data CSV
            model_type: 'logistic' or 'tree'
            look_ahead_hours: Hours ahead to predict failure
        
        Returns:
            Training results
        """
        logger.info(f"Loading data from {data_path}")
        df = pd.read_csv(data_path)
        
        if df.empty:
            raise ValueError("Empty dataset provided")
        
        # Parse lights data if needed
        if 'lights_data' in df.columns:
            try:
                from data_collection import DataCollector
            except ImportError:
                from ml_pipeline.data_collection import DataCollector
            collector = DataCollector()
            df = collector._parse_lights_data(df)
        
        # Prepare features (only dampness and delay)
        logger.info("Extracting features (dampness and delay)...")
        features_df = self.prepare_features(df)
        
        if features_df.empty or 'light_dampness' not in features_df.columns:
            raise ValueError("Could not extract dampness/delay features. Check data format.")
        
        # Create target: fault in next N hours
        logger.info(f"Creating target: fault in next {look_ahead_hours} hours...")
        y = self.create_target(df, look_ahead_hours)
        
        # Prepare data
        X = features_df[self.feature_names].fillna(0)
        
        # Remove rows where both features are 0 (no meaningful data)
        valid_mask = (X['light_dampness'] > 0) | (X['turn_on_delay'] > 0)
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(X) == 0:
            raise ValueError("No valid feature data after filtering")
        
        logger.info(f"Training samples: {len(X)}")
        logger.info(f"Class distribution: {y.value_counts().to_dict()}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, 
            stratify=y if len(y.value_counts()) > 1 else None
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if model_type == 'logistic':
            logger.info("Training Logistic Regression model...")
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                class_weight='balanced'
            )
            self.model.fit(X_train_scaled, y_train)
            X_test_final = X_test_scaled
        elif model_type == 'tree':
            logger.info("Training Decision Tree model...")
            self.model = DecisionTreeClassifier(
                max_depth=8,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                class_weight='balanced'
            )
            self.model.fit(X_train, y_train)
            X_test_final = X_test.values
            self.scaler = None  # Trees don't need scaling
        else:
            raise ValueError(f"Unknown model_type: {model_type}")
        
        # Evaluate
        y_pred = self.model.predict(X_test_final)
        accuracy = accuracy_score(y_test, y_pred)
        
        try:
            if hasattr(self.model, 'predict_proba'):
                y_proba = self.model.predict_proba(X_test_final)[:, 1]
                auc = roc_auc_score(y_test, y_proba)
            else:
                auc = None
        except:
            auc = None
        
        logger.info(f"Model accuracy: {accuracy:.4f}")
        if auc:
            logger.info(f"Model AUC: {auc:.4f}")
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred))
        
        # Save model
        model_path = os.path.join(self.model_dir, 'fault_predictor_simple.pkl')
        joblib.dump(self.model, model_path)
        
        if self.scaler:
            scaler_path = os.path.join(self.model_dir, 'fault_predictor_simple_scaler.pkl')
            joblib.dump(self.scaler, scaler_path)
        
        logger.info(f"Model saved to {model_path}")
        
        return {
            'model_path': model_path,
            'accuracy': accuracy,
            'auc': auc,
            'feature_names': self.feature_names,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def predict(self, light_dampness: float, turn_on_delay: float) -> Dict[str, Any]:
        """
        Predict failure probability given light dampness and turn-on delay
        
        Args:
            light_dampness: LDR2 reading when light should be on (higher = more dampness)
            turn_on_delay: Delay in seconds between command and light turning on
        
        Returns:
            Dictionary with prediction results
        """
        if not self.model:
            return {'error': 'Model not loaded'}
        
        # Prepare features
        X = pd.DataFrame([[light_dampness, turn_on_delay]], columns=self.feature_names)
        
        # Scale if needed
        if self.scaler:
            X = self.scaler.transform(X)
        else:
            X = X.values
        
        # Predict
        prediction = self.model.predict(X)[0]
        
        if hasattr(self.model, 'predict_proba'):
            probability = self.model.predict_proba(X)[0]
            failure_probability = float(probability[1] if len(probability) > 1 else probability[0])
        else:
            failure_probability = float(prediction)
        
        return {
            'will_fail': bool(prediction == 1),
            'failure_probability': failure_probability,
            'light_dampness': light_dampness,
            'turn_on_delay': turn_on_delay,
            'interpretation': self._interpret_prediction(light_dampness, turn_on_delay, failure_probability)
        }
    
    def _interpret_prediction(
        self, 
        dampness: float, 
        delay: float, 
        probability: float
    ) -> str:
        """Provide human-readable interpretation"""
        issues = []
        
        if dampness > 60:
            issues.append(f"High light dampness ({dampness:.1f}) - bulb may be failing")
        elif dampness > 40:
            issues.append(f"Moderate light dampness ({dampness:.1f}) - monitor closely")
        
        if delay > 5:
            issues.append(f"Significant relay delay ({delay:.1f}s) - relay aging detected")
        elif delay > 2:
            issues.append(f"Moderate relay delay ({delay:.1f}s) - early signs of aging")
        
        if probability > 0.7:
            severity = "HIGH"
        elif probability > 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        interpretation = f"Failure risk: {severity} ({probability:.1%})"
        if issues:
            interpretation += f". Issues: {'; '.join(issues)}"
        
        return interpretation
    
    def load(self, model_path: str = None):
        """Load trained model"""
        if model_path is None:
            model_path = os.path.join(self.model_dir, 'fault_predictor_simple.pkl')
        
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            
            scaler_path = os.path.join(self.model_dir, 'fault_predictor_simple_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            
            logger.info("Model loaded successfully")
        else:
            logger.warning(f"Model not found at {model_path}")


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train focused fault prediction model')
    parser.add_argument('--data', type=str, default='data/training_data.csv',
                       help='Path to training data CSV')
    parser.add_argument('--model-type', type=str, choices=['logistic', 'tree'],
                       default='logistic', help='Type of model to train')
    parser.add_argument('--look-ahead', type=int, default=24,
                       help='Hours ahead to predict failure')
    parser.add_argument('--model-dir', type=str, default='models',
                       help='Directory to save models')
    
    args = parser.parse_args()
    
    trainer = FaultPredictionModel(model_dir=args.model_dir)
    results = trainer.train(
        args.data, 
        model_type=args.model_type,
        look_ahead_hours=args.look_ahead
    )
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print(f"Model accuracy: {results['accuracy']:.4f}")
    if results.get('auc'):
        print(f"Model AUC: {results['auc']:.4f}")
    print(f"Features used: {results['feature_names']}")
    print(f"Model saved to: {results['model_path']}")


if __name__ == '__main__':
    main()

