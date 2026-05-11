#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

/* Timing */
constexpr unsigned long SERIAL_BAUDRATE = 9600UL;
constexpr unsigned long SERIAL_TIMEOUT_MS = 100UL;

/* Pin mapping */
constexpr uint8_t PIN_STATUS_LED     = 13; // 13번 핀은 보통 내장 LED에 연결되어 있음
constexpr uint8_t PIN_DOOR_SENSOR_NO = 2;
constexpr uint8_t PIN_DC_MOTOR_ENA   = 9;
constexpr uint8_t PIN_DC_MOTOR_IN1   = 7;
constexpr uint8_t PIN_DC_MOTOR_IN2   = 8;

/* dc_motor.c */
constexpr uint8_t DC_MOTOR_PWM_MAX = 255;
constexpr uint8_t DC_MOTOR_TEST_PWM = 120;

/* door_sensor.c */
constexpr uint8_t DOOR_SENSOR_ACTIVE_LEVEL = LOW; // NO 접점 + 내부 풀업 기준, 자석 감지 시 LOW
constexpr unsigned long DOOR_SENSOR_DEBOUNCE_MS = 30UL; // 도어 센서의 노이즈를 줄이기 위한 디바운스 시간 (30ms)

#endif