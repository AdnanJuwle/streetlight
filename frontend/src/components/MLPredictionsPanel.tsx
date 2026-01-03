'use client';

import { useEffect, useState } from 'react';
import { api, MLPrediction } from '@/lib/api';

interface MLPredictionsPanelProps {
  deviceId: string;
}

export default function MLPredictionsPanel({ deviceId }: MLPredictionsPanelProps) {
  const [predictions, setPredictions] = useState<MLPrediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPredictions();
    const interval = setInterval(loadPredictions, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [deviceId]);

  const loadPredictions = async () => {
    try {
      const data = await api.getMLPredictions(deviceId);
      // Get latest prediction for each type
      const latestByType = new Map<string, MLPrediction>();
      data.forEach((pred) => {
        const existing = latestByType.get(pred.prediction_type);
        if (!existing || new Date(pred.timestamp) > new Date(existing.timestamp)) {
          latestByType.set(pred.prediction_type, pred);
        }
      });
      setPredictions(Array.from(latestByType.values()));
      setLoading(false);
    } catch (error) {
      console.error('Failed to load predictions:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading predictions...</div>;
  }

  if (predictions.length === 0) {
    return <div style={{ color: '#666' }}>No ML predictions available yet. Train the model first.</div>;
  }

  const getPredictionColor = (type: string, value?: number) => {
    if (type === 'fault') {
      if (value && value > 0.7) return '#ef4444'; // Red for high fault probability
      if (value && value > 0.4) return '#f59e0b'; // Orange for medium
      return '#10b981'; // Green for low
    }
    if (type === 'failure') {
      if (value && value > 0.5) return '#ef4444';
      return '#10b981';
    }
    return '#6b7280';
  };

  const getPredictionLabel = (pred: MLPrediction) => {
    if (pred.prediction_type === 'fault') {
      const prob = pred.prediction_value || 0;
      return `${(prob * 100).toFixed(1)}% fault probability`;
    }
    if (pred.prediction_type === 'failure') {
      const prob = pred.prediction_value || 0;
      return `${(prob * 100).toFixed(1)}% failure probability`;
    }
    if (pred.prediction_type === 'anomaly') {
      return pred.prediction_label === 'anomaly' ? 'Anomaly Detected' : 'Normal';
    }
    return pred.prediction_label || 'Unknown';
  };

  return (
    <div>
      <div style={{ display: 'grid', gap: '15px' }}>
        {predictions.map((pred) => {
          const color = getPredictionColor(pred.prediction_type, pred.prediction_value);
          const label = getPredictionLabel(pred);
          
          return (
            <div
              key={pred.id}
              style={{
                padding: '15px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                borderLeft: `4px solid ${color}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
                <div>
                  <div style={{ fontWeight: 'bold', marginBottom: '5px', textTransform: 'capitalize' }}>
                    {pred.prediction_type} Prediction
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color }}>
                    {label}
                  </div>
                </div>
                {pred.confidence && (
                  <div style={{ fontSize: '0.875rem', color: '#666' }}>
                    Confidence: {(pred.confidence * 100).toFixed(1)}%
                  </div>
                )}
              </div>
              
              <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '8px' }}>
                Model: {pred.model_name || 'N/A'} v{pred.model_version || 'N/A'}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#999' }}>
                {new Date(pred.timestamp).toLocaleString()}
              </div>
            </div>
          );
        })}
      </div>
      
      {predictions.some(p => p.prediction_type === 'fault' && (p.prediction_value || 0) > 0.7) && (
        <div style={{
          marginTop: '15px',
          padding: '12px',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#991b1b',
          fontSize: '0.875rem',
        }}>
          ⚠️ High fault probability detected! Check the device for maintenance.
        </div>
      )}
    </div>
  );
}

