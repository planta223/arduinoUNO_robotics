#include "door_sensor.h"
#include "config.h"

void DoorSensor_Init(void)
{
  pinMode(PIN_DOOR_SENSOR_NO, INPUT_PULLUP);
}

bool DoorSensor_IsDetected(void)
{
  return digitalRead(PIN_DOOR_SENSOR_NO) == DOOR_SENSOR_ACTIVE_LEVEL;
}