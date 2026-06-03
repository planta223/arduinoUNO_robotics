#ifndef DOOR_SENSOR_H
#define DOOR_SENSOR_H

#include <Arduino.h>

void DoorSensor_Init(void);
void DoorSensor_Update(void);

bool DoorSensor_IsClosed(void);
bool DoorSensor_IsOpen(void);

#endif