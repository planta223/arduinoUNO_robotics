#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

/* Timing */
constexpr unsigned long SERIAL_BAUDRATE = 9600UL;
constexpr unsigned long SERIAL_TIMEOUT_MS = 100UL;

/* Pin mapping */
constexpr uint8_t PIN_STATUS_LED     = 13; // 13번 핀은 보통 내장 LED에 연결되어 있음
constexpr uint8_t PIN_DOOR_SENSOR_NO = 2;
constexpr uint8_t PIN_DC_MOTOR_ENA   = 5;
constexpr uint8_t PIN_DC_MOTOR_IN1   = 7;
constexpr uint8_t PIN_DC_MOTOR_IN2   = 8;
constexpr uint8_t PIN_GRIPPER_SERVO = 10;


/* door_sensor.c */
constexpr uint8_t DOOR_SENSOR_ACTIVE_LEVEL = LOW; // NO 접점 + 내부 풀업 기준, 자석 감지 시 LOW
constexpr unsigned long DOOR_SENSOR_DEBOUNCE_MS = 30UL; // 도어 센서의 노이즈를 줄이기 위한 디바운스 시간 (30ms)

/* dc_motor.c */
constexpr uint8_t DC_MOTOR_PWM_MAX = 255;
constexpr uint8_t DC_MOTOR_TEST_PWM = 120;

/* gripper_servo.c */
constexpr int GRIPPER_ANGLE_MIN = 0;
constexpr int GRIPPER_ANGLE_MAX = 180;
constexpr int GRIPPER_OPEN_ANGLE = 70; // 그리퍼 열림 각도 (임시값)
constexpr int GRIPPER_CLOSE_ANGLE = 110; // 그리퍼 닫힘 각도 (임시값)
constexpr int GRIPPER_INIT_ANGLE = 90; // 그리퍼 초기 각도 (임시값)
constexpr unsigned long GRIPPER_MOVE_TIME_MS = 1000UL; // 그리퍼가 목표 각도로 이동하는 데 걸리는 시간 (임시값, 실제로는 서보의 속도에 따라 달라질 수 있음)

#endif