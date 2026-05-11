#include "config.h"
#include "door_sensor.h"

void setup() {
  Serial.begin(9600);

  DoorSensor_Init();
  pinMode(PIN_STATUS_LED, OUTPUT);
}

void loop() {
  if (DoorSensor_IsDetected()) {
    digitalWrite(PIN_STATUS_LED, HIGH);
  } else {
    digitalWrite(PIN_STATUS_LED, LOW);
  }

  delay(100);
}