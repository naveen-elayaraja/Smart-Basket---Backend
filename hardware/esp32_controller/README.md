# ESP32 Controller

The ESP32 acts as the hardware-control peripheral for the Smart Basket.

## Current Communication

The ESP32 connects to Wi-Fi and runs an HTTP server on port 80.

### Endpoints

- `GET /ping` — communication health check
- `GET /status` — returns ESP32 online status and IP address

## Architecture

```text
Raspberry Pi
     |
     | Wi-Fi / HTTP
     v
   ESP32
     |
     +-- Servo
     +-- Load Cell / HX711
     +-- IR Sensor
     +-- Buzzer