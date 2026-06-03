#ifndef DC_MOTOR_H
#define DC_MOTOR_H

#include <Arduino.h>

void DcMotor_Init(void); // coast stop
void DcMotor_Update(void);

void DcMotor_Run(void);
void DcMotor_Stop(void);

bool DcMotor_IsRunning(void);

#endif