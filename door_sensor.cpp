#include "door_sensor.h"
#include "config.h"

static bool isClosed = false;

static bool ReadDoorClosed(void)
{
  return digitalRead(PIN_DOOR_SENSOR_NO) == DOOR_SENSOR_CLOSED_LEVEL;
}

static void UpdateStatusLed(void)
{
  digitalWrite(
    PIN_STATUS_LED,
    isClosed ? DOOR_STATUS_LED_CLOSED_LEVEL : DOOR_STATUS_LED_OPEN_LEVEL
  );
}

void DoorSensor_Init(void)
{
  pinMode(PIN_DOOR_SENSOR_NO, INPUT_PULLUP);
  pinMode(PIN_STATUS_LED, OUTPUT);

  isClosed = ReadDoorClosed();
  UpdateStatusLed();
}

void DoorSensor_Update(void)
{
  isClosed = ReadDoorClosed();
  UpdateStatusLed();
}

bool DoorSensor_IsClosed(void)
{
  return isClosed;
}

bool DoorSensor_IsOpen(void)
{
  return !isClosed;
}