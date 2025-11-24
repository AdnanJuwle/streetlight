'use client';

import { Alert } from '@/lib/api';
import { api } from '@/lib/api';

interface AlertsPanelProps {
  alerts: Alert[];
  onResolve: () => void;
}

export default function AlertsPanel({ alerts, onResolve }: AlertsPanelProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return '#dc2626';
      case 'high':
        return '#ea580c';
      case 'medium':
        return '#f59e0b';
      case 'low':
        return '#3b82f6';
      default:
        return '#6b7280';
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await api.resolveAlert(alertId);
      onResolve();
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  if (alerts.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No active alerts
      </div>
    );
  }

  return (
    <div>
      {alerts.slice(0, 10).map((alert) => (
        <div
          key={alert.id}
          style={{
            padding: '15px',
            marginBottom: '10px',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            borderLeft: `4px solid ${getSeverityColor(alert.severity)}`,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    backgroundColor: getSeverityColor(alert.severity),
                    color: 'white',
                    marginRight: '8px',
                  }}
                >
                  {alert.severity.toUpperCase()}
                </span>
                <span style={{ fontSize: '0.875rem', color: '#666' }}>
                  {alert.alert_type}
                </span>
              </div>
              <div style={{ fontWeight: '500', marginBottom: '5px' }}>
                {alert.message}
              </div>
              <div style={{ fontSize: '0.875rem', color: '#666' }}>
                Device: {alert.device_id}
                {alert.light_id && ` | Light: ${alert.light_id}`}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '5px' }}>
                {new Date(alert.created_at).toLocaleString()}
              </div>
            </div>
            <button
              onClick={() => handleResolve(alert.id)}
              style={{
                padding: '6px 12px',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
              }}
            >
              Resolve
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}


