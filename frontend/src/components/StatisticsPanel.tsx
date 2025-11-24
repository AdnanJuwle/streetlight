'use client';

import { useEffect, useState } from 'react';
import { api, DeviceStatistics } from '@/lib/api';

interface StatisticsPanelProps {
  deviceId: string;
}

export default function StatisticsPanel({ deviceId }: StatisticsPanelProps) {
  const [stats, setStats] = useState<DeviceStatistics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatistics();
    const interval = setInterval(loadStatistics, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [deviceId]);

  const loadStatistics = async () => {
    try {
      const data = await api.getDeviceStatistics(deviceId, 24);
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load statistics:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading statistics...</div>;
  }

  if (!stats) {
    return <div>No statistics available</div>;
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '15px' }}>
        <div style={{ padding: '15px', background: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '5px' }}>
            Total Readings (24h)
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {stats.total_readings}
          </div>
        </div>

        <div style={{ padding: '15px', background: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '5px' }}>
            Avg Ambient Light
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {stats.avg_ambient_light.toFixed(1)}
          </div>
        </div>

        <div style={{ padding: '15px', background: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '5px' }}>
            Max Faulty Lights
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: stats.max_faulty_lights > 0 ? '#ef4444' : 'inherit' }}>
            {stats.max_faulty_lights}
          </div>
        </div>

        <div style={{ padding: '15px', background: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '5px' }}>
            Avg Active Lights
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {stats.avg_active_lights.toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  );
}


