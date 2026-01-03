'use client';

import { useEffect, useState } from 'react';
import { api, Device, SensorData, Alert } from '@/lib/api';
import DeviceMap from '@/components/DeviceMap';
import DeviceList from '@/components/DeviceList';
import StatisticsPanel from '@/components/StatisticsPanel';
import AlertsPanel from '@/components/AlertsPanel';
import RealTimeChart from '@/components/RealTimeChart';
import MLPredictionsPanel from '@/components/MLPredictionsPanel';

export default function Home() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [latestData, setLatestData] = useState<Record<string, SensorData>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setError(null);
      const [devicesData, alertsData] = await Promise.all([
        api.getDevices(),
        api.getAlerts(undefined, 'open'),
      ]);

      setDevices(devicesData);
      setAlerts(alertsData);

      // Load latest data for all devices
      const dataPromises = devicesData.map(async (device) => {
        try {
          const data = await api.getLatestData(device.id);
          return { deviceId: device.id, data };
        } catch (error) {
          console.error(`Failed to load data for ${device.id}:`, error);
          return null;
        }
      });

      const dataResults = await Promise.all(dataPromises);
      const dataMap: Record<string, SensorData> = {};
      dataResults.forEach((result) => {
        if (result) {
          dataMap[result.deviceId] = result.data;
        }
      });
      setLatestData(dataMap);

      setLoading(false);
    } catch (error: any) {
      console.error('Failed to load data:', error);
      const errorMessage = error?.response?.status === 404 
        ? 'Backend API not found. Make sure the backend server is running on http://localhost:8000'
        : error?.message || 'Failed to connect to backend API';
      setError(errorMessage);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h2>Loading...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div style={{ 
          textAlign: 'center', 
          padding: '40px',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          margin: '20px',
          color: '#991b1b'
        }}>
          <h2 style={{ color: '#dc2626', marginBottom: '10px' }}>Connection Error</h2>
          <p>{error}</p>
          <p style={{ marginTop: '20px', fontSize: '0.875rem' }}>
            Make sure the backend server is running:<br />
            <code style={{ background: '#fee2e2', padding: '4px 8px', borderRadius: '4px' }}>
              python -m uvicorn backend.main:app --port 8000
            </code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '10px' }}>
          Smart Streetlight System
        </h1>
        <p style={{ color: '#666' }}>
          AI-powered monitoring and management dashboard
        </p>
      </header>

      <div className="grid grid-2" style={{ marginBottom: '20px' }}>
        <div className="card">
          <h2 style={{ marginBottom: '15px' }}>Device Map</h2>
          <DeviceMap
            devices={devices}
            latestData={latestData}
            onDeviceSelect={setSelectedDevice}
          />
        </div>

        <div className="card">
          <h2 style={{ marginBottom: '15px' }}>Active Alerts</h2>
          <AlertsPanel alerts={alerts} onResolve={loadData} />
        </div>
      </div>

      <div className="card" style={{ marginBottom: '20px' }}>
        <h2 style={{ marginBottom: '15px' }}>Devices</h2>
        <DeviceList
          devices={devices}
          latestData={latestData}
          selectedDevice={selectedDevice}
          onSelectDevice={setSelectedDevice}
        />
      </div>

      {selectedDevice && (
        <>
          <div className="grid grid-2" style={{ marginBottom: '20px' }}>
            <div className="card">
              <h2 style={{ marginBottom: '15px' }}>Statistics</h2>
              <StatisticsPanel deviceId={selectedDevice} />
            </div>

            <div className="card">
              <h2 style={{ marginBottom: '15px' }}>Real-time Data</h2>
              <RealTimeChart deviceId={selectedDevice} />
            </div>
          </div>

          <div className="card" style={{ marginBottom: '20px' }}>
            <h2 style={{ marginBottom: '15px' }}>ML Predictions</h2>
            <MLPredictionsPanel deviceId={selectedDevice} />
          </div>
        </>
      )}
    </div>
  );
}


