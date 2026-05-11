#include "config.h"
#include "door_sensor.h"
#include "dc_motor.h"

void setup()
{
  Serial.begin(SERIAL_BAUDRATE);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);

  DoorSensor_Init();
  DcMotor_Init();
  pinMode(PIN_STATUS_LED, OUTPUT);

  Serial.println("Arduino control start");
  Serial.println("Input PWM value: -255 ~ 255");
  Serial.println("Example: 120, -120, 0");
}

void loop()
{
  temp_DoorSensor_Update();
  temp_DcMotor_Update();
}

void temp_DoorSensor_Update(void)
{
  if (DoorSensor_IsDetected())
  {
    digitalWrite(PIN_STATUS_LED, HIGH);
  }
  else
  {
    digitalWrite(PIN_STATUS_LED, LOW);
  }
}

void temp_DcMotor_Update(void)
{
  if (Serial.available() <= 0)
  {
    return;
  }

  int pwm = Serial.parseInt();

  DcMotor_SetPwm(pwm);

  Serial.print("DC motor PWM command = ");
  Serial.println(pwm);

  /*
   * Serial.parseInt()는 숫자 뒤에 남은 개행 문자를 남길 수 있으므로 제거
   */
  while (Serial.available() > 0)
  {
    Serial.read();
  }
}