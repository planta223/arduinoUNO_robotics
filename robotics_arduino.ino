#include "config.h"
#include "door_sensor.h"
#include "dc_motor.h"
#include "gripper_servo.h"
#include "protocol.h"

void DoorSensor_Update(void);
void temp_SerialCommand_Update(void);
void HandleSensorCommand(const String &cmd);
void StopAll(void);

void setup()
{
  DoorSensor_Init();
  DcMotor_Init();
  GripperServo_Init(); 
  Protocol_Init();
}

void loop()
{
  DcMotor_Update();
  GripperServo_Update();
  DoorSensor_Update();
  Protocol_Update();
}