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
        light_ir_cols = [f'light_{i+1}_ir' for i in range(4)]
        
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
        
        # Add light dampness and turn-on delay features for each light
        for i in range(4):
            light_id = i + 1
            ldr_col = f'light_{light_id}_ldr'
            state_col = f'light_{light_id}_state'
            ir_col = f'light_{light_id}_ir'
            
            if all(col in df.columns for col in [ldr_col, state_col, ir_col]):
                # Light dampness: LDR2 value when light should be on
                # Higher LDR value = less light detected = more dampness/fault
                # Only calculate when light_state is True (light should be on)
                df[f'light_{light_id}_dampness'] = np.where(
                    df[state_col] == 1,  # Light should be on
                    df[ldr_col],  # LDR2 reading (higher = less light = more dampness)
                    0  # No dampness when light is off
                )
                
                # Average dampness over rolling window (for trend analysis)
                df[f'light_{light_id}_dampness_rolling_mean'] = (
                    df[f'light_{light_id}_dampness']
                    .rolling(window=self.window_size, min_periods=1)
                    .mean()
                )
                
                # Turn-on delay: Time between IR detection and light actually turning on
                # This indicates relay aging
                df[f'light_{light_id}_turn_on_delay'] = self._calculate_turn_on_delay(
                    df, ir_col, state_col, ldr_col
                )
                
                # Average delay over rolling window
                df[f'light_{light_id}_delay_rolling_mean'] = (
                    df[f'light_{light_id}_turn_on_delay']
                    .rolling(window=self.window_size, min_periods=1)
                    .mean()
                )
        
        # Aggregate dampness and delay features across all lights
        dampness_cols = [f'light_{i+1}_dampness' for i in range(4) 
                        if f'light_{i+1}_dampness' in df.columns]
        delay_cols = [f'light_{i+1}_turn_on_delay' for i in range(4) 
                     if f'light_{i+1}_turn_on_delay' in df.columns]
        
        if dampness_cols:
            df['mean_dampness'] = df[dampness_cols].mean(axis=1)
            df['max_dampness'] = df[dampness_cols].max(axis=1)
        
        if delay_cols:
            df['mean_turn_on_delay'] = df[delay_cols].mean(axis=1)
            df['max_turn_on_delay'] = df[delay_cols].max(axis=1)
        
        return df
    
    def _calculate_turn_on_delay(
        self, 
        df: pd.DataFrame, 
        ir_col: str, 
        state_col: str, 
        ldr_col: str
    ) -> pd.Series:
        """
        Calculate turn-on delay: time between IR detection and light actually turning on.
        This indicates relay aging.
        
        Returns:
            Series with delay values in seconds (0 if no delay detected)
        """
        delay = pd.Series(0.0, index=df.index)
        
        if len(df) < 2:
            return delay
        
        # Convert timestamp to numeric for time calculations
        timestamp_numeric = None
        if 'timestamp' in df.columns:
            try:
                timestamp_numeric = pd.to_datetime(df['timestamp']).astype('int64') / 1e9  # Convert to seconds
            except:
                timestamp_numeric = None
        
        if timestamp_numeric is None:
            # If no timestamp, use index as proxy (assuming regular intervals)
            timestamp_numeric = pd.Series(df.index * 5, index=df.index)  # Assume 5 second intervals
        
        # Track when IR sensor detects vehicle (transition from 0 to 1 or low to high)
        ir_detected = (df[ir_col] == 1) & (df[ir_col].shift(1).fillna(0) == 0)
        
        # Also track when state transitions from 0 to 1 (light turns on)
        state_turned_on = (df[state_col] == 1) & (df[state_col].shift(1).fillna(0) == 0)
        
        # For each IR detection, find when light actually turns on
        for idx in df[ir_detected].index:
            if idx >= len(df) - 1:
                continue
                
            # Look ahead to find when light_state becomes 1 or LDR shows light is on
            # LDR value decreases when light is on (lower value = more light)
            look_ahead = min(20, len(df) - idx - 1)  # Look ahead up to 20 readings
            
            light_on_idx = None
            initial_ldr = df.loc[idx, ldr_col] if pd.notna(df.loc[idx, ldr_col]) else 100
            
            for offset in range(1, look_ahead + 1):
                future_idx = idx + offset
                if future_idx >= len(df):
                    break
                
                # Light is on if state is 1 or LDR value dropped significantly
                future_state = df.loc[future_idx, state_col]
                future_ldr = df.loc[future_idx, ldr_col] if pd.notna(df.loc[future_idx, ldr_col]) else initial_ldr
                
                if future_state == 1:
                    light_on_idx = future_idx
                    break
                elif pd.notna(future_ldr) and (initial_ldr - future_ldr) > 10:  # LDR dropped by 10
                    light_on_idx = future_idx
                    break
            
            if light_on_idx:
                # Calculate delay in seconds
                try:
                    time_diff = timestamp_numeric.iloc[light_on_idx] - timestamp_numeric.iloc[idx]
                    delay.loc[idx] = max(0, time_diff)
                except:
                    delay.loc[idx] = 0
        
        # Alternative: Calculate delay based on state transitions when IR was recently detected
        # This works even if we don't have future data
        for idx in df[state_turned_on].index:
            if idx == 0:
                continue
            
            # Look back to see if IR was detected recently
            look_back = min(10, idx)
            for offset in range(1, look_back + 1):
                past_idx = idx - offset
                if df.loc[past_idx, ir_col] == 1:
                    # IR was detected, calculate delay
                    try:
                        time_diff = timestamp_numeric.iloc[idx] - timestamp_numeric.iloc[past_idx]
                        if delay.loc[past_idx] == 0:  # Only update if not already set
                            delay.loc[past_idx] = max(0, time_diff)
                    except:
                        pass
                    break
        
        return delay
    
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


