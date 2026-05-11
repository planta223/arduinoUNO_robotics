#ifndef DC_MOTOR_H
#define DC_MOTOR_H

#include <Arduino.h>

void DcMotor_Init(void);
void DcMotor_SetPwm(int pwm);
void DcMotor_Stop(void);
void DcMotor_Brake(void);

void DcMotor_CommandUpdate(const String &cmd);

#endif