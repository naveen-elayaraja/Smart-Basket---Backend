SERVO TEST — ESP32

Purpose
───────
Test three SG90-style servos using an ESP32 with an external 5V supply.

Pin Configuration
─────────────────

Servo 1 signal → GPIO 18
Servo 2 signal → GPIO 19
Servo 3 signal → GPIO 21

Power
─────
Servo power → External 5V supply
Servo ground → External GND
ESP32 GND → External GND

Servo Positions
───────────────

0°   → Closed position
120° → Open position

Test Behaviour
───────────────
All three servos move together:

0° → 120° → 0°

The servos remain at each position for a few seconds before moving.
