#include "gripper_servo.h"
#include "config.h"
#include <Servo.h>

static Servo gripperServo;

/*
 * commandAngle is the last commanded angle.
 * It is not a measured servo angle.
 */
static int commandAngle = GRIPPER_INIT_ANGLE;

/*
 * Servo busy state is estimated by elapsed time.
 * It is not based on actual position feedback.
 */
static unsigned long busyUntilMs = 0UL;

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

static bool IsIntegerString(const String &str)
{
  if (str.length() == 0)
  {
    return false;
  }

  int startIndex = 0;

  if (str.charAt(0) == '-' || str.charAt(0) == '+')
  {
    if (str.length() == 1)
    {
      return false;
    }

    startIndex = 1;
  }

  for (int i = startIndex; i < str.length(); i++)
  {
    if (!isDigit(str.charAt(i)))
    {
      return false;
    }
  }

  return true;
}

void GripperServo_Init(void)
{
  gripperServo.attach(PIN_GRIPPER_SERVO);

  commandAngle = ClampAngle(GRIPPER_INIT_ANGLE);
  gripperServo.write(commandAngle);

  busyUntilMs = millis() + GRIPPER_MOVE_TIME_MS;
}

void GripperServo_Open(void)
{
  GripperServo_SetAngle(GRIPPER_OPEN_ANGLE);
}

void GripperServo_Close(void)
{
  GripperServo_SetAngle(GRIPPER_CLOSE_ANGLE);
}

void GripperServo_SetAngle(int angle)
{
  int clampedAngle = ClampAngle(angle);

  if (clampedAngle == commandAngle)
  {
    return;
  }

  commandAngle = clampedAngle;
  gripperServo.write(commandAngle);

  busyUntilMs = millis() + GRIPPER_MOVE_TIME_MS;
}

bool GripperServo_IsBusy(void)
{
  return (long)(busyUntilMs - millis()) > 0;
}

int GripperServo_GetCommandAngle(void)
{
  return commandAngle;
}

void GripperServo_CommandUpdate(const String &cmd)
{
  String arg = cmd.substring(2);
  arg.trim();

  if (arg.equalsIgnoreCase("OPEN"))
  {
    GripperServo_Open();
    Serial.println("OK G OPEN");
  }
  else if (arg.equalsIgnoreCase("CLOSE"))
  {
    GripperServo_Close();
    Serial.println("OK G CLOSE");
  }
  else if (arg.equalsIgnoreCase("BUSY"))
  {
    Serial.print("BUSY ");
    Serial.println(GripperServo_IsBusy() ? 1 : 0);
  }
  else if (arg.equalsIgnoreCase("ANGLE"))
  {
    Serial.print("ANGLE ");
    Serial.println(GripperServo_GetCommandAngle());
  }
  else
  {
    if (!IsIntegerString(arg))
    {
      Serial.println("ERR G");
      return;
    }

    int angle = arg.toInt();

    GripperServo_SetAngle(angle);

    Serial.print("OK G ");
    Serial.println(GripperServo_GetCommandAngle());
  }
}