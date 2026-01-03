import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Device {
  id: string;
  name?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SensorData {
  id: number;
  device_id: string;
  timestamp: string;
  ambient_light?: number;
  ambient_light_raw?: number;
  gps_latitude?: number;
  gps_longitude?: number;
  gps_valid: boolean;
  is_dark?: boolean;
  active_lights_count?: number;
  faulty_lights_count?: number;
  created_at: string;
}

export interface Alert {
  id: number;
  device_id: string;
  alert_type: string;
  severity: string;
  message: string;
  light_id?: number;
  latitude?: number;
  longitude?: number;
  status: string;
  created_at: string;
  resolved_at?: string;
}

export interface MLPrediction {
  id: number;
  device_id: string;
  prediction_type: string;
  timestamp: string;
  prediction_value?: number;
  prediction_label?: string;
  confidence?: number;
  model_version?: string;
  model_name?: string;
  created_at: string;
}

export interface DeviceStatistics {
  total_readings: number;
  avg_ambient_light: number;
  max_faulty_lights: number;
  avg_active_lights: number;
}

export const api = {
  async getDevices(): Promise<Device[]> {
    const response = await apiClient.get('/api/v1/devices');
    return response.data;
  },

  async getDevice(deviceId: string): Promise<Device> {
    const response = await apiClient.get(`/api/v1/devices/${deviceId}`);
    return response.data;
  },

  async getLatestData(deviceId: string): Promise<SensorData> {
    const response = await apiClient.get(`/api/v1/devices/${deviceId}/data/latest`);
    return response.data;
  },

  async getHistoricalData(deviceId: string, hours: number = 24): Promise<SensorData[]> {
    const response = await apiClient.get(`/api/v1/devices/${deviceId}/data/historical`, {
      params: { hours },
    });
    return response.data;
  },

  async getAlerts(deviceId?: string, status?: string): Promise<Alert[]> {
    const params: any = {};
    if (deviceId) params.device_id = deviceId;
    if (status) params.status = status;
    const response = await apiClient.get('/api/v1/alerts', { params });
    return response.data;
  },

  async resolveAlert(alertId: number): Promise<void> {
    await apiClient.post(`/api/v1/alerts/${alertId}/resolve`);
  },

  async getMLPredictions(deviceId: string): Promise<MLPrediction[]> {
    const response = await apiClient.get(`/api/v1/ml/predictions/${deviceId}`);
    return response.data;
  },

  async getLatestMLPrediction(deviceId: string): Promise<MLPrediction> {
    const response = await apiClient.get(`/api/v1/ml/predictions/${deviceId}/latest`);
    return response.data;
  },

  async getDeviceStatistics(deviceId: string, hours: number = 24): Promise<DeviceStatistics> {
    const response = await apiClient.get(`/api/v1/devices/${deviceId}/statistics`, {
      params: { hours },
    });
    return response.data;
  },
};

