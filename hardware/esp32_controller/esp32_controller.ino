
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// Wi-Fi: preserve the credentials from your existing sketch
const char* WIFI_SSID = "1028";
const char* WIFI_PASSWORD = "/;/'/;/'";

WebServer server(80);


Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

const int SERVO1_PIN = 18;
const int SERVO2_PIN = 19;
const int SERVO3_PIN = 21;
const int SERVO4_PIN = 22;

const int CLOSED_ANGLE = 0;
const int OPEN_ANGLE = 120;


Servo* getServo(int number) {
  if (number == 1) return &servo1;
  if (number == 2) return &servo2;
  if (number == 3) return &servo3;
  if (number == 4) return &servo4;
  return nullptr;
}


void handlePing() {
  server.send(200, "application/json",
              "{\"status\":\"ok\",\"message\":\"pong\"}");
}

void handleStatus() {
  String response = "{\"status\":\"online\",\"device\":\"ESP32\",\"ip\":\"";
  response += WiFi.localIP().toString();
  response += "\",\"servos\":3}";
  server.send(200, "application/json", response);
}

void handleServoCommand(bool open) {
  if (!server.hasArg("servo")) {
    server.send(400, "application/json",
                "{\"error\":\"Specify servo=1, servo=2, or servo=3\"}");
    return;
  }

  int number = server.arg("servo").toInt();
  Servo* selectedServo = getServo(number);

  if (selectedServo == nullptr || !selectedServo->attached()) {
    server.send(400, "application/json",
                "{\"error\":\"Invalid or unattached servo; use 1, 2, or 3\"}");
    return;
  }

  int angle = open ? OPEN_ANGLE : CLOSED_ANGLE;
  selectedServo->write(angle);

  Serial.printf("Servo %d commanded to %d degrees\n", number, angle);

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

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\nSmart Basket - Three Servo Controller");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWi-Fi connected.");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());

  servo1.setPeriodHertz(50);
  servo2.setPeriodHertz(50);
  servo3.setPeriodHertz(50);
  servo4.setPeriodHertz(50);
  

  servo1.attach(SERVO1_PIN, 500, 2400);
  servo2.attach(SERVO2_PIN, 500, 2400);
  servo3.attach(SERVO3_PIN, 500, 2400);
  servo4.attach(SERVO4_PIN, 500, 2400);

  Serial.printf("Servo 1 (GPIO18): %s\n",
                servo1.attached() ? "attached" : "FAILED");
  Serial.printf("Servo 2 (GPIO19): %s\n",
                servo2.attached() ? "attached" : "FAILED");
  Serial.printf("Servo 3 (GPIO21): %s\n",
                servo3.attached() ? "attached" : "FAILED");
  Serial.printf("Servo 4 (GPIO22): %s\n",
                servo4.attached() ? "attached" : "FAILED");

  // Start at the closed position
  if (servo1.attached()) servo1.write(CLOSED_ANGLE);
  if (servo2.attached()) servo2.write(CLOSED_ANGLE);
  if (servo3.attached()) servo3.write(CLOSED_ANGLE);
  if (servo4.attached()) servo4.write(CLOSED_ANGLE);

  server.on("/ping", HTTP_GET, handlePing);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/servo/open", HTTP_GET, handleServoOpen);
  server.on("/servo/close", HTTP_GET, handleServoClose);

  server.begin();

  Serial.println("HTTP server started.");
  Serial.println("Servo routes registered for channels 1, 2, and 3.");
}

void loop() {
  server.handleClient();
}
