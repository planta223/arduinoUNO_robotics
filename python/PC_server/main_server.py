'''
Windows PC에서 실행되는 UR5e-Arduino 중계 서버입니다.

전체 구조:
UR5e PolyScope
    ↓ TCP Socket
PC Python Server
    ↓ USB Serial
Arduino Uno
    ↓ GPIO / PWM
DC Motor, Gripper Servo, Door Sensor

프로토콜 기준:
URScript → PC Server → Arduino 명령 문자열을 동일하게 유지합니다.

사용 명령:
PING
G OPEN
G CLOSE
D RUN
ESTOP
MOTOR STATUS
DOOR STATUS
V CAMERA

원칙:
1. PC는 명령을 임의 변환하지 않습니다.
2. Arduino로 전달 가능한 명령은 그대로 전달합니다.
3. Arduino 응답은 단순화하지 않고 그대로 UR5e로 반환합니다.
4. V CAMERA는 Arduino가 아니라 PC에서 처리합니다.
'''

import socket
import time

import serial
from serial.tools import list_ports

import config


def list_serial_ports() -> None:
    ports = list(list_ports.comports())

    if not ports:
        print("[Arduino] No serial ports found.")
        return

    print("[Arduino] Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")


def open_arduino() -> serial.Serial:
    '''
    Arduino Serial 포트를 엽니다.
    Arduino Uno는 Serial 연결 시 리셋될 수 있으므로 일정 시간 대기합니다.
    '''

    ser = serial.Serial(
        port=config.ARDUINO_PORT,
        baudrate=config.ARDUINO_BAUDRATE,
        timeout=config.ARDUINO_TIMEOUT_S,
    )

    time.sleep(config.ARDUINO_RESET_WAIT_S)
    clear_arduino_startup_messages(ser)

    return ser


def clear_arduino_startup_messages(ser: serial.Serial) -> None:
    '''
    Arduino 부팅 직후 READY 등의 메시지를 읽어서 제거합니다.
    '''

    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if line:
            print(f"[Arduino startup] {line}")


def clean_ur_command(cmd: str) -> str:
    '''
    URScript에서 문자열 "\\n", "\\r" 자체를 잘못 보낸 경우를 방어합니다.
    실제 개행 문자는 recv 후 strip()에서 제거됩니다.
    '''

    cmd = cmd.strip()
    cmd = cmd.replace("\\n", "")
    cmd = cmd.replace("\\r", "")
    cmd = cmd.strip()

    return cmd


def send_to_arduino(ser: serial.Serial, cmd: str) -> str:
    '''
    Arduino에 한 줄 명령을 보내고 한 줄 응답을 받습니다.
    Arduino 응답은 수정하지 않고 그대로 반환합니다.
    '''

    cmd = cmd.strip()

    if not cmd:
        return config.RESP_ERR_UNKNOWN_CMD

    print(f"[PC -> Arduino] {cmd}")

    try:
        # 이전 명령의 잔여 응답 제거
        ser.reset_input_buffer()

        # Arduino Protocol_Update()는 '\n' 기준으로 한 줄 명령을 읽음
        ser.write((cmd + "\n").encode("utf-8"))
        ser.flush()

        response = ser.readline().decode("utf-8", errors="ignore").strip()

    except serial.SerialException as exc:
        print(f"[Arduino Serial Error] {exc}")
        return config.RESP_ERR_ARDUINO_SERIAL

    except OSError as exc:
        print(f"[Arduino OS Error] {exc}")
        return config.RESP_ERR_ARDUINO_SERIAL

    if not response:
        print(f"[Arduino -> PC] {config.RESP_ERR_ARDUINO_TIMEOUT}")
        return config.RESP_ERR_ARDUINO_TIMEOUT

    print(f"[Arduino -> PC] {response}")
    return response


def handle_camera_command() -> str:
    '''
    비전 판정 명령 처리부입니다.
    현재는 임시로 PAPER 1을 반환합니다.
    추후 OpenCV, 카메라 캡처, 모델 추론 등으로 교체하면 됩니다.
    '''

    # TODO: 실제 카메라 판정 로직으로 교체
    return config.RESP_PAPER_DETECTED


def is_arduino_command(cmd: str) -> bool:
    '''
    Arduino로 그대로 전달할 수 있는 명령인지 확인합니다.
    '''

    arduino_commands = {
        config.CMD_PING,
        config.CMD_GRIPPER_OPEN,
        config.CMD_GRIPPER_CLOSE,
        config.CMD_DC_MOTOR_RUN,
        config.CMD_ESTOP,
        config.CMD_MOTOR_STATUS,
        config.CMD_DOOR_STATUS,
    }

    return cmd in arduino_commands


def handle_command(cmd: str, ser: serial.Serial) -> str:
    '''
    UR5e에서 받은 명령을 처리합니다.
    '''

    cmd = clean_ur_command(cmd)

    print(f"[UR CMD] {cmd}")

    if not cmd:
        return config.RESP_ERR_UNKNOWN_CMD

    # PC 자체 처리 명령
    if cmd == config.CMD_CAMERA_RESULT:
        return handle_camera_command()

    # Arduino 전달 명령
    if is_arduino_command(cmd):
        return send_to_arduino(ser, cmd)

    return config.RESP_ERR_UNKNOWN_CMD


def run_server(ser: serial.Serial) -> None:
    '''
    TCP Socket 서버를 실행합니다.
    UR5e가 클라이언트로 접속합니다.
    '''

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((config.HOST, config.PORT))
        server.listen(1)

        print(f"[SERVER] Listening on {config.HOST}:{config.PORT}")

        while True:
            print("[SERVER] Waiting for UR connection...")

            try:
                conn, addr = server.accept()

            except OSError as exc:
                print(f"[SERVER] Accept error: {exc}")
                continue

            with conn:
                print(f"[SERVER] Connected by {addr}")

                while True:
                    try:
                        data = conn.recv(config.SOCKET_RECV_SIZE)

                        if not data:
                            print("[SERVER] Connection closed.")
                            break

                        cmd = data.decode("utf-8", errors="ignore")
                        response = handle_command(cmd, ser)

                        conn.sendall((response + "\n").encode("utf-8"))
                        print(f"[SERVER RESP] {response}")

                    except ConnectionResetError:
                        print("[SERVER] Connection reset by UR5e.")
                        break

                    except BrokenPipeError:
                        print("[SERVER] Broken pipe. UR5e connection already closed.")
                        break

                    except OSError as exc:
                        print(f"[SERVER] Socket error: {exc}")
                        break

                    except Exception as exc:
                        print(f"[SERVER] Unexpected error: {type(exc).__name__}: {exc}")
                        break


def main() -> None:
    list_serial_ports()

    try:
        with open_arduino() as ser:
            print(f"[Arduino] Connected on {config.ARDUINO_PORT}")
            run_server(ser)

    except serial.SerialException as exc:
        print(f"[Arduino] Serial open error: {exc}")

    except KeyboardInterrupt:
        print("\n[SERVER] Interrupted by user.")


if __name__ == "__main__":
    main()