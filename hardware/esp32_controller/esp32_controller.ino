#include <WiFi.h>
#include <WebServer.h>

// ============================================================
// Wi-Fi Configuration
// ============================================================

const char* WIFI_SSID = "Infinix NOTE 40X 5G";
const char* WIFI_PASSWORD = "sanlok2130";

// ============================================================
// Web Server
// ============================================================

WebServer server(80);

// ============================================================
// PING Endpoint
// ============================================================

void handlePing() {
  server.send(
    200,
    "application/json",
    "{\"status\":\"ok\",\"message\":\"pong\"}"
  );
}

// ============================================================
// STATUS Endpoint
// ============================================================

void handleStatus() {
  String response = "{";
  response += "\"status\":\"online\",";
  response += "\"device\":\"ESP32\",";
  response += "\"ip\":\"";
  response += WiFi.localIP().toString();
  response += "\"";
  response += "}";

  server.send(
    200,
    "application/json",
    response
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
  Serial.println("Smart Basket ESP32 Controller");
  Serial.println("================================");

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

  // HTTP routes
  server.on("/ping", HTTP_GET, handlePing);
  server.on("/status", HTTP_GET, handleStatus);

  // Start server
  server.begin();

  Serial.println("HTTP server started.");
  Serial.println("================================");
}

// ============================================================
// LOOP
// ============================================================

void loop() {
  server.handleClient();
}