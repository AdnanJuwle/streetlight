"""
ML Data Collection Pipeline
Aggregates and prepares sensor data for ML training
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """Collect and prepare data for ML training"""
    
    def __init__(self, database_url: str = None):
        """Initialize data collector"""
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://streetlight:streetlight@localhost:5432/streetlight_db'
        )
        self.engine = create_engine(self.database_url)
    
    def collect_device_data(
        self,
        device_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        min_readings: int = 100
    ) -> pd.DataFrame:
        """
        Collect sensor data for a specific device
        
        Args:
            device_id: Device identifier
            start_date: Start date for data collection
            end_date: End date for data collection
            min_readings: Minimum number of readings required
        
        Returns:
            DataFrame with sensor data
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        query = text("""
            SELECT 
                id,
                device_id,
                timestamp,
                ambient_light,
                ambient_light_raw,
                gps_latitude,
                gps_longitude,
                gps_valid,
                lights_data,
                is_dark,
                active_lights_count,
                faulty_lights_count,
                created_at
            FROM sensor_data
            WHERE device_id = :device_id
            AND timestamp >= :start_date
            AND timestamp <= :end_date
            ORDER BY timestamp ASC
        """)
        
        df = pd.read_sql(
            query,
            self.engine,
            params={
                'device_id': device_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        if len(df) < min_readings:
            logger.warning(
                f"Only {len(df)} readings found for device {device_id}, "
                f"minimum {min_readings} required"
            )
            return pd.DataFrame()
        
        # Parse lights_data JSON
        if 'lights_data' in df.columns and not df['lights_data'].isna().all():
            df = self._parse_lights_data(df)
        
        logger.info(f"Collected {len(df)} readings for device {device_id}")
        return df
    
    def _parse_lights_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse JSON lights_data column into separate columns"""
        import json
        
        # Extract individual light data
        for i in range(4):  # 4 lights
            df[f'light_{i+1}_ldr'] = None
            df[f'light_{i+1}_ldr_raw'] = None
            df[f'light_{i+1}_ir'] = None
            df[f'light_{i+1}_state'] = None
            df[f'light_{i+1}_fault'] = None
        
        for idx, row in df.iterrows():
            if pd.notna(row['lights_data']):
                try:
                    lights = json.loads(row['lights_data'])
                    for light in lights:
                        light_id = light.get('id', 0)
                        if 1 <= light_id <= 4:
                            df.at[idx, f'light_{light_id}_ldr'] = light.get('ldr_value')
                            df.at[idx, f'light_{light_id}_ldr_raw'] = light.get('ldr_raw')
                            df.at[idx, f'light_{light_id}_ir'] = 1 if light.get('ir_sensor') else 0
                            df.at[idx, f'light_{light_id}_state'] = 1 if light.get('light_state') else 0
                            df.at[idx, f'light_{light_id}_fault'] = 1 if light.get('fault_detected') else 0
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse lights_data at index {idx}: {e}")
        
        return df
    
    def collect_all_devices_data(
        self,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, pd.DataFrame]:
        """Collect data for all devices"""
        # Get all device IDs
        query = text("SELECT DISTINCT device_id FROM sensor_data")
        devices_df = pd.read_sql(query, self.engine)
        device_ids = devices_df['device_id'].tolist()
        
        all_data = {}
        for device_id in device_ids:
            df = self.collect_device_data(device_id, start_date, end_date)
            if not df.empty:
                all_data[device_id] = df
        
        logger.info(f"Collected data for {len(all_data)} devices")
        return all_data
    
    def create_training_dataset(
        self,
        device_id: str = None,
        output_path: str = 'data/training_data.csv',
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """
        Create a training dataset from collected data
        
        Args:
            device_id: Specific device ID or None for all devices
            output_path: Path to save the dataset
            start_date: Start date for data collection
            end_date: End date for data collection
        
        Returns:
            DataFrame with training data
        """
        if device_id:
            df = self.collect_device_data(device_id, start_date, end_date)
        else:
            all_data = self.collect_all_devices_data(start_date, end_date)
            if not all_data:
                logger.error("No data collected")
                return pd.DataFrame()
            df = pd.concat(all_data.values(), ignore_index=True)
        
        if df.empty:
            logger.error("No data available for training dataset")
            return pd.DataFrame()
        
        # Save to CSV
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Training dataset saved to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        
        return df
    
    def get_failure_events(self, device_id: str = None) -> pd.DataFrame:
        """Get historical failure events for labeling"""
        query = text("""
            SELECT 
                a.id,
                a.device_id,
                a.alert_type,
                a.severity,
                a.light_id,
                a.created_at as failure_time,
                a.latitude,
                a.longitude
            FROM alerts a
            WHERE a.alert_type = 'fault'
            AND a.status = 'resolved'
        """)
        
        if device_id:
            query = text(str(query).replace('FROM alerts a', f'FROM alerts a WHERE a.device_id = \'{device_id}\' AND'))
        
        df = pd.read_sql(query, self.engine)
        logger.info(f"Found {len(df)} failure events")
        return df


def main():
    """Main entry point for data collection"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect data for ML training')
    parser.add_argument('--device-id', type=str, default=None,
                       help='Specific device ID or all devices if not specified')
    parser.add_argument('--output', type=str, default='data/training_data.csv',
                       help='Output CSV file path')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of historical data to collect')
    
    args = parser.parse_args()
    
    collector = DataCollector()
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=args.days)
    
    df = collector.create_training_dataset(
        device_id=args.device_id,
        output_path=args.output,
        start_date=start_date,
        end_date=end_date
    )
    
    if not df.empty:
        print(f"\nDataset Statistics:")
        print(f"Total records: {len(df)}")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Devices: {df['device_id'].nunique()}")
        print(f"\nColumns: {list(df.columns)}")


if __name__ == '__main__':
    main()


