'use client';

import { Device, SensorData } from '@/lib/api';

interface DeviceListProps {
  devices: Device[];
  latestData: Record<string, SensorData>;
  selectedDevice: string | null;
  onSelectDevice: (deviceId: string) => void;
}

export default function DeviceList({
  devices,
  latestData,
  selectedDevice,
  onSelectDevice,
}: DeviceListProps) {
  const getStatusColor = (device: Device, data?: SensorData) => {
    if (device.status !== 'active') return 'status-maintenance';
    if (data?.faulty_lights_count && data.faulty_lights_count > 0) return 'status-inactive';
    return 'status-active';
  };

  return (
    <div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
            <th style={{ padding: '12px' }}>Device ID</th>
            <th style={{ padding: '12px' }}>Name</th>
            <th style={{ padding: '12px' }}>Status</th>
            <th style={{ padding: '12px' }}>Active Lights</th>
            <th style={{ padding: '12px' }}>Faulty Lights</th>
            <th style={{ padding: '12px' }}>Ambient Light</th>
            <th style={{ padding: '12px' }}>Last Update</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => {
            const data = latestData[device.id];
            const isSelected = selectedDevice === device.id;
            return (
              <tr
                key={device.id}
                onClick={() => onSelectDevice(device.id)}
                style={{
                  cursor: 'pointer',
                  backgroundColor: isSelected ? '#f0f9ff' : 'transparent',
                  borderBottom: '1px solid #eee',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected ? '#e0f2fe' : '#f9fafb';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = isSelected ? '#f0f9ff' : 'transparent';
                }}
              >
                <td style={{ padding: '12px' }}>{device.id}</td>
                <td style={{ padding: '12px' }}>{device.name || 'N/A'}</td>
                <td style={{ padding: '12px' }}>
                  <span className={`status-indicator ${getStatusColor(device, data)}`} />
                  {device.status}
                </td>
                <td style={{ padding: '12px' }}>
                  {data?.active_lights_count ?? 'N/A'}
                </td>
                <td style={{ padding: '12px', color: data?.faulty_lights_count ? '#ef4444' : 'inherit' }}>
                  {data?.faulty_lights_count ?? 'N/A'}
                </td>
                <td style={{ padding: '12px' }}>
                  {data?.ambient_light?.toFixed(1) ?? 'N/A'}
                </td>
                <td style={{ padding: '12px' }}>
                  {data?.timestamp
                    ? new Date(data.timestamp).toLocaleString()
                    : 'N/A'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}


