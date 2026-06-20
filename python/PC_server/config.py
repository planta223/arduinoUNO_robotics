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
CAMERA_INDEX = 1
CAMERA_BACKEND = "dshow"   # Windows + Logitech C270 기준
CAMERA_FRAME_WIDTH = 1280
CAMERA_FRAME_HEIGHT = 720

CAMERA_AUTO_EXPOSURE = 0
CAMERA_EXPOSURE = -1
CAMERA_GAIN = 0
CAMERA_BRIGHTNESS = 128
CAMERA_CONTRAST = 128
CAMERA_AUTO_WB = 0
CAMERA_WB_TEMPERATURE = 7000
CAMERA_BACKLIGHT = 0
CAMERA_WARMUP_FRAMES = 30

ARUCO_DICTIONARY = "DICT_4X4_50"
ARUCO_MARKER_ID = 0

PAPER_CONFIG_PATH = "paper_align_config.json"
PAPER_BACKGROUND_PATH = "paper_align_config_background.png"


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

# vision 명령 (URScript → PC Server 기준)
CMD_VISION_LID_STATUS = "V LID"    # ArUco 기반 스캐너 뚜껑 open/close 판정
CMD_VISION_PAPER_ALIGN = "V PAPER" # ROI/background diff 기반 종이 위치·정렬 판정


# ============================================================
# PC 자체 응답 문자열
# Arduino 응답은 main_server.py에서 그대로 UR5e로 전달
# ============================================================
RESP_ERR_UNKNOWN_CMD = "ERR UNKNOWN_CMD"
RESP_ERR_ARDUINO_TIMEOUT = "ERR ARDUINO_TIMEOUT"
RESP_ERR_ARDUINO_SERIAL = "ERR ARDUINO_SERIAL"

# vision 응답
RESP_LID_OPEN = "LID_OPEN"
RESP_LID_CLOSED = "LID_CLOSED"

RESP_PAPER_OK = "PAPER_OK"
RESP_PAPER_NOT_FOUND = "PAPER_NOT_FOUND"

RESP_PAPER_SHIFTED_UP = "PAPER_SHIFTED_UP"       # 종이가 정상 위치보다 위쪽으로 벗어남
RESP_PAPER_SHIFTED_DOWN = "PAPER_SHIFTED_DOWN"   # 종이가 정상 위치보다 아래쪽으로 벗어남
RESP_PAPER_SHIFTED_LEFT = "PAPER_SHIFTED_LEFT"   # 종이가 정상 위치보다 왼쪽으로 벗어남
RESP_PAPER_SHIFTED_RIGHT = "PAPER_SHIFTED_RIGHT" # 종이가 정상 위치보다 오른쪽으로 벗어남

RESP_PAPER_NG = "PAPER_NG"
