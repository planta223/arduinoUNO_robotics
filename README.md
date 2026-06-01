# arduinoUNO_robotics

Arduino UNO, PC Python 서버, UR5e를 연동한 로봇공학 실습 프로젝트입니다.

본 프로젝트는 Arduino UNO를 하위 제어부로 사용하여 도어 센서, DC 모터, 서보 그리퍼를 제어하고, PC Python 서버를 통해 UR5e와 TCP Socket 통신을 수행하는 구조입니다.

## 폴더 구조

arduinoUNO_robotics/
│
├── .git/
├── .gitignore
├── README.md
│
├── python/
│   ├── PC_to_arduino.py : PC-아두이노 동작 테스트용
│   └── PC_server/
│       ├── main_server.py : Arduino-PC-UR5e 중계용
│       └── config.py
│
├── UR5e_scripts/  : URScript 스크립트 보관
│
├── URprogram_log/ : 날짜별 UR5e 프로그램 기록 보관
│
├── robotics_arduino.ino
├── config.h
└── X.cpp/h

## Hardware Configuration

Door NO  -- D2
Door COM -- GND

## Arduino Software

- `config.h` 기반 핀 매핑 및 상수 관리
- 마그네틱 도어 센서 입력 감지
- DC 모터 PWM 제어
- 서보 모터 제어

## ip 설정
- PC Ethernet 1  : ip 192.168.0.10
- UR5e Ethernet  : ip 192.168.0.20

## 남은 해야 할 일

- 하드웨어 최종단계 결선 (필요 : 단자대, 16AWG, 주름관, 주름관 고정장치, 피복제거기, 압착기, 페룰단자, 납땜장비)
- 하드웨어 최종파라미터 결정 (Gripper Open/Close 각도, DC motor PWM 값, Gripper, Step/DC Motor 대기 시간, 그 외)
- 카메라 추가 및 Python 파일 연동 예정
- 그리퍼 최종본 조립, 카메라 고정장치 설계 및 조립, 급지함 설계 및 조립 필요
- 그리퍼 완성 후 UR5e TCP, Payload, 무게중심 설정
- 급지함 완성 후 UR5e Plane (급지함 및 프린터) 설정
- VirtualBox URSim(Universal Robots 5.11) 기반 전체 프로그램 flow 작성
- 실물 UR5e 기반 웨이포인트 지정