# ============================================================
# PC Socket Server 설정
# ============================================================
HOST = "0.0.0.0"
PORT = 5000
SOCKET_RECV_SIZE = 1024


# ============================================================
# Arduino 설정
# ============================================================
ARDUINO_PORT = "COM5"
ARDUINO_BAUDRATE = 9600
ARDUINO_TIMEOUT_S = 1.0
ARDUINO_RESET_WAIT_S = 2.0


# ============================================================
# Camera 설정
# ============================================================
# TODO: 실제 비전 판정 로직 추가 예정


# ============================================================
# 공통 명령 문자열
# URScript → PC Server → Arduino 기준
# Arduino config.h / protocol.cpp와 동일하게 유지
# ============================================================
CMD_PING = "PING"

CMD_GRIPPER_OPEN = "G OPEN"
CMD_GRIPPER_CLOSE = "G CLOSE"

CMD_DC_MOTOR_RUN = "D RUN"

CMD_ESTOP = "ESTOP"

CMD_MOTOR_STATUS = "MOTOR STATUS"
CMD_DOOR_STATUS = "DOOR STATUS"

# PC에서만 처리하는 명령
CMD_CAMERA_RESULT = "V CAMERA"


# ============================================================
# PC 자체 응답 문자열
# Arduino 응답은 main_server.py에서 그대로 UR5e로 전달
# ============================================================
RESP_PAPER_DETECTED = "PAPER DETECTED"
RESP_PAPER_NOT_DETECTED = "PAPER NOT DETECTED"

RESP_ERR_UNKNOWN_CMD = "ERR UNKNOWN_CMD"
RESP_ERR_ARDUINO_TIMEOUT = "ERR ARDUINO_TIMEOUT"
RESP_ERR_ARDUINO_SERIAL = "ERR ARDUINO_SERIAL"