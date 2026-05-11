#ifndef DOOR_SENSOR_H
#define DOOR_SENSOR_H

#include <Arduino.h>

void DoorSensor_Init(void);
bool DoorSensor_IsDetected(void);

#endif