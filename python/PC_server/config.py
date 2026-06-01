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
# 추가 예정


# ============================================================
# UR5e → PC 명령 문자열
# ============================================================
CMD_PING = "PING"

CMD_GRIPPER_OPEN = "G OPEN"
CMD_GRIPPER_CLOSE = "G CLOSE"

CMD_DC_MOTOR_STOP = "D STOP"
CMD_DC_MOTOR_RUN = "D RUN"

CMD_SENSOR_DOOR = "S DOOR"

CMD_CAMERA_RESULT = "V CAMERA"


# ============================================================
# PC → Arduino 명령 문자열
# ============================================================
ARDUINO_GRIPPER_OPEN_CMD = "G OPEN"
ARDUINO_GRIPPER_CLOSE_CMD = "G CLOSE"

ARDUINO_DC_MOTOR_STOP_CMD = "D 0"
ARDUINO_DC_MOTOR_RUN_CMD = "D 120"

ARDUINO_SENSOR_DOOR_CMD = "S DOOR"


# ============================================================
# PC → UR5e 응답 문자열
# ============================================================
RESP_OK = "OK"

RESP_DOOR_OPEN = "DOOR 1"
RESP_DOOR_CLOSED = "DOOR 0"

RESP_PAPER_DETECTED = "PAPER 1"
RESP_PAPER_NOT_DETECTED = "PAPER 0"

RESP_ERR_UNKNOWN_CMD = "ERR UNKNOWN_CMD"
RESP_ERR_ARDUINO_TIMEOUT = "ERR ARDUINO_TIMEOUT"
