#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

/* Pin mapping */
constexpr uint8_t PIN_DOOR_SENSOR = 2;
constexpr uint8_t PIN_STATUS_LED  = 13; // 13번 핀은 보통 내장 LED에 연결되어 있음

/* Logic level */
constexpr uint8_t DOOR_SENSOR_ACTIVE_LEVEL = LOW; // NO 접점 + 내부 풀업 기준, 자석 감지 시 LOW

/* Timing */
constexpr unsigned long DOOR_SENSOR_DEBOUNCE_MS = 30UL; // 도어 센서의 노이즈를 줄이기 위한 디바운스 시간 (30ms)
constexpr unsigned long SERIAL_BAUDRATE = 9600UL;

#endif