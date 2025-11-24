'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api, SensorData } from '@/lib/api';
import { format } from 'date-fns';

interface RealTimeChartProps {
  deviceId: string;
}

export default function RealTimeChart({ deviceId }: RealTimeChartProps) {
  const [data, setData] = useState<SensorData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [deviceId]);

  const loadData = async () => {
    try {
      const historicalData = await api.getHistoricalData(deviceId, 1, 100); // Last hour, 100 points
      setData(historicalData.reverse()); // Reverse to show chronological order
      setLoading(false);
    } catch (error) {
      console.error('Failed to load chart data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading chart data...</div>;
  }

  if (data.length === 0) {
    return <div>No data available for chart</div>;
  }

  const chartData = data.map((item) => ({
    time: format(new Date(item.timestamp), 'HH:mm:ss'),
    ambientLight: item.ambient_light || 0,
    activeLights: item.active_lights_count || 0,
    faultyLights: item.faulty_lights_count || 0,
  }));

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="ambientLight"
            stroke="#3b82f6"
            name="Ambient Light"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="activeLights"
            stroke="#10b981"
            name="Active Lights"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="faultyLights"
            stroke="#ef4444"
            name="Faulty Lights"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}


