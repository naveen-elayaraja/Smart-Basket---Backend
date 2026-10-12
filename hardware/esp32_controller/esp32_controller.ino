#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// ============================================================
// Wi-Fi Configuration
// ============================================================

const char* WIFI_SSID = "1028";
const char* WIFI_PASSWORD = "/;/'/;/'";

// ============================================================
// Web Server and Servo 1 Diagnostic Test
// ============================================================

WebServer server(80);
Servo servo1;

const int SERVO1_PIN = 18;
const int CLOSED_ANGLE = 0;
const int OPEN_ANGLE = 120;

// ============================================================
// PING
// ============================================================

void handlePing() {
  server.send(
    200,
    "application/json",
    "{\"status\":\"ok\",\"message\":\"pong\"}"
  );
}

// ============================================================
// STATUS
// ============================================================

void handleStatus() {
  String response = "{";
  response += "\"status\":\"online\",";
  response += "\"device\":\"ESP32\",";
  response += "\"ip\":\"";
  response += WiFi.localIP().toString();
  response += "\"}";

  server.send(200, "application/json", response);
}

// ============================================================
// SERVO OPEN
// ============================================================

void handleServoOpen() {
  Serial.println("Received SERVO OPEN command");

  if (!server.hasArg("servo") || server.arg("servo") != "1") {
    server.send(
      400,
      "application/json",
      "{\"error\":\"Use servo=1 for this diagnostic test\"}"
    );
    return;
  }

  servo1.write(OPEN_ANGLE);
  Serial.println("Servo 1 commanded to 120 degrees");

  server.send(
    200,
    "application/json",
    "{\"status\":\"ok\",\"action\":\"open\",\"servo\":1}"
  );
}

// ============================================================
// SERVO CLOSE
// ============================================================

void handleServoClose() {
  Serial.println("Received SERVO CLOSE command");

  if (!server.hasArg("servo") || server.arg("servo") != "1") {
    server.send(
      400,
      "application/json",
      "{\"error\":\"Use servo=1 for this diagnostic test\"}"
    );
    return;
  }

  servo1.write(CLOSED_ANGLE);
  Serial.println("Servo 1 commanded to 0 degrees");

  server.send(
    200,
    "application/json",
    "{\"status\":\"ok\",\"action\":\"close\",\"servo\":1}"
  );
}

// ============================================================
// SETUP
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("================================");
  Serial.println("Smart Basket Servo Diagnostic");
  Serial.println("================================");

  // Initialize Servo 1 only
  servo1.setPeriodHertz(50);
  servo1.attach(SERVO1_PIN, 500, 2400);
  servo1.write(CLOSED_ANGLE);

  Serial.println("Servo 1 attached to GPIO18");

  // Connect to Wi-Fi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi connected.");

  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());

  // Register routes
  server.on("/ping", HTTP_GET, handlePing);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/servo/open", HTTP_GET, handleServoOpen);
  server.on("/servo/close", HTTP_GET, handleServoClose);

  server.begin();

  Serial.println("HTTP server started.");
  Serial.println("Servo routes registered.");
  Serial.println("Ready for Servo 1 commands.");
  Serial.println("================================");
}

// ============================================================
// LOOP
// ============================================================

void loop() {
  server.handleClient();
}