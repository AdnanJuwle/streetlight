#!/usr/bin/env python3
"""
ESP32/Raspberry Pi Bridge Service
Reads JSON data from Arduino via Serial and transmits to backend API
"""

import serial
import json
import time
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArduinoBridge:
    def __init__(self, serial_port: str = '/dev/ttyUSB0', baud_rate: int = 9600,
                 api_url: str = 'http://localhost:8000', device_id: str = 'streetlight-001'):
        """
        Initialize Arduino Bridge Service
        
        Args:
            serial_port: Serial port for Arduino connection (e.g., '/dev/ttyUSB0' or 'COM3')
            baud_rate: Serial communication baud rate
            api_url: Backend API base URL
            device_id: Unique identifier for this device
        """
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.api_url = api_url
        self.device_id = device_id
        self.serial_connection: Optional[serial.Serial] = None
        self.buffer = ""
        self.last_successful_send = time.time()
        self.retry_count = 0
        self.max_retries = 3
        
    def connect_serial(self) -> bool:
        """Establish serial connection with Arduino"""
        try:
            self.serial_connection = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=1,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            time.sleep(2)  # Wait for Arduino to reset
            logger.info(f"Connected to Arduino on {self.serial_port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to serial: {e}")
            return False
    
    def read_serial_line(self) -> Optional[str]:
        """Read a line from serial connection"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        try:
            if self.serial_connection.in_waiting > 0:
                line = self.serial_connection.readline().decode('utf-8').strip()
                return line
        except UnicodeDecodeError:
            logger.warning("Failed to decode serial data, skipping line")
        except Exception as e:
            logger.error(f"Error reading serial: {e}")
        
        return None
    
    def parse_json_data(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse JSON data from Arduino"""
        try:
            data = json.loads(line)
            # Add device metadata
            data['device_id'] = self.device_id
            data['received_at'] = datetime.utcnow().isoformat()
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}, Line: {line[:100]}")
            return None
        except Exception as e:
            logger.error(f"Error parsing data: {e}")
            return None
    
    def send_to_api(self, data: Dict[str, Any]) -> bool:
        """Send data to backend API"""
        try:
            endpoint = f"{self.api_url}/api/v1/devices/{self.device_id}/data"
            response = requests.post(
                endpoint,
                json=data,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200 or response.status_code == 201:
                self.last_successful_send = time.time()
                self.retry_count = 0
                logger.debug(f"Data sent successfully: {data.get('timestamp', 'N/A')}")
                return True
            else:
                logger.warning(f"API returned status {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to backend API, data will be buffered")
            return False
        except requests.exceptions.Timeout:
            logger.warning("API request timed out")
            return False
        except Exception as e:
            logger.error(f"Error sending data to API: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """Check if backend API is available"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def run(self):
        """Main loop - read from Arduino and send to API"""
        if not self.connect_serial():
            logger.error("Failed to establish serial connection. Exiting.")
            return
        
        logger.info(f"Bridge service started. Device ID: {self.device_id}")
        logger.info(f"Backend API: {self.api_url}")
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while True:
            try:
                # Read line from Arduino
                line = self.read_serial_line()
                
                if line:
                    # Try to parse as JSON
                    data = self.parse_json_data(line)
                    
                    if data:
                        # Send to API
                        success = self.send_to_api(data)
                        
                        if success:
                            consecutive_errors = 0
                        else:
                            consecutive_errors += 1
                            # Log buffered data (in production, implement actual buffering)
                            logger.warning(f"Data buffered (API unavailable): {data.get('timestamp', 'N/A')}")
                            
                            if consecutive_errors >= max_consecutive_errors:
                                logger.error("Too many consecutive errors. Checking API health...")
                                if not self.check_api_health():
                                    logger.error("API is not responding. Waiting before retry...")
                                    time.sleep(30)
                                    consecutive_errors = 0
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Shutting down bridge service...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(1)
        
        # Cleanup
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        logger.info("Bridge service stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Arduino to Backend API Bridge Service')
    parser.add_argument('--serial-port', type=str, default='/dev/ttyUSB0',
                       help='Serial port for Arduino (default: /dev/ttyUSB0)')
    parser.add_argument('--baud-rate', type=int, default=9600,
                       help='Serial baud rate (default: 9600)')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000',
                       help='Backend API URL (default: http://localhost:8000)')
    parser.add_argument('--device-id', type=str, default='streetlight-001',
                       help='Device ID (default: streetlight-001)')
    
    args = parser.parse_args()
    
    bridge = ArduinoBridge(
        serial_port=args.serial_port,
        baud_rate=args.baud_rate,
        api_url=args.api_url,
        device_id=args.device_id
    )
    
    bridge.run()


if __name__ == '__main__':
    main()


