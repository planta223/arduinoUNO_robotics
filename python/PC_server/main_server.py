'''
이 코드는 Windows PC에서 실행됩니다.
PC가 서버, UR5e가 클라이언트입니다.

UR5e가 PolyScope에서 다음처럼 접속합니다.
socket_open("192.168.0.10", 5000)
socket_send_string("PING")

그러면 Python 서버가 PING을 받고 OK를 돌려주는 구조입니다.

추가 구조:
UR5e가 G OPEN, G CLOSE, D STOP, D RUN, S DOOR 명령을 보내면
Python 서버가 Arduino로 해당 명령을 Serial 전송하고,
Arduino 응답을 다시 UR5e로 전달합니다.
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
    Arduino Uno는 Serial 연결 시 리셋될 수 있으므로 대기합니다.
    '''

    ser = serial.Serial(
        port=config.ARDUINO_PORT,
        baudrate=config.ARDUINO_BAUDRATE,
        timeout=config.ARDUINO_TIMEOUT_S,
    )

    # Arduino Uno는 Serial 연결 시 리셋될 수 있음
    time.sleep(config.ARDUINO_RESET_WAIT_S)

    # Arduino 부팅 메시지 제거
    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if line:
            print(f"[Arduino startup] {line}")

    return ser


def send_to_arduino(ser: serial.Serial, cmd: str) -> str:
    '''
    UR5e에서 받은 명령을 Arduino로 전달하고,
    Arduino 응답을 한 줄 읽어서 반환합니다.
    '''

    print(f"[PC -> Arduino] {cmd}")

    try:
        # 이전 명령의 잔여 응답이 남아 있으면 제거
        ser.reset_input_buffer()

        ser.write((cmd + "\n").encode("utf-8"))
        ser.flush()

        response = ser.readline().decode("utf-8", errors="ignore").strip()

    except serial.SerialException as exc:
        print(f"[Arduino Serial Error] {exc}")
        return "ERR ARDUINO_SERIAL"

    except OSError as exc:
        print(f"[Arduino OS Error] {exc}")
        return "ERR ARDUINO_SERIAL"

    if not response:
        print(f"[Arduino -> PC] {config.RESP_ERR_ARDUINO_TIMEOUT}")
        return config.RESP_ERR_ARDUINO_TIMEOUT

    print(f"[Arduino -> PC] {response}")
    return response


def normalize_arduino_response(arduino_response: str) -> str:
    '''
    Arduino 응답을 UR5e가 처리하기 쉬운 형태로 정리합니다.

    예:
    Arduino: OK G OPEN  -> UR5e: OK
    Arduino: OK D 120   -> UR5e: OK
    Arduino: DOOR 1     -> UR5e: DOOR 1
    '''

    if arduino_response.startswith(config.RESP_OK):
        return config.RESP_OK

    if arduino_response.startswith("DOOR"):
        return arduino_response

    if arduino_response.startswith("ERR"):
        return arduino_response

    return arduino_response


def handle_command(cmd: str, ser: serial.Serial) -> str:
    cmd = cmd.strip()

    # URScript에서 실수로 "\n" 문자열 자체를 보낸 경우 방어
    cmd = cmd.replace("\\n", "")
    cmd = cmd.replace("\\r", "")

    print(f"[UR CMD] {cmd}")

    if cmd == config.CMD_PING:
        return config.RESP_OK

    if cmd == config.CMD_GRIPPER_OPEN:
        arduino_response = send_to_arduino(ser, config.ARDUINO_GRIPPER_OPEN_CMD)
        return normalize_arduino_response(arduino_response)

    if cmd == config.CMD_GRIPPER_CLOSE:
        arduino_response = send_to_arduino(ser, config.ARDUINO_GRIPPER_CLOSE_CMD)
        return normalize_arduino_response(arduino_response)

    if cmd == config.CMD_DC_MOTOR_STOP:
        arduino_response = send_to_arduino(ser, config.ARDUINO_DC_MOTOR_STOP_CMD)
        return normalize_arduino_response(arduino_response)

    if cmd == config.CMD_DC_MOTOR_RUN:
        arduino_response = send_to_arduino(ser, config.ARDUINO_DC_MOTOR_RUN_CMD)
        return normalize_arduino_response(arduino_response)

    if cmd == config.CMD_SENSOR_DOOR:
        arduino_response = send_to_arduino(ser, config.ARDUINO_SENSOR_DOOR_CMD)
        return normalize_arduino_response(arduino_response)

    if cmd == config.CMD_CAMERA_RESULT:
        # TODO: 실제 카메라 판정 로직으로 교체 필요
        return config.RESP_PAPER_DETECTED

    return config.RESP_ERR_UNKNOWN_CMD


def main() -> None:
    print(f"[SERVER] Listening on {config.HOST}:{config.PORT}")

    list_serial_ports()

    try:
        with open_arduino() as ser:
            print(f"[Arduino] Connected on {config.ARDUINO_PORT}")

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((config.HOST, config.PORT))
                server.listen(1)

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

                                cmd = data.decode("utf-8", errors="ignore").strip()
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

    except serial.SerialException as exc:
        print(f"[Arduino] Serial open error: {exc}")

    except KeyboardInterrupt:
        print("\n[SERVER] Interrupted by user.")


if __name__ == "__main__":
    main()