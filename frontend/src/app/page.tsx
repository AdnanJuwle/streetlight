'use client';

import { useEffect, useState } from 'react';
import { api, Device, SensorData, Alert } from '@/lib/api';
import DeviceMap from '@/components/DeviceMap';
import DeviceList from '@/components/DeviceList';
import StatisticsPanel from '@/components/StatisticsPanel';
import AlertsPanel from '@/components/AlertsPanel';
import RealTimeChart from '@/components/RealTimeChart';

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

  const loadData = async () => {
    try {
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
    } catch (error) {
      console.error('Failed to load data:', error);
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
      )}
    </div>
  );
}


