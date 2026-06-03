#include "dc_motor.h"
#include "config.h"

static bool isRunning = false;
static unsigned long runUntilMs = 0UL;

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

static void SetPwm(int pwm)
{
  int clampedPwm = ClampSignedPwm(pwm);
  int outputPwm = clampedPwm * DC_MOTOR_POLARITY;

  if (outputPwm > 0)
  {
    digitalWrite(PIN_DC_MOTOR_IN1, HIGH);
    digitalWrite(PIN_DC_MOTOR_IN2, LOW);
    analogWrite(PIN_DC_MOTOR_ENA, outputPwm);
  }
  else if (outputPwm < 0)
  {
    digitalWrite(PIN_DC_MOTOR_IN1, LOW);
    digitalWrite(PIN_DC_MOTOR_IN2, HIGH);
    analogWrite(PIN_DC_MOTOR_ENA, -outputPwm);
  }
  else
  {
    DcMotor_Stop();
  }
}

void DcMotor_Init(void)
{
  pinMode(PIN_DC_MOTOR_ENA, OUTPUT);
  pinMode(PIN_DC_MOTOR_IN1, OUTPUT);
  pinMode(PIN_DC_MOTOR_IN2, OUTPUT);

  DcMotor_Stop();
}

void DcMotor_Update(void)
{
  if (!isRunning)
  {
    return;
  }

  if ((long)(millis() - runUntilMs) >= 0)
  {
    DcMotor_Stop();
  }
}

void DcMotor_Run(void)
{
  SetPwm(DC_MOTOR_RUN_PWM);

  runUntilMs = millis() + DC_MOTOR_RUN_TIME_MS;
  isRunning = true;
}

void DcMotor_Stop(void)
{

  analogWrite(PIN_DC_MOTOR_ENA, 0);

  /*
   * Coast stop
   */
  digitalWrite(PIN_DC_MOTOR_IN1, LOW);
  digitalWrite(PIN_DC_MOTOR_IN2, LOW);

  runUntilMs = 0UL;
  isRunning = false;
}

bool DcMotor_IsRunning(void)
{
  return isRunning;
}