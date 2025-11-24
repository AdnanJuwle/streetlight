"""
Advanced Analytics Service
Traffic pattern analysis, energy optimization, and reporting
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import logging

from models.database import SensorData, EnergyConsumption

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced analytics"""
    
    @staticmethod
    def analyze_traffic_patterns(
        db: Session,
        device_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Analyze traffic/usage patterns from IR sensor data"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sensor data
        query = db.query(SensorData).filter(
            SensorData.device_id == device_id,
            SensorData.timestamp >= start_date
        ).all()
        
        if not query:
            return {'error': 'No data available'}
        
        # Convert to DataFrame
        data = []
        for row in query:
            if row.lights_data:
                import json
                try:
                    lights = json.loads(row.lights_data)
                    for light in lights:
                        data.append({
                            'timestamp': row.timestamp,
                            'hour': row.timestamp.hour,
                            'day_of_week': row.timestamp.weekday(),
                            'ir_detected': 1 if light.get('ir_sensor') else 0,
                            'light_id': light.get('id')
                        })
                except:
                    pass
        
        if not data:
            return {'error': 'No traffic data available'}
        
        df = pd.DataFrame(data)
        
        # Hourly patterns
        hourly_pattern = df.groupby('hour')['ir_detected'].sum().to_dict()
        
        # Daily patterns
        daily_pattern = df.groupby('day_of_week')['ir_detected'].sum().to_dict()
        
        # Peak hours
        peak_hour = df.groupby('hour')['ir_detected'].sum().idxmax()
        
        # Average activity
        avg_activity = df['ir_detected'].mean()
        
        return {
            'hourly_pattern': hourly_pattern,
            'daily_pattern': daily_pattern,
            'peak_hour': int(peak_hour),
            'average_activity': float(avg_activity),
            'total_detections': int(df['ir_detected'].sum())
        }
    
    @staticmethod
    def calculate_energy_consumption(
        db: Session,
        device_id: str,
        days: int = 7,
        watts_per_light: float = 50.0,
        cost_per_kwh: float = 0.12
    ) -> Dict[str, Any]:
        """Calculate energy consumption and costs"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(SensorData).filter(
            SensorData.device_id == device_id,
            SensorData.timestamp >= start_date
        ).order_by(SensorData.timestamp.asc()).all()
        
        if not query:
            return {'error': 'No data available'}
        
        total_energy = 0.0
        total_cost = 0.0
        hourly_consumption = {}
        
        for i, row in enumerate(query):
            if row.active_lights_count:
                # Calculate energy for this period
                if i > 0:
                    prev_row = query[i-1]
                    time_diff = (row.timestamp - prev_row.timestamp).total_seconds() / 3600.0
                else:
                    time_diff = 0.1  # Default 0.1 hours for first reading
                
                power_watts = row.active_lights_count * watts_per_light
                energy_kwh = (power_watts / 1000.0) * time_diff
                cost = energy_kwh * cost_per_kwh
                
                total_energy += energy_kwh
                total_cost += cost
                
                # Track hourly consumption
                hour = row.timestamp.hour
                if hour not in hourly_consumption:
                    hourly_consumption[hour] = 0.0
                hourly_consumption[hour] += energy_kwh
        
        return {
            'total_energy_kwh': round(total_energy, 2),
            'total_cost': round(total_cost, 2),
            'average_daily_energy': round(total_energy / days, 2),
            'average_daily_cost': round(total_cost / days, 2),
            'hourly_consumption': {str(k): round(v, 2) for k, v in hourly_consumption.items()},
            'estimated_monthly_cost': round((total_cost / days) * 30, 2)
        }
    
    @staticmethod
    def optimize_energy(
        db: Session,
        device_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Suggest energy optimization strategies"""
        traffic_patterns = AnalyticsService.analyze_traffic_patterns(db, device_id, days)
        energy_data = AnalyticsService.calculate_energy_consumption(db, device_id, days)
        
        if 'error' in traffic_patterns or 'error' in energy_data:
            return {'error': 'Insufficient data for optimization'}
        
        suggestions = []
        potential_savings = 0.0
        
        # Suggestion 1: Dimming during low-traffic hours
        low_traffic_hours = [h for h, count in traffic_patterns['hourly_pattern'].items() 
                            if count < traffic_patterns['average_activity'] * 0.5]
        if low_traffic_hours:
            suggestions.append({
                'type': 'dimming',
                'description': f'Reduce brightness during low-traffic hours: {low_traffic_hours}',
                'potential_savings_percent': 20
            })
            potential_savings += energy_data['average_daily_cost'] * 0.2
        
        # Suggestion 2: Adaptive timing
        peak_hour = traffic_patterns.get('peak_hour', 20)
        suggestions.append({
            'type': 'adaptive_timing',
            'description': f'Optimize activation timing based on peak hour ({peak_hour}:00)',
            'potential_savings_percent': 10
        })
        potential_savings += energy_data['average_daily_cost'] * 0.1
        
        return {
            'suggestions': suggestions,
            'estimated_daily_savings': round(potential_savings, 2),
            'estimated_monthly_savings': round(potential_savings * 30, 2),
            'current_daily_cost': energy_data['average_daily_cost']
        }
    
    @staticmethod
    def generate_report(
        db: Session,
        device_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        traffic = AnalyticsService.analyze_traffic_patterns(db, device_id, days)
        energy = AnalyticsService.calculate_energy_consumption(db, device_id, days)
        optimization = AnalyticsService.optimize_energy(db, device_id, days)
        
        # Get fault statistics
        from models.database import Alert
        fault_count = db.query(Alert).filter(
            Alert.device_id == device_id,
            Alert.alert_type == 'fault',
            Alert.created_at >= datetime.utcnow() - timedelta(days=days)
        ).count()
        
        return {
            'device_id': device_id,
            'report_period_days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'traffic_analysis': traffic,
            'energy_analysis': energy,
            'optimization': optimization,
            'fault_count': fault_count,
            'uptime_percent': 100.0 - (fault_count / days * 100) if days > 0 else 100.0
        }


