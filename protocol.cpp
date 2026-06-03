#include "protocol.h"
#include "config.h"
#include "dc_motor.h"
#include "gripper_servo.h"
#include "door_sensor.h"

static void HandleMotorStatusCommand(void)
{
  if (DcMotor_IsRunning() || GripperServo_IsRunning())
  {
    Serial.println(RESP_MOTOR_STATUS_BUSY);
  }
  else
  {
    Serial.println(RESP_MOTOR_STATUS_IDLE);
  }
}

static void HandleDoorStatusCommand(void)
{
  if (DoorSensor_IsOpen())
  {
    Serial.println(RESP_DOOR_STATUS_OPEN);
  }
  else
  {
    Serial.println(RESP_DOOR_STATUS_CLOSED);
  }
}

static void EmergencyStop(void)
{
  DcMotor_Stop();
  GripperServo_Stop();
}

static void ExecuteCommand(const String &cmd)
{
  if (cmd.equalsIgnoreCase(CMD_PING))
  {
    Serial.println(RESP_OK_PING);
    return;
  }

  if (cmd.equalsIgnoreCase(CMD_DC_MOTOR_RUN))
  {
    DcMotor_Run();
    Serial.println(RESP_OK_DC_MOTOR_RUN);
    return;
  }

  if (cmd.equalsIgnoreCase(CMD_GRIPPER_OPEN))
  {
    GripperServo_Open();
    Serial.println(RESP_OK_GRIPPER_OPEN);
    return;
  }

  if (cmd.equalsIgnoreCase(CMD_GRIPPER_CLOSE))
  {
    GripperServo_Close();
    Serial.println(RESP_OK_GRIPPER_CLOSE);
    return;
  }

  if (cmd.equalsIgnoreCase(CMD_ESTOP))
  {
    EmergencyStop();
    Serial.println(RESP_OK_ESTOP);
    return;
  }

  if (cmd.equalsIgnoreCase(CMD_MOTOR_STATUS))
  {
    HandleMotorStatusCommand();
    return;
  }

  if (cmd.equalsIgnoreCase(CMD_DOOR_STATUS))
  {
    HandleDoorStatusCommand();
    return;
  }

  Serial.println(RESP_ERR_UNKNOWN_CMD);
}

void Protocol_Init(void)
{
  Serial.begin(SERIAL_BAUDRATE);
  Serial.setTimeout(SERIAL_TIMEOUT_MS);

  Serial.println(RESP_READY);
}

void Protocol_Update(void)
{
  if (Serial.available() <= 0)
  {
    return;
  }

  String cmd = Serial.readStringUntil('\n'); // 모든 Serial 명령은 '\n'으로 종료되어야 한다.
  cmd.trim();

  if (cmd.length() == 0)
  {
    return;
  }

  ExecuteCommand(cmd);
}