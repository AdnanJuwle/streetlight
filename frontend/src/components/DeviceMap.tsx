'use client';

import dynamic from 'next/dynamic';
import { Device, SensorData } from '@/lib/api';

// Dynamically import Leaflet map component (client-side only)
const MapComponent = dynamic(
  () => import('./MapComponent'),
  { 
    ssr: false,
    loading: () => (
      <div style={{ height: '400px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f3f4f6' }}>
        <div>Loading map...</div>
      </div>
    )
  }
);

interface DeviceMapProps {
  devices: Device[];
  latestData: Record<string, SensorData>;
  onDeviceSelect: (deviceId: string) => void;
}

export default function DeviceMap({ devices, latestData, onDeviceSelect }: DeviceMapProps) {
  return (
    <div style={{ height: '400px', width: '100%' }}>
      <MapComponent
        devices={devices}
        latestData={latestData}
        onDeviceSelect={onDeviceSelect}
      />
    </div>
  );
}


