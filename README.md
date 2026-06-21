# arduinoUNO_robotics

Arduino UNO, PC Python 서버, PC Vision, UR5e를 연동한 로봇공학 실습 프로젝트입니다.

본 프로젝트는 UR5e 협동로봇을 이용하여 프린터 부품 또는 종이를 자동으로 이송·파지·배치하는 실습 시스템을 구현하는 것을 목표로 합니다. Arduino UNO는 도어 센서, DC 모터, 서보 그리퍼를 제어하는 하위 제어부로 사용하고, Windows PC는 Python 기반 TCP Socket 서버와 Vision 처리부를 담당합니다. UR5e는 PolyScope/URScript에서 PC 서버로 명령을 전송하고, PC 서버는 명령 종류에 따라 Arduino 또는 Vision 모듈로 분기하여 결과를 UR5e로 반환합니다.

---

## 전체 시스템 구조

```text
UR5e PolyScope / URScript
        ↓ TCP Socket
Windows PC Python Server
        ├── USB Serial → Arduino UNO → Door Sensor / DC Motor / Servo Gripper
        └── OpenCV Vision → Logitech C270 Camera
```

### 역할 분담

| 구분               | 역할                                                    |
| ---------------- | ----------------------------------------------------- |
| UR5e             | 로봇 동작, 웨이포인트 이동, 그리퍼/모터/비전 명령 호출                      |
| PC Python Server | UR5e TCP 명령 수신, Arduino Serial 중계, Vision 명령 처리       |
| Arduino UNO      | 도어 센서 입력, DC 모터 PWM 제어, 서보 그리퍼 각도 제어                  |
| PC Vision        | ArUco 기반 뚜껑 상태 판정, ROI/background diff 기반 종이 위치·정렬 판정 |
| Logitech C270    | 비전 입력 카메라                                             |

---

## 폴더 구조

```text
arduinoUNO_robotics/
├── .git/
├── .gitignore
├── README.md
│
├── python/
│   ├── PC_to_arduino.py
│   │   └── Arduino 단독 동작 테스트용 Serial 프로그램
│   │
│   └── PC_server/
│       ├── main_server.py
│       │   └── UR5e-Arduino-Vision 중계 TCP 서버
│       ├── config.py
│       │   └── 서버, Arduino, Camera, Vision 명령/응답 설정
│       ├── vision_checker.py
│       │   └── Vision 통합 wrapper
│       ├── vision_lid.py
│       │   └── ArUco marker 기반 스캐너 뚜껑 open/close 판정
│       └── vision_paper_align.py
│           └── ROI/background diff 기반 종이 위치·정렬 판정
│
├── UR5e_scripts/
│   └── URScript 스크립트 보관
│
├── URprogram_log/
│   └── 날짜별 UR5e 프로그램 기록 보관
│
├── robotics_arduino.ino
├── config.h
├── protocol.h
├── protocol.cpp
├── door_sensor.h
├── door_sensor.cpp
├── dc_motor.h
├── dc_motor.cpp
├── gripper_servo.h
└── gripper_servo.cpp
```

---

## Hardware Configuration

### 사용 하드웨어

| 구분        | 부품                                              |
| --------- | ----------------------------------------------- |
| 하위 제어부    | Arduino UNO                                     |
| 상위 제어부    | Windows PC                                      |
| 카메라       | Logitech C270                                   |
| 그리퍼 모터    | 방수 코어리스 서보 모터 180도 35 kg RC Arduino 호환, HAM4813 |
| 보관함/급지 모터 | OEM 기어박스 장착 모터, NP01D-288                       |
| 모터 드라이버   | L298 2A 모터 드라이버 모듈                              |
| 개폐 센서     | ADIT BL0304 NC/NO 마그네틱 도어 센서                    |
| 로봇        | UR5e 협동로봇                                       |

### 기본 결선

```text
Door NO      -- Arduino D2
Door COM     -- GND

DC Motor ENA -- Arduino D5
DC Motor IN1 -- Arduino D7
DC Motor IN2 -- Arduino D8

Servo Red    -- External 12V
Servo Brown  -- GND
Servo Orange -- Arduino D10

Arduino GND  -- External Power GND 공통 접지
```

주의사항:

* 서보 전원은 Arduino 5V에서 직접 공급하지 않는다.
* 서보 외부 전원 GND와 Arduino GND는 반드시 공통 접지로 연결한다.
* DC 모터 방향이 반대일 경우 `DC_MOTOR_POLARITY`를 수정한다.
* 실제 장착 후 UR5e TCP, Payload, Center of Gravity 설정이 필요하다.

---

## Network Configuration

```text
PC Ethernet 1 : 192.168.0.10
UR5e Ethernet : 192.168.0.20
PC Server     : 0.0.0.0:5000
```

UR5e는 TCP Client로 동작하고, PC Python 서버는 TCP Server로 동작합니다.

---

## Arduino Software

Arduino는 다음 기능을 담당합니다.

* `config.h` 기반 핀 매핑 및 파라미터 관리
* 마그네틱 도어 센서 입력 감지
* DC 모터 PWM 제어
* 서보 그리퍼 open/close 각도 제어
* Serial 기반 명령 처리
* 비상정지 명령 처리

### 주요 Arduino 파라미터

```cpp
PIN_DOOR_SENSOR_NO = 2
PIN_DC_MOTOR_ENA   = 5
PIN_DC_MOTOR_IN1   = 7
PIN_DC_MOTOR_IN2   = 8
PIN_GRIPPER_SERVO  = 10

DC_MOTOR_RUN_PWM      = 120
DC_MOTOR_RUN_TIME_MS  = 1500

GRIPPER_OPEN_ANGLE    = 60
GRIPPER_CLOSE_ANGLE   = 125
GRIPPER_MOVE_TIME_MS  = 1000

SERIAL_BAUDRATE       = 9600
```

위 값들은 현재 임시 튜닝값입니다. 실물 그리퍼, 급지함, 프린터 위치가 확정된 뒤 최종 조정해야 합니다.

---

## PC Python Server

PC 서버는 UR5e에서 받은 명령을 다음 두 경로로 분기합니다.

```text
1. Arduino 명령
   UR5e → PC Server → Arduino Serial → Motor/Sensor/Gripper

2. Vision 명령
   UR5e → PC Server → OpenCV Vision → Camera 판정 결과 반환
```

### 서버 실행 파일

```text
python/PC_server/main_server.py
```

### 서버 설정 파일

```text
python/PC_server/config.py
```

주요 설정:

```python
HOST = "0.0.0.0"
PORT = 5000

ARDUINO_PORT = "COM5"
ARDUINO_BAUDRATE = 9600

CAMERA_INDEX = 1
CAMERA_BACKEND = "dshow"
CAMERA_FRAME_WIDTH = 1280
CAMERA_FRAME_HEIGHT = 720
```

---

## Command Protocol

### Arduino 명령

| UR5e/PC 명령     | 기능                          | Arduino 응답                                |
| -------------- | --------------------------- | ----------------------------------------- |
| `PING`         | Arduino 연결 확인               | `OK PING`                                 |
| `G OPEN`       | 그리퍼 열기                      | `OK G OPEN`                               |
| `G CLOSE`      | 그리퍼 닫기                      | `OK G CLOSE`                              |
| `D RUN`        | DC 모터 일정 시간 구동              | `OK D RUN`                                |
| `ESTOP`        | DC 모터 정지, 그리퍼 running 상태 해제 | `OK ESTOP`                                |
| `MOTOR STATUS` | DC 모터 또는 그리퍼 동작 상태 확인       | `MOTOR STATUS BUSY` / `MOTOR STATUS IDLE` |
| `DOOR STATUS`  | 도어 센서 상태 확인                 | `DOOR STATUS OPEN` / `DOOR STATUS CLOSED` |

### Vision 명령

| UR5e 명령   | 기능                                 | PC 응답                                                                                                                                  |
| --------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `V LID`   | ArUco marker 기반 스캐너 뚜껑 상태 판정       | `LID_OPEN` / `LID_CLOSED`                                                                                                              |
| `V PAPER` | ROI/background diff 기반 종이 위치·정렬 판정 | `PAPER_OK` / `PAPER_NOT_FOUND` / `PAPER_SHIFTED_UP` / `PAPER_SHIFTED_DOWN` / `PAPER_SHIFTED_LEFT` / `PAPER_SHIFTED_RIGHT` / `PAPER_NG` |

Vision 내부 오류 발생 시 fail-safe 기준으로 응답합니다.

```text
V LID 실패  → LID_CLOSED
V PAPER 실패 → PAPER_NG
```

---

## Vision Software

### 1. Lid Check

```text
vision_lid.py
```

ArUco marker 검출 여부로 스캐너 또는 덮개 상태를 판정합니다.

```text
Marker detected     → LID_OPEN
Marker not detected → LID_CLOSED
```

### 2. Paper Alignment Check

```text
vision_paper_align.py
```

저장된 배경 이미지와 현재 프레임을 비교하여 종이 존재 여부와 위치 이탈 방향을 판정합니다.

사용 ROI:

```text
PRESENCE   : 종이 존재 여부 판단 영역
ALIGN_IN   : 정상 정렬 내부 영역
OUT_TOP    : 위쪽 이탈 판단 영역
OUT_LEFT   : 왼쪽 이탈 판단 영역
OUT_RIGHT  : 오른쪽 이탈 판단 영역
OUT_BOTTOM : 아래쪽 이탈 판단 영역
```

판정 결과:

```text
PAPER_OK
PAPER_NOT_FOUND
PAPER_SHIFTED_UP
PAPER_SHIFTED_DOWN
PAPER_SHIFTED_LEFT
PAPER_SHIFTED_RIGHT
PAPER_NG
```

### Vision 단독 테스트

```bash
cd python/PC_server
python vision_checker.py
```

단독 preview 모드 키 입력:

```text
b : 현재 프레임을 background 이미지로 저장
r : background 이미지 다시 로드
p : 현재 프레임으로 paper align 판정
l : 현재 프레임으로 lid 판정
q : 종료
```

---

## Test Programs

### Arduino 단독 테스트

```bash
cd python
python PC_to_arduino.py
```

기능:

* Serial port 목록 출력
* Arduino 연결
* Ping 테스트
* Gripper open/close 테스트
* DC motor run 테스트
* Door sensor 상태 확인
* Motor status 확인
* ESTOP 명령 전송
* Raw command 입력

### PC Server 실행

```bash
cd python/PC_server
python main_server.py
```

실행 전 확인 사항:

```text
1. Arduino가 PC에 USB로 연결되어 있는지 확인
2. config.py의 ARDUINO_PORT가 실제 COM 포트와 일치하는지 확인
3. Logitech C270 카메라가 연결되어 있는지 확인
4. CAMERA_INDEX가 실제 카메라 번호와 일치하는지 확인
5. UR5e와 PC Ethernet IP가 같은 대역인지 확인
6. Windows 방화벽에서 TCP 5000 포트가 차단되지 않는지 확인
```

---

## UR5e Program Flow

현재 목표 flow는 다음과 같습니다.

```text
1. 초기 위치 이동
2. 급지함 또는 프린터 기준 위치 접근
3. 비전 검사 수행
   - V LID
   - V PAPER
4. 종이 또는 부품 위치 판정
5. UR5e 접근 자세 이동
6. 그리퍼 닫기: G CLOSE
7. Motor status 확인
8. 파지 후 상승
9. 목표 위치 이동
10. 그리퍼 열기: G OPEN
11. Motor status 확인
12. 다음 작업 반복 또는 종료
```

실제 PolyScope 프로그램에서는 각 작업 단계 후 fail check를 수행하고, 실패 시 직전 복구 가능한 단계로 복귀하도록 구성합니다.

---

## Current Status

현재 구현 완료 또는 진행 중인 항목은 다음과 같습니다.

### 완료

* Arduino UNO 기반 하위 제어 코드 작성
* DC 모터 제어 모듈 작성
* 서보 그리퍼 제어 모듈 작성
* 도어 센서 입력 모듈 작성
* Serial command protocol 작성
* PC-to-Arduino 단독 테스트 프로그램 작성
* UR5e-Arduino 중계용 PC TCP 서버 작성
* Logitech C270 기반 Vision wrapper 작성
* ArUco 기반 lid open/close 판정 코드 작성
* ROI/background diff 기반 paper align 판정 코드 작성
* UR5e-더미 서버-실제 서버 연동 구조 검토
* VirtualBox URSim 기반 PolyScope flow 작성 진행

### 진행 중

* 실물 UR5e 기준 웨이포인트 지정
* URScript/PolyScope 전체 task flow 정리
* Vision ROI 및 background calibration
* 그리퍼 open/close 각도 튜닝
* DC motor PWM 및 동작 시간 튜닝
* 급지함 구조 설계 및 조립
* 카메라 고정장치 설계 및 조립
* 그리퍼 최종본 조립
* 프린터/급지함 Plane 설정
* TCP, Payload, Center of Gravity 설정

---

## Remaining Work

### Hardware

* 하드웨어 최종 결선
* 단자대, 16AWG 배선, 주름관, 주름관 고정장치 적용
* 피복 제거, 압착, 페룰 단자 처리
* 필요 시 납땜 처리
* 그리퍼 최종본 조립
* 카메라 고정장치 설계 및 조립
* 급지함 설계 및 조립
* 프린터 주변 fixture 정리

### Parameter Tuning

* `GRIPPER_OPEN_ANGLE`
* `GRIPPER_CLOSE_ANGLE`
* `GRIPPER_MOVE_TIME_MS`
* `DC_MOTOR_RUN_PWM`
* `DC_MOTOR_RUN_TIME_MS`
* 도어 센서 open/close 판정 방향
* Vision threshold
* Paper ROI 좌표
* Paper background 이미지
* UR5e waypoint 접근 높이
* UR5e approach/retract 거리

### UR5e Setup

* 실물 UR5e 웨이포인트 지정
* TCP 설정
* Payload 설정
* Center of Gravity 설정
* 급지함 Plane 설정
* 프린터 Plane 설정
* 속도/가속도 제한 설정
* 충돌 또는 과부하 상황 대응 확인

### Software

* URScript socket 통신 함수 정리
* 각 task별 fail check 구조 확정
* `V PAPER` 결과별 복구 동작 작성
* `V LID` 결과별 대기 또는 재시도 구조 작성
* Arduino timeout 발생 시 UR5e 안전정지 처리
* PC 서버 예외 발생 시 fail-safe 응답 확인
* 전체 반복 작업 flow 검증

---

## Notes

* Arduino 명령 문자열은 `config.h`, `PC_to_arduino.py`, `config.py`, `main_server.py`에서 동일하게 유지해야 합니다.
* UR5e에서 문자열 전송 시 개행 문자 처리에 주의해야 합니다.
* Arduino는 한 줄 명령을 `\n` 기준으로 읽습니다.
* PC 서버는 URScript에서 `\n`, `\r` 문자열이 잘못 포함되는 경우를 방어하도록 처리되어 있습니다.
* Vision 판정은 조명, 카메라 위치, 배경 이미지, ROI 설정에 민감하므로 실물 고정 후 다시 calibration해야 합니다.
* 그리퍼 장착 후에는 UR5e의 TCP/Payload/무게중심 설정을 하지 않으면 궤적 오차와 보호정지 가능성이 커질 수 있습니다.
