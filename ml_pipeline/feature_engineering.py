"""
Feature Engineering for ML Models
Extract and create features from raw sensor data
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Engineer features from sensor data"""
    
    def __init__(self, window_size: int = 10):
        """
        Initialize feature engineer
        
        Args:
            window_size: Size of rolling window for temporal features
        """
        self.window_size = window_size
    
    def create_features(self, df: pd.DataFrame, target_col: str = None) -> pd.DataFrame:
        """
        Create features from raw sensor data
        
        Args:
            df: DataFrame with sensor data
            target_col: Target column name for supervised learning
        
        Returns:
            DataFrame with engineered features
        """
        if df.empty:
            return df
        
        # Sort by timestamp
        df = df.sort_values('timestamp').copy()
        df = df.reset_index(drop=True)
        
        # Basic features
        df = self._add_basic_features(df)
        
        # Temporal features
        df = self._add_temporal_features(df)
        
        # Rolling statistics
        df = self._add_rolling_features(df)
        
        # Light-specific features
        df = self._add_light_features(df)
        
        # Lag features
        df = self._add_lag_features(df)
        
        # Target variable (if provided)
        if target_col:
            df = self._create_target(df, target_col)
        
        # Remove rows with NaN values created by rolling windows
        initial_len = len(df)
        df = df.dropna()
        logger.info(f"Removed {initial_len - len(df)} rows with NaN values")
        
        return df
    
    def _add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic statistical features"""
        # Hour of day, day of week
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            df['is_night'] = ((df['hour'] >= 20) | (df['hour'] <= 6)).astype(int)
        
        # Ambient light features
        if 'ambient_light' in df.columns:
            df['ambient_light_squared'] = df['ambient_light'] ** 2
            df['ambient_light_log'] = np.log1p(df['ambient_light'])
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal/seasonal features"""
        if 'timestamp' not in df.columns:
            return df
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['time_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600
        
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling window statistics"""
        numeric_cols = ['ambient_light', 'active_lights_count', 'faulty_lights_count']
        
        for col in numeric_cols:
            if col in df.columns:
                # Rolling mean
                df[f'{col}_rolling_mean'] = df[col].rolling(window=self.window_size, min_periods=1).mean()
                # Rolling std
                df[f'{col}_rolling_std'] = df[col].rolling(window=self.window_size, min_periods=1).std()
                # Rolling min/max
                df[f'{col}_rolling_min'] = df[col].rolling(window=self.window_size, min_periods=1).min()
                df[f'{col}_rolling_max'] = df[col].rolling(window=self.window_size, min_periods=1).max()
                # Change from previous
                df[f'{col}_diff'] = df[col].diff()
                # Rate of change
                df[f'{col}_pct_change'] = df[col].pct_change()
        
        return df
    
    def _add_light_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features specific to individual lights"""
        # Aggregate light features
        light_cols = [f'light_{i+1}_ldr' for i in range(4)]
        light_fault_cols = [f'light_{i+1}_fault' for i in range(4)]
        light_state_cols = [f'light_{i+1}_state' for i in range(4)]
        
        # Count available light columns
        available_light_cols = [col for col in light_cols if col in df.columns]
        
        if available_light_cols:
            # Mean LDR across all lights
            df['mean_light_ldr'] = df[available_light_cols].mean(axis=1)
            # Std of LDR across lights (variance indicator)
            df['std_light_ldr'] = df[available_light_cols].std(axis=1)
            # Min/max LDR
            df['min_light_ldr'] = df[available_light_cols].min(axis=1)
            df['max_light_ldr'] = df[available_light_cols].max(axis=1)
        
        # Fault-related features
        available_fault_cols = [col for col in light_fault_cols if col in df.columns]
        if available_fault_cols:
            df['total_faults'] = df[available_fault_cols].sum(axis=1)
            df['fault_rate'] = df['total_faults'] / len(available_fault_cols)
        
        # State-related features
        available_state_cols = [col for col in light_state_cols if col in df.columns]
        if available_state_cols:
            df['total_active'] = df[available_state_cols].sum(axis=1)
            df['active_rate'] = df['total_active'] / len(available_state_cols)
        
        return df
    
    def _add_lag_features(self, df: pd.DataFrame, lags: List[int] = [1, 3, 6]) -> pd.DataFrame:
        """Add lagged features"""
        lag_cols = ['ambient_light', 'active_lights_count', 'faulty_lights_count']
        
        for col in lag_cols:
            if col in df.columns:
                for lag in lags:
                    df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        return df
    
    def _create_target(self, df: pd.DataFrame, target_type: str = 'failure') -> pd.DataFrame:
        """
        Create target variable for supervised learning
        
        Args:
            df: Input dataframe
            target_type: Type of target ('failure', 'anomaly', 'maintenance')
        """
        if target_type == 'failure':
            # Binary target: will there be a failure in the next N hours?
            # This is a simplified version - in practice, you'd use actual failure events
            if 'faulty_lights_count' in df.columns:
                # Create target: failure in next 6 hours
                df['target_failure'] = (
                    (df['faulty_lights_count'].shift(-6) > 0) |
                    (df['faulty_lights_count'].shift(-3) > 0)
                ).astype(int)
                # Fill NaN with 0 (no failure)
                df['target_failure'] = df['target_failure'].fillna(0)
        
        elif target_type == 'anomaly':
            # Anomaly detection target (unsupervised, but can create labels)
            if 'ambient_light' in df.columns:
                # Use z-score for anomaly detection
                mean = df['ambient_light'].mean()
                std = df['ambient_light'].std()
                df['target_anomaly'] = (np.abs(df['ambient_light'] - mean) > 2 * std).astype(int)
        
        return df
    
    def get_feature_columns(self, df: pd.DataFrame, exclude_targets: bool = True) -> List[str]:
        """Get list of feature columns (excluding targets and metadata)"""
        exclude_cols = [
            'id', 'device_id', 'timestamp', 'created_at', 'gps_latitude',
            'gps_longitude', 'gps_valid', 'lights_data', 'target_failure',
            'target_anomaly', 'time_string', 'received_at'
        ]
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if exclude_targets:
            feature_cols = [col for col in feature_cols if not col.startswith('target_')]
        
        return feature_cols


