Status: Completed on 2026-06-23

# robotics_arduino

UR5e, Arduino UNO, Windows PC Python 서버, OpenCV 비전을 연결해 종이 위치와 스캐너 상태를 확인하고 그리퍼 동작을 연동하는 프로젝트입니다.

이 README는 현재 저장소의 코드 상태를 기준으로 정리했습니다.  
특히 `dc motor` 관련 파일과 명령 문자열은 일부 남아 있지만, 최종 운용 기준에서는 사용하지 않습니다.

## 현재 구성 요약

- Arduino UNO는 문 센서와 서보 그리퍼를 담당합니다.
- Windows PC Python 서버는 UR5e TCP 요청을 받아 Arduino Serial 또는 Vision 로직으로 분기합니다.
- Vision은 Logitech C270 카메라 기준으로 동작하며, 두 가지 판정을 제공합니다.
- `V LID`: ArUco 마커 기반 뚜껑 open/close 판정
- `V PAPER`: 배경 차분 + ROI 기반 종이 존재/정렬 판정
- DC motor 경로는 레거시 호환용 흔적만 남아 있고, 현재 펌웨어에서는 실제 구동되지 않습니다.

## 시스템 구조

```text
UR5e PolyScope / URScript
        |
        | TCP Socket
        v
Windows PC Python Server
        |                         |
        | USB Serial              | OpenCV
        v                         v
Arduino UNO                 Logitech C270 Camera
  - Door Sensor
  - Servo Gripper
```

## 저장소 구조

```text
robotics_arduino/
├─ README.md
├─ robotics_arduino.ino
├─ config.h
├─ protocol.h
├─ protocol.cpp
├─ door_sensor.h
├─ door_sensor.cpp
├─ gripper_servo.h
├─ gripper_servo.cpp
├─ dc_motor.h
├─ dc_motor.cpp
├─ UR5e_scripts/
│  ├─ Init_Variables.script
│  ├─ Socket_Open.script
│  ├─ Check_Camera_Open.script
│  ├─ Check_Camera_Align.script
│  ├─ Check_Door_Open.script
│  ├─ Check_Door_Closed.script
│  ├─ Gripper_Open.script
│  ├─ Gripper_Close.script
│  ├─ DC_Run.script
│  ├─ Error_Stop.script
│  └─ Enter_Next_Task.script
├─ UR5e_program_log/
│  └─ UR 프로그램 백업/로그
└─ python/
   ├─ pc_to_arduino.py
   └─ PC_server/
      ├─ main_server.py
      ├─ config.py
      ├─ camera_settings.py
      ├─ vision_checker.py
      ├─ vision_lid.py
      ├─ vision_paper_align.py
      ├─ paper_align_config.json
      ├─ paper_align_config_background.png
      ├─ run_main_server.bat
      └─ run_paper_align.bat
```

## 역할별 설명

### 1. Arduino 펌웨어

주요 파일:

- `robotics_arduino.ino`
- `config.h`
- `protocol.cpp`
- `door_sensor.*`
- `gripper_servo.*`

현재 실제 동작:

- 문 센서 상태 읽기
- 상태 LED 갱신
- 서보 그리퍼 open/close 명령 처리
- Serial 명령 수신 및 응답

현재 코드상 비활성/레거시:

- `dc_motor.cpp` / `dc_motor.h`
- `D RUN` 명령

주의할 점:

- `setup()`에서 `DcMotor_Init()`을 호출하지 않습니다.
- `loop()`에서 `DcMotor_Update()`를 호출하지 않습니다.
- `protocol.cpp`에서 `D RUN` 수신 시 실제 모터 함수를 호출하지 않고 `OK D RUN`만 반환합니다.

즉, 현재 저장소 기준으로 DC motor는 "명령/파일 흔적은 있으나 실제 운용은 하지 않는 상태"입니다.

### 2. PC Python 서버

주요 파일:

- `python/PC_server/main_server.py`
- `python/PC_server/config.py`

역할:

- UR5e의 TCP 클라이언트 요청 수신
- Arduino Serial 명령 릴레이
- Vision 명령 직접 처리
- 응답 문자열을 UR5e로 반환

명령 분기 방식:

- Arduino 계열: `PING`, `G OPEN`, `G CLOSE`, `D RUN`, `ESTOP`, `MOTOR STATUS`, `DOOR STATUS`
- Vision 계열: `V LID`, `V PAPER`

### 3. Vision

주요 파일:

- `python/PC_server/vision_checker.py`
- `python/PC_server/vision_lid.py`
- `python/PC_server/vision_paper_align.py`
- `python/PC_server/paper_align_config.json`
- `python/PC_server/paper_align_config_background.png`

역할:

- `V LID`: ArUco 마커가 보이면 `LID_OPEN`, 아니면 `LID_CLOSED`
- `V PAPER`: 저장된 배경 이미지와 현재 프레임을 비교해 종이 존재 및 정렬 상태 판정

Fail-safe 동작:

- Vision 초기화 실패 또는 카메라 읽기 실패 시 `V LID`는 `LID_CLOSED`
- Vision 초기화 실패, 배경 없음, ROI 미설정, 카메라 오류 시 `V PAPER`는 `PAPER_NG`

### 4. UR5e 스크립트

`UR5e_scripts/`에는 PolyScope에서 사용하거나 참고할 수 있는 URScript 조각이 들어 있습니다.

대표 파일:

- `Init_Variables.script`: 공용 변수/명령/응답 문자열 정의
- `Socket_Open.script`: PC 서버 연결 및 `PING` 확인
- `Check_Camera_Open.script`: `V LID` 요청
- `Check_Camera_Align.script`: `V PAPER` 요청
- `Gripper_Open.script`, `Gripper_Close.script`: 그리퍼 제어
- `Check_Door_Open.script`, `Check_Door_Closed.script`: 센서 상태 확인

`UR5e_program_log/`는 실행 로그 및 내보낸 프로그램 백업 성격의 폴더입니다.

## 하드웨어 기준

### 현재 사용 기준

| 구분 | 상태 | 비고 |
| --- | --- | --- |
| Arduino UNO | 사용 | 하위 제어 |
| UR5e | 사용 | 상위 동작 제어 |
| Logitech C270 | 사용 | Vision 입력 |
| Door Sensor | 사용 | `DOOR STATUS` |
| Servo Gripper | 사용 | `G OPEN`, `G CLOSE` |
| DC Motor | 미사용 | 코드 흔적만 남아 있음 |
| Motor Driver(L298 등) | 미사용 | 최종 운용 기준 제외 |

### 핀 매핑

현재 코드 기준 핀:

| 기능 | 핀 |
| --- | --- |
| 상태 LED | `D13` |
| Door Sensor NO | `D2` |
| Servo Signal | `D10` |

레거시 DC motor 핀:

| 기능 | 핀 |
| --- | --- |
| DC Motor ENA | `D5` |
| DC Motor IN1 | `D7` |
| DC Motor IN2 | `D8` |

## 네트워크/포트 기본값

`python/PC_server/config.py` 기준:

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

`UR5e_scripts/Socket_Open.script` 예시는 PC 서버를 `192.168.0.10:5000`으로 바라보도록 되어 있습니다.

## 실행 준비

### Arduino

1. `robotics_arduino.ino`를 Arduino IDE에서 엽니다.
2. 대상 보드를 Arduino UNO로 설정합니다.
3. 업로드 후 Serial baudrate는 `9600`을 사용합니다.

Arduino 쪽 외부 라이브러리는 기본 `Servo` 라이브러리만 사용합니다.

### Python

Windows PC에서 Python 환경을 준비한 뒤 아래 패키지를 설치합니다.

```bash
python -m pip install pyserial numpy opencv-contrib-python
```

설명:

- `pyserial`: Arduino 통신
- `numpy`: Vision 처리
- `opencv-contrib-python`: OpenCV + ArUco 모듈

## 실행 순서

### 1. PC 서버 설정 확인

`python/PC_server/config.py`에서 아래 항목을 실제 환경에 맞춥니다.

- `ARDUINO_PORT`
- `CAMERA_INDEX`
- 필요 시 카메라 세부 설정값

### 2. PC 서버 실행

```bash
cd python/PC_server
python main_server.py
```

또는:

```bash
python/PC_server/run_main_server.bat
```

### 3. UR5e에서 소켓 연결

`UR5e_scripts/Init_Variables.script`와 `Socket_Open.script`를 기준으로 PC 서버에 접속합니다.

일반 흐름:

1. 소켓 오픈
2. `PING` 송신
3. `OK PING` 확인
4. 이후 그리퍼/센서/비전 명령 사용

## 단독 테스트 도구

### Arduino Serial 테스트

```bash
cd python
python pc_to_arduino.py
```

기능:

- 사용 가능한 시리얼 포트 출력
- `PING` 테스트
- 그리퍼 open/close
- 문 센서 상태 확인
- `MOTOR STATUS` 확인
- `ESTOP`
- Raw command 입력

`DC motor` 메뉴는 남아 있지만, 현재 펌웨어에서는 실제 구동 테스트가 되지 않습니다.

### Paper Align 캘리브레이션/디버그

```bash
cd python/PC_server
python vision_paper_align.py
```

또는:

```bash
python/PC_server/run_paper_align.bat
```

주요 키:

- `b`: 현재 프레임을 빈 배경 이미지로 저장
- `1` ~ `6`: ROI 설정 시작
- `z`: 마지막 ROI 제거
- `r`: ROI 전체 초기화
- `s`: 설정 저장
- `e`: 설정 다시 읽기
- `x` 또는 `Esc`: ROI 선택 취소
- `q`: 종료

ROI 종류:

- `PRESENCE`
- `ALIGN_IN`
- `OUT_TOP`
- `OUT_LEFT`
- `OUT_RIGHT`
- `OUT_BOTTOM`

### Lid 판정 단독 테스트

```bash
cd python/PC_server
python vision_lid.py --camera-index 1 --backend dshow --aruco-dictionary DICT_4X4_50 --marker-id 0
```

## 명령 프로토콜

### Arduino 계열 명령

| 명령 | 현재 동작 | 응답 |
| --- | --- | --- |
| `PING` | 연결 확인 | `OK PING` |
| `G OPEN` | 서보 그리퍼 열기 | `OK G OPEN` |
| `G CLOSE` | 서보 그리퍼 닫기 | `OK G CLOSE` |
| `D RUN` | 레거시 호환용 응답만 반환, 실제 모터 구동 없음 | `OK D RUN` |
| `ESTOP` | 서보 running 상태 해제 | `OK ESTOP` |
| `MOTOR STATUS` | 그리퍼 running window 기준 busy/idle 반환 | `MOTOR STATUS BUSY` / `MOTOR STATUS IDLE` |
| `DOOR STATUS` | 문 센서 상태 반환 | `DOOR STATUS OPEN` / `DOOR STATUS CLOSED` |

### Vision 계열 명령

| 명령 | 설명 | 응답 |
| --- | --- | --- |
| `V LID` | ArUco 마커 기반 뚜껑 상태 판정 | `LID_OPEN` / `LID_CLOSED` |
| `V PAPER` | 배경 차분 + ROI 기반 종이 정렬 판정 | `PAPER_OK` / `PAPER_NOT_FOUND` / `PAPER_SHIFTED_UP` / `PAPER_SHIFTED_DOWN` / `PAPER_SHIFTED_LEFT` / `PAPER_SHIFTED_RIGHT` / `PAPER_NG` |

## Paper Align 설정 파일

현재 저장소에는 다음 두 파일이 포함되어 있습니다.

- `python/PC_server/paper_align_config.json`
- `python/PC_server/paper_align_config_background.png`

의미:

- `paper_align_config.json`: ROI와 threshold 설정
- `paper_align_config_background.png`: 종이가 없는 기준 배경 이미지

이 둘 중 하나라도 준비되지 않으면 `V PAPER`는 정상 판정을 못 하고 `PAPER_NG`로 떨어질 수 있습니다.

## 구현상 주의사항

- `MOTOR STATUS`는 이름과 달리 현재 DC motor 상태가 아니라 사실상 그리퍼 동작 중 여부를 반환합니다.
- `ESTOP`은 서보 전원을 끄는 하드웨어 정지가 아니라, 코드상 running 상태를 해제하는 수준입니다.
- `D RUN`은 현재 프로토콜 호환성 유지를 위한 자리표시자에 가깝습니다.
- `vision_checker.py`는 `V PAPER` 호출 시 디버그 창을 띄웁니다.
- `vision_lid.py`는 ArUco를 사용하므로 `opencv-contrib-python`이 필요합니다.
- 카메라 위치, 조명, 배경 이미지, ROI, threshold에 따라 `V PAPER` 결과 민감도가 크게 달라집니다.

## 현재 README 기준 결론

이 저장소의 현재 실사용 경로는 아래와 같습니다.

1. UR5e가 PC Python 서버에 TCP로 명령을 보냅니다.
2. PC 서버가 명령을 Arduino 또는 Vision으로 분기합니다.
3. Arduino는 문 센서와 서보 그리퍼를 담당합니다.
4. Vision은 뚜껑 상태와 종이 정렬 상태를 판정합니다.
5. DC motor는 코드 흔적은 있으나 현재 최종 구성에서는 사용하지 않습니다.
