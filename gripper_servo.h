#ifndef GRIPPER_SERVO_H
#define GRIPPER_SERVO_H

#include <Arduino.h>

void GripperServo_Init(void);
void GripperServo_Update(void);

void GripperServo_Open(void);
void GripperServo_Close(void);
void GripperServo_Stop(void);

bool GripperServo_IsRunning(void);

#endif