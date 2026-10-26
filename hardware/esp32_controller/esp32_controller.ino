#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>
#include "HX711.h"
#include <math.h>

// =====================================================
// WIFI CONFIGURATION
// Enter your existing Wi-Fi credentials locally.
// =====================================================

const char* WIFI_SSID = "1028";
const char* WIFI_PASSWORD = "/;/'/;/'";

// =====================================================
// HTTP SERVER
// =====================================================

WebServer server(80);
HX711 scale;

// =====================================================
// SERVO CONFIGURATION - EXISTING PINS PRESERVED
// =====================================================

Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

const int SERVO1_PIN = 18;
const int SERVO2_PIN = 19;
const int SERVO3_PIN = 21;
const int SERVO4_PIN = 22;

const int SERVO12_CLOSED = 0;
const int SERVO12_OPEN = 120;

const int SERVO34_CLOSED = 120;
const int SERVO34_OPEN = 0;

Servo* allServos[] = {
  &servo1,
  &servo2,
  &servo3,
  &servo4
};

Servo* getServo(int number) {
  switch (number) {
    case 1: return &servo1;
    case 2: return &servo2;
    case 3: return &servo3;
    case 4: return &servo4;
    default: return nullptr;
  }
}

// =====================================================
// HX711 LOAD CELL CONFIGURATION
// =====================================================

const int DT_PIN = 32;
const int SCK_PIN = 33;

// Starting estimate based on your 1 kg test.
// Recheck against a known weight after uploading.
const float CALIBRATION_FACTOR = 311.86f;

// =====================================================
// IR SENSOR CONFIGURATION
// =====================================================

// Proposed default GPIO. Change to match your wiring.
const int IR_SENSOR_PIN = 27;

// Common digital IR modules output LOW when detecting
// an obstacle. Change to false if your module outputs HIGH.
const bool IR_ACTIVE_LOW = true;

// Obstacle must remain detected for MORE than 10 seconds.
const unsigned long OBSTACLE_ALARM_DELAY_MS = 10000UL;

// =====================================================
// BUZZER CONFIGURATION
// =====================================================

// Proposed default GPIO. Change to match your wiring.
const int BUZZER_PIN = 25;

// Assumes an active buzzer that sounds when GPIO is HIGH.
const bool BUZZER_ACTIVE_HIGH = true;

// Duration of an ordinary error alarm.
const unsigned long ERROR_ALARM_DURATION_MS = 3000UL;

// Buzzer beep pattern.
const unsigned long BUZZER_PATTERN_MS = 500UL;

// =====================================================
// RUNTIME STATE
// =====================================================

bool obstacleCurrentlyDetected = false;
bool obstacleAlarmActive = false;

unsigned long obstacleStartTime = 0;

bool errorAlarmActive = false;
unsigned long errorAlarmStartTime = 0;

unsigned long lastBuzzerPatternTime = 0;
bool buzzerPatternOn = false;

// =====================================================
// BUZZER CONTROL
// =====================================================

void setBuzzer(bool on) {
  if (BUZZER_ACTIVE_HIGH) {
    digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
  } else {
    digitalWrite(BUZZER_PIN, on ? LOW : HIGH);
  }
}

// Trigger an ordinary error alarm without blocking HTTP.
void triggerErrorAlarm(const char* reason) {
  errorAlarmActive = true;
  errorAlarmStartTime = millis();

  Serial.print("ALARM: ");
  Serial.println(reason);
}

// =====================================================
// IR SENSOR
// =====================================================

bool isObstacleDetected() {
  int sensorValue = digitalRead(IR_SENSOR_PIN);

  if (IR_ACTIVE_LOW) {
    return sensorValue == LOW;
  }

  return sensorValue == HIGH;
}

void updateIRSensor() {
  const unsigned long now = millis();

  bool detected = isObstacleDetected();

  if (detected && !obstacleCurrentlyDetected) {
    obstacleCurrentlyDetected = true;
    obstacleStartTime = now;

    Serial.println("IR: Obstacle detected.");
  }

  if (!detected && obstacleCurrentlyDetected) {
    obstacleCurrentlyDetected = false;
    obstacleAlarmActive = false;
    obstacleStartTime = 0;

    Serial.println("IR: Obstacle cleared.");
  }

  if (obstacleCurrentlyDetected && !obstacleAlarmActive) {
    if (now - obstacleStartTime > OBSTACLE_ALARM_DELAY_MS) {
      obstacleAlarmActive = true;

      Serial.println(
        "ALARM: Obstacle detected for more than 10 seconds!"
      );
    }
  }
}

// =====================================================
// BUZZER UPDATE
// Non-blocking: Wi-Fi and HTTP continue to work.
// =====================================================

void updateBuzzer() {
  const unsigned long now = millis();

  // Highest priority: persistent obstacle alarm.
  if (obstacleAlarmActive) {
    if (now - lastBuzzerPatternTime >= BUZZER_PATTERN_MS) {
      lastBuzzerPatternTime = now;
      buzzerPatternOn = !buzzerPatternOn;
      setBuzzer(buzzerPatternOn);
    }

    return;
  }

  // Ordinary camera, weight, or hardware error alarm.
  if (errorAlarmActive) {
    if (now - errorAlarmStartTime >= ERROR_ALARM_DURATION_MS) {
      errorAlarmActive = false;
      buzzerPatternOn = false;
      setBuzzer(false);
      return;
    }

    if (now - lastBuzzerPatternTime >= BUZZER_PATTERN_MS) {
      lastBuzzerPatternTime = now;
      buzzerPatternOn = !buzzerPatternOn;
      setBuzzer(buzzerPatternOn);
    }

    return;
  }

  buzzerPatternOn = false;
  setBuzzer(false);
}

// =====================================================
// COMMON HTTP RESPONSE
// =====================================================

void sendAlarmResponse(const char* reason) {
  String response = "{\"status\":\"ok\",\"alarm\":\"";
  response += reason;
  response += "\",\"buzzer_triggered\":true}";

  server.send(200, "application/json", response);
}

// =====================================================
// STATUS ENDPOINTS
// =====================================================

void handlePing() {
  server.send(
    200,
    "application/json",
    "{\"status\":\"ok\",\"message\":\"pong\"}"
  );
}

void handleStatus() {
  String response = "{";

  response += "\"status\":\"online\",";
  response += "\"device\":\"ESP32\",";
  response += "\"ip\":\"";
  response += WiFi.localIP().toString();
  response += "\",";

  response += "\"servos\":4,";
  response += "\"hx711\":";
  response += scale.is_ready() ? "true," : "false,";

  response += "\"ir_obstacle_detected\":";
  response += obstacleCurrentlyDetected ? "true," : "false,";

  response += "\"obstacle_alarm_active\":";
  response += obstacleAlarmActive ? "true," : "false,";

  response += "\"error_alarm_active\":";
  response += errorAlarmActive ? "true" : "false";

  response += "}";

  server.send(200, "application/json", response);
}

// =====================================================
// SERVO CONTROL
// Existing angles and endpoint behavior preserved.
// =====================================================

void handleServoCommand(bool open) {
  if (!server.hasArg("servo")) {
    server.send(
      400,
      "application/json",
      "{\"status\":\"error\",\"message\":\"Specify servo=1, 2, 3, or 4\"}"
    );
    return;
  }

  int number = server.arg("servo").toInt();
  Servo* selectedServo = getServo(number);

  if (selectedServo == nullptr || !selectedServo->attached()) {
    triggerErrorAlarm("Invalid servo command");

    server.send(
      400,
      "application/json",
      "{\"status\":\"error\",\"message\":\"Invalid or unattached servo\"}"
    );
    return;
  }

  int angle;

  if (number <= 2) {
    angle = open ? SERVO12_OPEN : SERVO12_CLOSED;
  } else {
    angle = open ? SERVO34_OPEN : SERVO34_CLOSED;
  }

  selectedServo->write(angle);

  Serial.printf(
    "Servo %d commanded to %d degrees\n",
    number,
    angle
  );

  String response = "{\"status\":\"ok\",\"action\":\"";
  response += open ? "open" : "close";
  response += "\",\"servo\":";
  response += String(number);
  response += ",\"angle\":";
  response += String(angle);
  response += "}";

  server.send(200, "application/json", response);
}

void handleServoOpen() {
  handleServoCommand(true);
}

void handleServoClose() {
  handleServoCommand(false);
}

void handleAllServos(bool open) {
  for (int i = 0; i < 4; i++) {
    if (!allServos[i]->attached()) {
      triggerErrorAlarm("Servo attachment error");

      server.send(
        503,
        "application/json",
        "{\"status\":\"error\",\"message\":\"Servo not attached\"}"
      );
      return;
    }
  }

  int angle12 = open ? SERVO12_OPEN : SERVO12_CLOSED;
  int angle34 = open ? SERVO34_OPEN : SERVO34_CLOSED;

  servo1.write(angle12);
  servo2.write(angle12);
  servo3.write(angle34);
  servo4.write(angle34);

  Serial.printf(
    "All servos: %d, %d, %d, %d\n",
    angle12,
    angle12,
    angle34,
    angle34
  );

  String response = "{\"status\":\"ok\",\"action\":\"";
  response += open ? "open_all" : "close_all";
  response += "\",\"servos\":4,\"angles\":[";
  response += String(angle12) + ",";
  response += String(angle12) + ",";
  response += String(angle34) + ",";
  response += String(angle34) + "]}";

  server.send(200, "application/json", response);
}

void handleOpenAll() {
  handleAllServos(true);
}

void handleCloseAll() {
  handleAllServos(false);
}

// =====================================================
// LOAD CELL: WEIGHT
// =====================================================

void handleWeight() {
  if (!scale.is_ready()) {
    triggerErrorAlarm("HX711 not ready");

    server.send(
      503,
      "application/json",
      "{\"status\":\"error\",\"message\":\"HX711 not ready\"}"
    );
    return;
  }

  float weight = scale.get_units(10);

  if (!isfinite(weight)) {
    triggerErrorAlarm("Invalid weight reading");

    server.send(
      500,
      "application/json",
      "{\"status\":\"error\",\"message\":\"Invalid reading\"}"
    );
    return;
  }

  Serial.printf("Measured weight: %.1f g\n", weight);

  String response = "{\"status\":\"ok\",\"weight_g\":";
  response += String(weight, 1);
  response += ",\"unit\":\"g\"}";

  server.send(200, "application/json", response);
}

// =====================================================
// LOAD CELL: TARE
// ONLY call this when the platform is empty.
// =====================================================

void handleTare() {
  if (!scale.is_ready()) {
    triggerErrorAlarm("HX711 not ready during tare");

    server.send(
      503,
      "application/json",
      "{\"status\":\"error\",\"message\":\"HX711 not ready\"}"
    );
    return;
  }

  scale.tare(15);

  Serial.println("Scale tared.");

  server.send(
    200,
    "application/json",
    "{\"status\":\"ok\",\"message\":\"Tare completed\"}"
  );
}

// =====================================================
// CAMERA MISMATCH ALARM
// The Raspberry Pi/backend must call this endpoint
// when camera recognition detects a product mismatch.
// =====================================================

void handleCameraMismatch() {
  triggerErrorAlarm("Camera product mismatch");
  sendAlarmResponse("camera_mismatch");
}

// =====================================================
// WEIGHT MISMATCH ALARM
// The Raspberry Pi/backend must call this endpoint
// when measured and expected weights do not match.
// =====================================================

void handleWeightMismatch() {
  triggerErrorAlarm("Product weight mismatch");
  sendAlarmResponse("weight_mismatch");
}

// =====================================================
// GENERAL HARDWARE / SYSTEM ERROR ALARM
// =====================================================

void handleGeneralError() {
  triggerErrorAlarm("General hardware or system error");
  sendAlarmResponse("general_error");
}

// =====================================================
// IR STATUS ENDPOINT
// =====================================================

void handleIRStatus() {
  String response = "{";

  response += "\"obstacle_detected\":";
  response += obstacleCurrentlyDetected ? "true," : "false,";

  response += "\"alarm_active\":";
  response += obstacleAlarmActive ? "true" : "false";

  response += "}";

  server.send(200, "application/json", response);
}

// =====================================================
// SETUP
// =====================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=================================");
  Serial.println("SMART TROLLEY ESP32");
  Serial.println("Servo + HX711 + IR + Buzzer");
  Serial.println("=================================");

  // Initialize the buzzer before other components.
  pinMode(BUZZER_PIN, OUTPUT);
  setBuzzer(false);

  // Initialize IR sensor.
  pinMode(IR_SENSOR_PIN, INPUT);

  Serial.printf("IR sensor GPIO: %d\n", IR_SENSOR_PIN);
  Serial.printf("Buzzer GPIO: %d\n", BUZZER_PIN);

  // Initialize the HX711.
  scale.begin(DT_PIN, SCK_PIN);
  scale.set_scale(CALIBRATION_FACTOR);

  Serial.println("Checking HX711...");

  unsigned long startTime = millis();

  while (!scale.is_ready() && millis() - startTime < 3000) {
    delay(50);
  }

  if (scale.is_ready()) {
    Serial.println("HX711 ready.");
    Serial.println("Keep the platform EMPTY during startup tare.");

    delay(1500);

    scale.tare(15);

    Serial.println("Startup tare complete.");
  } else {
    Serial.println("WARNING: HX711 not ready.");
    Serial.println("Weight readings will be unavailable.");
  }

  // Connect to Wi-Fi.
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi connected.");

  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // Initialize the four existing servos.
  for (int i = 0; i < 4; i++) {
    allServos[i]->setPeriodHertz(50);
  }

  servo1.attach(SERVO1_PIN, 500, 2400);
  servo2.attach(SERVO2_PIN, 500, 2400);
  servo3.attach(SERVO3_PIN, 500, 2400);
  servo4.attach(SERVO4_PIN, 500, 2400);

  Serial.printf(
    "Servo 1 GPIO18: %s\n",
    servo1.attached() ? "attached" : "FAILED"
  );

  Serial.printf(
    "Servo 2 GPIO19: %s\n",
    servo2.attached() ? "attached" : "FAILED"
  );

  Serial.printf(
    "Servo 3 GPIO21: %s\n",
    servo3.attached() ? "attached" : "FAILED"
  );

  Serial.printf(
    "Servo 4 GPIO22: %s\n",
    servo4.attached() ? "attached" : "FAILED"
  );

  // Preserve the original startup servo positions.
  servo1.write(SERVO12_CLOSED);
  servo2.write(SERVO12_CLOSED);
  servo3.write(SERVO34_CLOSED);
  servo4.write(SERVO34_CLOSED);

  // ---------------------------------------------------
  // REGISTER EXISTING ENDPOINTS
  // ---------------------------------------------------

  server.on("/ping", HTTP_GET, handlePing);
  server.on("/status", HTTP_GET, handleStatus);

  server.on("/servo/open", HTTP_GET, handleServoOpen);
  server.on("/servo/close", HTTP_GET, handleServoClose);

  server.on("/servos/open-all", HTTP_GET, handleOpenAll);
  server.on("/servos/close-all", HTTP_GET, handleCloseAll);

  server.on("/weight", HTTP_GET, handleWeight);
  server.on("/weight/tare", HTTP_POST, handleTare);

  // ---------------------------------------------------
  // NEW ALARM ENDPOINTS
  // POST or GET can trigger these alarms.
  // ---------------------------------------------------

  server.on(
    "/alarm/camera-mismatch",
    HTTP_POST,
    handleCameraMismatch
  );

  server.on(
    "/alarm/camera-mismatch",
    HTTP_GET,
    handleCameraMismatch
  );

  server.on(
    "/alarm/weight-mismatch",
    HTTP_POST,
    handleWeightMismatch
  );

  server.on(
    "/alarm/weight-mismatch",
    HTTP_GET,
    handleWeightMismatch
  );

  server.on(
    "/alarm/error",
    HTTP_POST,
    handleGeneralError
  );

  server.on(
    "/alarm/error",
    HTTP_GET,
    handleGeneralError
  );

  server.on("/ir/status", HTTP_GET, handleIRStatus);

  // Start HTTP server.
  server.begin();

  Serial.println();
  Serial.println("HTTP server started.");
  Serial.println("GET  /ping");
  Serial.println("GET  /status");
  Serial.println("GET  /servo/open?servo=1");
  Serial.println("GET  /servo/close?servo=1");
  Serial.println("GET  /servos/open-all");
  Serial.println("GET  /servos/close-all");
  Serial.println("GET  /weight");
  Serial.println("POST /weight/tare");
  Serial.println("GET  /ir/status");
  Serial.println("POST /alarm/camera-mismatch");
  Serial.println("POST /alarm/weight-mismatch");
  Serial.println("POST /alarm/error");
  Serial.println();
  Serial.println("Obstacle alarm threshold: 10 seconds.");
}

// =====================================================
// MAIN LOOP
// =====================================================

void loop() {
  server.handleClient();

  updateIRSensor();

  updateBuzzer();

  // Keep Wi-Fi reconnection simple and non-blocking.
  static unsigned long lastWiFiCheck = 0;

  if (millis() - lastWiFiCheck >= 5000UL) {
    lastWiFiCheck = millis();

    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WARNING: Wi-Fi disconnected.");
      WiFi.reconnect();
    }
  }
}