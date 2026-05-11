#include "config.h"
#include "door_sensor.h"
#include "dc_motor.h"
#include "gripper_servo.h"

void temp_DoorSensor_Update(void);
void temp_SerialCommand_Update(void);
void HandleSensorCommand(const String &cmd);
void StopAll(void);

void setup()
{
  Serial.begin(SERIAL_BAUDRATE);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);

  DoorSensor_Init();
  DcMotor_Init();
  GripperServo_Init();

  pinMode(PIN_STATUS_LED, OUTPUT);

  Serial.println("READY");
}

void loop()
{
  temp_DoorSensor_Update();
  temp_SerialCommand_Update();
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

void temp_SerialCommand_Update(void)
{
  if (Serial.available() <= 0)
  {
    return;
  }

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd.length() == 0)
  {
    return;
  }

  if (cmd.startsWith("D ") || cmd.startsWith("d "))
  {
    DcMotor_CommandUpdate(cmd);
  }
  else if (cmd.startsWith("G ") || cmd.startsWith("g "))
  {
    GripperServo_CommandUpdate(cmd);
  }
  else if (cmd.startsWith("S ") || cmd.startsWith("s "))
  {
    HandleSensorCommand(cmd);
  }
  else if (cmd.equalsIgnoreCase("STOP"))
  {
    StopAll();
    Serial.println("OK STOP");
  }
  else
  {
    Serial.println("ERR UNKNOWN");
  }
}

void HandleSensorCommand(const String &cmd)
{
  String arg = cmd.substring(2);
  arg.trim();

  if (arg.equalsIgnoreCase("DOOR"))
  {
    Serial.print("DOOR ");
    Serial.println(DoorSensor_IsDetected() ? 1 : 0);
  }
  else
  {
    Serial.println("ERR SENSOR");
  }
}

void StopAll(void)
{
  DcMotor_Stop();

  /*
   * RC servo는 별도 stop 개념이 불명확하므로
   * 마지막 command angle을 유지한다.
   */
}