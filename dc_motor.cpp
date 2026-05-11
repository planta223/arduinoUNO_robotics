#include "dc_motor.h"
#include "config.h"

static int ClampSignedPwm(int pwm)
{
  if (pwm > DC_MOTOR_PWM_MAX)
  {
    return DC_MOTOR_PWM_MAX;
  }

  if (pwm < -DC_MOTOR_PWM_MAX)
  {
    return -DC_MOTOR_PWM_MAX;
  }

  return pwm;
}

void DcMotor_Init(void)
{
  pinMode(PIN_DC_MOTOR_ENA, OUTPUT);
  pinMode(PIN_DC_MOTOR_IN1, OUTPUT);
  pinMode(PIN_DC_MOTOR_IN2, OUTPUT);

  DcMotor_Stop();
}

void DcMotor_SetPwm(int pwm)
{
  int clampedPwm = ClampSignedPwm(pwm);

  if (clampedPwm > 0)
  {
    digitalWrite(PIN_DC_MOTOR_IN1, HIGH);
    digitalWrite(PIN_DC_MOTOR_IN2, LOW);
    analogWrite(PIN_DC_MOTOR_ENA, clampedPwm);
  }
  else if (clampedPwm < 0)
  {
    digitalWrite(PIN_DC_MOTOR_IN1, LOW);
    digitalWrite(PIN_DC_MOTOR_IN2, HIGH);
    analogWrite(PIN_DC_MOTOR_ENA, -clampedPwm);
  }
  else
  {
    DcMotor_Stop();
  }
}

void DcMotor_Stop(void)
{
  analogWrite(PIN_DC_MOTOR_ENA, 0);

  /*
   * Coast stop
   */
  digitalWrite(PIN_DC_MOTOR_IN1, LOW);
  digitalWrite(PIN_DC_MOTOR_IN2, LOW);
}

void DcMotor_Brake(void)
{
  /*
   * Dynamic braking
   */
  analogWrite(PIN_DC_MOTOR_ENA, DC_MOTOR_PWM_MAX);
  digitalWrite(PIN_DC_MOTOR_IN1, HIGH);
  digitalWrite(PIN_DC_MOTOR_IN2, HIGH);
}

void DcMotor_CommandUpdate(const String &cmd)
{
  String arg = cmd.substring(2);
  arg.trim();

  int pwm = ClampSignedPwm(arg.toInt());

  DcMotor_SetPwm(pwm);

  Serial.print("OK D ");
  Serial.println(pwm);
}