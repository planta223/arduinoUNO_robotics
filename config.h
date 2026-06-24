#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

/* Pin mapping */
constexpr uint8_t PIN_STATUS_LED     = 13; // 13번 핀은 보통 내장 LED에 연결되어 있음
constexpr uint8_t PIN_DOOR_SENSOR_NO = 2;
constexpr uint8_t PIN_DC_MOTOR_ENA   = 5;
constexpr uint8_t PIN_DC_MOTOR_IN1   = 7;
constexpr uint8_t PIN_DC_MOTOR_IN2   = 8;
constexpr uint8_t PIN_GRIPPER_SERVO = 10;

/* door_sensor.cpp */
constexpr uint8_t DOOR_SENSOR_CLOSED_LEVEL = HIGH; // NO 접점 + 내부 풀업 기준, 자석 감지 시 LOW
constexpr uint8_t DOOR_STATUS_LED_OPEN_LEVEL = LOW;
constexpr uint8_t DOOR_STATUS_LED_CLOSED_LEVEL = HIGH;

/* dc_motor.c */
constexpr int DC_MOTOR_POLARITY = 1; // 튜닝 대상. 1 or -1
constexpr uint8_t DC_MOTOR_PWM_MAX = 255;
constexpr uint8_t DC_MOTOR_RUN_PWM = 200; // 튜닝 대상이지만 수정 필요 없을듯.
constexpr unsigned long DC_MOTOR_RUN_TIME_MS = 700UL; // 튜닝 대상. 대략 1~2초?

/* gripper_servo.cpp */
constexpr int GRIPPER_ANGLE_MIN = 0;
constexpr int GRIPPER_ANGLE_MAX = 180;
constexpr int GRIPPER_OPEN_ANGLE = 62; // 그리퍼 열림 각도 (임시값)
constexpr int GRIPPER_CLOSE_ANGLE = 112; // 그리퍼 닫힘 각도 (임시값)
constexpr int GRIPPER_INIT_ANGLE = GRIPPER_OPEN_ANGLE; // 초기 각도 (열림 상태)
constexpr unsigned long GRIPPER_MOVE_TIME_MS = 1000UL; // 그리퍼가 목표 각도로 이동하는 데 걸리는 시간 (임시값, 실제로는 서보의 속도에 따라 달라질 수 있음)

/* protocol.cpp */
constexpr unsigned long SERIAL_BAUDRATE = 9600UL;
constexpr unsigned long SERIAL_TIMEOUT_MS = 100UL;

constexpr const char CMD_PING[]               = "PING";
constexpr const char CMD_DC_MOTOR_RUN[]       = "D RUN";
constexpr const char CMD_GRIPPER_OPEN[]       = "G OPEN";
constexpr const char CMD_GRIPPER_CLOSE[]      = "G CLOSE";
constexpr const char CMD_ESTOP[]              = "ESTOP";
constexpr const char CMD_MOTOR_STATUS[]       = "MOTOR STATUS";
constexpr const char CMD_DOOR_STATUS[]        = "DOOR STATUS";

constexpr const char RESP_READY[]             = "READY";

constexpr const char RESP_OK_PING[]           = "OK PING";
constexpr const char RESP_OK_DC_MOTOR_RUN[]   = "OK D RUN";
constexpr const char RESP_OK_GRIPPER_OPEN[]   = "OK G OPEN";
constexpr const char RESP_OK_GRIPPER_CLOSE[]  = "OK G CLOSE";
constexpr const char RESP_OK_ESTOP[]          = "OK ESTOP";

constexpr const char RESP_MOTOR_STATUS_BUSY[] = "MOTOR STATUS BUSY";
constexpr const char RESP_MOTOR_STATUS_IDLE[] = "MOTOR STATUS IDLE";
constexpr const char RESP_DOOR_STATUS_OPEN[]  = "DOOR STATUS OPEN";
constexpr const char RESP_DOOR_STATUS_CLOSED[]= "DOOR STATUS CLOSED";

constexpr const char RESP_ERR_UNKNOWN_CMD[]   = "ERR UNKNOWN_CMD";
#endif