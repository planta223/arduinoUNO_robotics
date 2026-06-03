#include "gripper_servo.h"
#include "config.h"
#include <Servo.h>

static Servo gripperServo;

static int commandAngle = GRIPPER_INIT_ANGLE;
static bool isRunning = false;
static unsigned long runUntilMs = 0UL;

static int ClampAngle(int angle)
{
  if (angle < GRIPPER_ANGLE_MIN)
  {
    return GRIPPER_ANGLE_MIN;
  }

  if (angle > GRIPPER_ANGLE_MAX)
  {
    return GRIPPER_ANGLE_MAX;
  }

  return angle;
}

static void SetAngle(int angle)
{
  int clampedAngle = ClampAngle(angle);

  if (clampedAngle == commandAngle)
  {
    runUntilMs = 0UL;
    isRunning = false;
    return;
  }

  commandAngle = clampedAngle;
  gripperServo.write(commandAngle);

  runUntilMs = millis() + GRIPPER_MOVE_TIME_MS;
  isRunning = true;
}

void GripperServo_Init(void)
{
  gripperServo.attach(PIN_GRIPPER_SERVO);

  commandAngle = ClampAngle(GRIPPER_INIT_ANGLE);
  gripperServo.write(commandAngle);

  runUntilMs = millis() + GRIPPER_MOVE_TIME_MS;
  isRunning = true;
}

void GripperServo_Update(void)
{
  if (!isRunning)
  {
    return;
  }

  if ((long)(millis() - runUntilMs) >= 0)
  {
    runUntilMs = 0UL;
    isRunning = false;
  }
}

void GripperServo_Open(void)
{
  SetAngle(GRIPPER_OPEN_ANGLE);
}

void GripperServo_Close(void)
{
  SetAngle(GRIPPER_CLOSE_ANGLE);
}

void GripperServo_Stop(void)
{
  /*
   * RC servo는 별도의 stop 명령이 명확하지 않으므로
   * 마지막 command angle을 유지하고 running 상태만 해제한다.
   */
  runUntilMs = 0UL;
  isRunning = false;
}

bool GripperServo_IsRunning(void)
{
  return isRunning;
}