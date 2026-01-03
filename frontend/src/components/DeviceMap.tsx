'use client';

import { useEffect, useRef, useState } from 'react';
import { Device, SensorData } from '@/lib/api';

// Dynamically import Leaflet only on client side
let MapContainer: any, TileLayer: any, Marker: any, Popup: any, L: any;

if (typeof window !== 'undefined') {
  const leaflet = require('react-leaflet');
  MapContainer = leaflet.MapContainer;
  TileLayer = leaflet.TileLayer;
  Marker = leaflet.Marker;
  Popup = leaflet.Popup;
  L = require('leaflet');
  require('leaflet/dist/leaflet.css');
  
  // Fix for default marker icons in Next.js
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  });
}

interface DeviceMapProps {
  devices: Device[];
  latestData: Record<string, SensorData>;
  onDeviceSelect: (deviceId: string) => void;
}

export default function DeviceMap({ devices, latestData, onDeviceSelect }: DeviceMapProps) {
  const [isClient, setIsClient] = useState(false);
  const mapRef = useRef<any>(null);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isClient && mapRef.current && devices.length > 0 && L) {
      const bounds = devices
        .filter((d) => d.latitude && d.longitude)
        .map((d) => [d.latitude!, d.longitude!] as [number, number]);

      if (bounds.length > 0) {
        mapRef.current.fitBounds(bounds, { padding: [20, 20] });
      }
    }
  }, [devices, isClient]);

  const getMarkerColor = (device: Device, data?: SensorData) => {
    if (!data) return '#gray';
    if (data.faulty_lights_count && data.faulty_lights_count > 0) return '#red';
    if (data.active_lights_count && data.active_lights_count > 0) return '#green';
    return '#blue';
  };

  if (!isClient || !MapContainer) {
    return (
      <div style={{ height: '400px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f3f4f6' }}>
        <div>Loading map...</div>
      </div>
    );
  }

  return (
    <div style={{ height: '400px', width: '100%' }}>
      <MapContainer
        center={[20.5937, 78.9629]} // Default to India center
        zoom={6}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {devices
          .filter((d) => d.latitude && d.longitude)
          .map((device) => {
            const data = latestData[device.id];
            return (
              <Marker
                key={device.id}
                position={[device.latitude!, device.longitude!]}
                eventHandlers={{
                  click: () => onDeviceSelect(device.id),
                }}
              >
                <Popup>
                  <div>
                    <strong>{device.name || device.id}</strong>
                    <br />
                    {device.location_name && <div>{device.location_name}</div>}
                    {data && (
                      <div style={{ marginTop: '10px' }}>
                        <div>Active Lights: {data.active_lights_count || 0}</div>
                        <div>Faulty Lights: {data.faulty_lights_count || 0}</div>
                        <div>Ambient Light: {data.ambient_light?.toFixed(1) || 'N/A'}</div>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>
    </div>
  );
}


