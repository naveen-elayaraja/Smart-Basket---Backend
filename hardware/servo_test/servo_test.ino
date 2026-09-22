#include <ESP32Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;

void setup() {
  servo1.attach(18, 500, 2400);
  servo2.attach(19, 500, 2400);
  servo3.attach(21, 500, 2400);

  servo1.write(0);
  servo2.write(0);
  servo3.write(0);

  delay(2000);
}

void loop() {
  servo1.write(120);
  servo2.write(120);
  servo3.write(120);

  delay(3000);

  servo1.write(0);
  servo2.write(0);
  servo3.write(0);

  delay(3000);
}
