#include <SoftwareSerial.h>
#include <TinyGPS.h>

// Define constants and thresholds
const int ambientLDR = A0;      // Analog pin for ambient light LDR (LDR1)
const int lightThreshold = 50; // Threshold value for individual LDR fault detection
const char* phoneNumber = "+919822232859"; // Replace with your phone number for receiving SMS
const unsigned long DATA_INTERVAL = 5000; // Send data every 5 seconds

// Define pin arrays for LDRs, IR sensors, and light control
int individualLDRs[4] = {A1, A2, A3, A4};  // Analog pins for individual LDRs under each light (LDR2)
int IRsensors[4] = {2, 3, 4, 5};        // Digital pins for IR sensors
int lightPins[4] = {6, 7, 8, 9};      // Digital pins for controlling bulbs (via transistors/relays)

// Define SoftwareSerial objects for GSM and GPS communication
SoftwareSerial sgsm(12,13);
SoftwareSerial sgps(11,10);

// Flag to track if SMS has been sent for each faulty light
bool smsSent[5] = {false}; // Initialize all flags to false

// GPS variables
TinyGPS gps;
float gpslat, gpslon;
bool gpsValid = false;

// Timing variables
unsigned long lastDataSend = 0;
unsigned long startTime = 0;

// Track turn-on delays for ML model
unsigned long lightCommandTime[4] = {0};  // When command was sent to turn on light
unsigned long lightTurnOnTime[4] = {0};   // When light actually turned on (detected by LDR2)
int lightTurnOnDelay[4] = {0};            // Calculated delay in milliseconds

void setup() {
  Serial.begin(9600);  // Initialize serial communication for debugging and data transmission
  sgsm.begin(9600);
  sgps.begin(9600);

  startTime = millis();

  // Set IR sensor pins as input
  for (int i = 0; i < 4; i++) {
    pinMode(IRsensors[i], INPUT);
  }

  // Set individual LDR pins as input
  for (int i = 0; i < 4; i++) {
    pinMode(individualLDRs[i], INPUT);
  }

  // Set light control pins as output
  for (int i = 0; i < 4; i++) {
    pinMode(lightPins[i], OUTPUT);
  }
  
  // Initialize GPS
  sgps.listen();
  delay(100);
}

int readLDR(int pin) {
  int rawLDR = analogRead(pin);
  int lightIntensity = map(rawLDR, 0, 1030, 0, 100); // Map analog value to a 0-100 scale
  return lightIntensity;
}

int readLDRRaw(int pin) {
  return analogRead(pin);
}

void updateGPS() {
  sgps.listen();
  delay(10);
  while (sgps.available()) {
    if (gps.encode(sgps.read())) {
      gps.f_get_position(&gpslat, &gpslon);
      gpsValid = true;
    }
  }
}

String getTimestamp() {
  unsigned long currentTime = millis();
  unsigned long seconds = (currentTime - startTime) / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;
  
  String timestamp = String(hours) + ":" + 
                     String(minutes % 60) + ":" + 
                     String(seconds % 60);
  return timestamp;
}

void sendJSONData() {
  // Update GPS data
  updateGPS();
  
  // Read all sensor values
  int ambientLight = readLDR(ambientLDR);
  int ambientLightRaw = readLDRRaw(ambientLDR);
  
  // Build JSON string
  String json = "{";
  json += "\"timestamp\":" + String(millis()) + ",";
  json += "\"time_string\":\"" + getTimestamp() + "\",";
  json += "\"ambient_light\":" + String(ambientLight) + ",";
  json += "\"ambient_light_raw\":" + String(ambientLightRaw) + ",";
  
  // GPS data
  json += "\"gps\":{";
  json += "\"valid\":" + String(gpsValid ? "true" : "false") + ",";
  if (gpsValid) {
    json += "\"latitude\":" + String(gpslat, 6) + ",";
    json += "\"longitude\":" + String(gpslon, 6);
  } else {
    json += "\"latitude\":null,";
    json += "\"longitude\":null";
  }
  json += "},";
  
  // Lights array
  json += "\"lights\":[";
  for (int i = 0; i < 4; i++) {
    int lightLevel = readLDR(individualLDRs[i]);
    int lightLevelRaw = readLDRRaw(individualLDRs[i]);
    int movementDetected = digitalRead(IRsensors[i]);
    int lightState = digitalRead(lightPins[i]);
    bool faultDetected = (lightLevel > lightThreshold && lightState == HIGH);
    
    json += "{";
    json += "\"id\":" + String(i + 1) + ",";
    json += "\"ldr_value\":" + String(lightLevel) + ",";
    json += "\"ldr_raw\":" + String(lightLevelRaw) + ",";
    json += "\"ir_sensor\":" + String(movementDetected == LOW ? "true" : "false") + ",";
    json += "\"light_state\":" + String(lightState == HIGH ? "true" : "false") + ",";
    json += "\"fault_detected\":" + String(faultDetected ? "true" : "false") + ",";
    json += "\"turn_on_delay_ms\":" + String(lightTurnOnDelay[i]) + ",";  // NEW: Include delay
    json += "\"sms_sent\":" + String(smsSent[i] ? "true" : "false");
    json += "}";
    if (i < 3) json += ",";
  }
  json += "],";
  
  // System status
  json += "\"system\":{";
  json += "\"is_dark\":" + String(ambientLight > 20 ? "true" : "false") + ",";
  json += "\"active_lights\":" + String(countActiveLights()) + ",";
  json += "\"faulty_lights\":" + String(countFaultyLights());
  json += "}";
  
  json += "}";
  
  // Send JSON via Serial for ESP32/RPi bridge
  Serial.println(json);
}

int countActiveLights() {
  int count = 0;
  for (int i = 0; i < 4; i++) {
    if (digitalRead(lightPins[i]) == HIGH) {
      count++;
    }
  }
  return count;
}

int countFaultyLights() {
  int count = 0;
  for (int i = 0; i < 4; i++) {
    if (digitalRead(lightPins[i]) == HIGH) {
      int lightLevel = readLDR(individualLDRs[i]);
      if (lightLevel > lightThreshold) {
        count++;
      }
    }
  }
  return count;
}

void sendSMS(char* message) {
  sgsm.println("AT+CMGF=1"); // Set SMS mode to text
  delay(100);
  sgsm.print("AT+CMGS=\""); // Set recipient phone number
  sgsm.print(phoneNumber);
  sgsm.println("\"");
  delay(100);
  sgsm.print(message); // Send message content
  delay(100);
  sgsm.write(0x1A); // Send Ctrl+Z to indicate end of SMS
  delay(100);
}

void loop() {
  int ambientLight = readLDR(ambientLDR);  // Read ambient light level (LDR1)

  // Send structured JSON data at regular intervals
  if (millis() - lastDataSend >= DATA_INTERVAL) {
    sendJSONData();
    lastDataSend = millis();
  }

  // Check if it's dark enough for street lights to operate
  if (ambientLight > 20) { // Adjust threshold based on your light sensitivity needs
    for (int i = 0; i < 4; i++) {
      int movementDetected = digitalRead(IRsensors[i]);  // Check for movement
      
      // Turn on light if movement detected and it's dark
      if (movementDetected == LOW) {
        // Record when command is sent
        if (digitalRead(lightPins[i]) == LOW) {
          lightCommandTime[i] = millis();
        }
        
        digitalWrite(lightPins[i], HIGH);
        
        // Wait a bit for light to turn on, then check LDR2
        delay(100);  // Small delay to allow relay to activate
        
        // Check if light actually turned on (LDR2 detects light)
        int lightLevel = readLDR(individualLDRs[i]);
        int previousLightLevel = lightLevel;
        
        // Monitor for light to actually turn on (LDR value should drop)
        unsigned long checkStartTime = millis();
        while (millis() - checkStartTime < 3000) {  // Check for up to 3 seconds
          int currentLightLevel = readLDR(individualLDRs[i]);
          
          // Light is on if LDR value dropped significantly (more light detected)
          if (currentLightLevel < previousLightLevel - 10) {
            lightTurnOnTime[i] = millis();
            lightTurnOnDelay[i] = lightTurnOnTime[i] - lightCommandTime[i];
            break;
          }
          
          // Or if enough time has passed, assume it's on
          if (millis() - lightCommandTime[i] > 2000) {
            lightTurnOnTime[i] = millis();
            lightTurnOnDelay[i] = millis() - lightCommandTime[i];
            break;
          }
          
          delay(50);  // Check every 50ms
        }
        
        // Final check for fault after light should be on
        delay(1000);  // Wait 1 second after turn-on
        lightLevel = readLDR(individualLDRs[i]);
        if (lightLevel > lightThreshold && !smsSent[i]) {
          // Get GPS location
          updateGPS();
          if (gpsValid) {
            // Construct SMS message with location data
            String message = "Fault detected in light: ";
            message += (i + 1);
            message += " Location: https://maps.google.com/?q=";
            message += String(gpslat, 6); // Format latitude to 6 decimal places
            message += ",";
            message += String(gpslon, 6); // Format longitude to 6 decimal places
            
            // Send SMS notification with GPS location (only once per faulty light)
            sendSMS(message.c_str());
            smsSent[i] = true;  // Mark SMS sent for this light
          }
        }
      } else {
        digitalWrite(lightPins[i], LOW);
        // Reset delay tracking when light is off
        lightCommandTime[i] = 0;
        lightTurnOnTime[i] = 0;
        lightTurnOnDelay[i] = 0;
      }
    }
  } else {
    // It's not dark enough, turn off all lights
    for (int i = 0; i < 4; i++) {
      digitalWrite(lightPins[i], LOW);
      // Reset delay tracking
      lightCommandTime[i] = 0;
      lightTurnOnTime[i] = 0;
      lightTurnOnDelay[i] = 0;
    }
    // Reset SMS flag for the next day
    for (int i = 0; i < 4; i++) {
      smsSent[i] = false;
    }
  }
  
  delay(100); // Small delay to prevent overwhelming the system
}

