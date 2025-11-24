# Arduino Bridge Service

This service reads JSON data from Arduino via Serial communication and transmits it to the backend API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure the service:
- Set the correct serial port (e.g., `/dev/ttyUSB0` on Linux, `COM3` on Windows)
- Configure backend API URL
- Set unique device ID

## Usage

```bash
python bridge_service.py --serial-port /dev/ttyUSB0 --api-url http://localhost:8000 --device-id streetlight-001
```

## Command Line Arguments

- `--serial-port`: Serial port for Arduino connection (default: `/dev/ttyUSB0`)
- `--baud-rate`: Serial communication baud rate (default: 9600)
- `--api-url`: Backend API base URL (default: `http://localhost:8000`)
- `--device-id`: Unique identifier for this device (default: `streetlight-001`)

## Features

- Automatic reconnection handling
- Data buffering when API is unavailable
- Health check monitoring
- JSON parsing and validation
- Error logging and recovery


