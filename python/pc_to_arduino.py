import time
import serial
from serial.tools import list_ports


# ============================================================
# Serial 설정
# ============================================================
BAUDRATE = 9600
TIMEOUT_S = 1.0
ARDUINO_RESET_WAIT_S = 2.0


# ============================================================
# Arduino 명령 문자열
# Arduino config.h / protocol.cpp 기준
# ============================================================
CMD_PING = "PING"

CMD_GRIPPER_OPEN = "G OPEN"
CMD_GRIPPER_CLOSE = "G CLOSE"

CMD_DC_MOTOR_RUN = "D RUN"

CMD_ESTOP = "ESTOP"

CMD_MOTOR_STATUS = "MOTOR STATUS"
CMD_DOOR_STATUS = "DOOR STATUS"


def list_serial_ports() -> None:
    ports = list(list_ports.comports())

    if not ports:
        print("[PC] No serial ports found.")
        return

    print("[PC] Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")


def open_serial(port: str) -> serial.Serial:
    """
    Arduino Uno는 Serial 포트가 열릴 때 리셋될 수 있다.
    따라서 연결 후 일정 시간 대기하고, READY 같은 부팅 메시지를 제거한다.
    """

    ser = serial.Serial(
        port=port,
        baudrate=BAUDRATE,
        timeout=TIMEOUT_S,
    )

    time.sleep(ARDUINO_RESET_WAIT_S)
    clear_startup_messages(ser)

    return ser


def clear_startup_messages(ser: serial.Serial) -> None:
    """
    Arduino 부팅 직후 출력되는 READY 등의 메시지를 읽어서 제거한다.
    """

    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if line:
            print(f"[Arduino startup] {line}")


def send_command(ser: serial.Serial, cmd: str) -> str:
    """
    Arduino에 한 줄 명령을 보내고, 한 줄 응답을 받는다.
    모든 명령은 \\n으로 종료한다.
    """

    cmd = cmd.strip()

    if not cmd:
        return ""

    print(f"[PC -> Arduino] {cmd}")

    try:
        # 이전 명령의 잔여 응답 제거
        ser.reset_input_buffer()

        ser.write((cmd + "\n").encode("utf-8"))
        ser.flush()

        response = ser.readline().decode("utf-8", errors="ignore").strip()

    except serial.SerialException as exc:
        print(f"[PC] Serial error: {exc}")
        return "ERR SERIAL"

    except OSError as exc:
        print(f"[PC] OS error: {exc}")
        return "ERR SERIAL"

    if not response:
        print("[Arduino -> PC] ERR TIMEOUT")
        return "ERR TIMEOUT"

    print(f"[Arduino -> PC] {response}")
    return response


def gripper_menu(ser: serial.Serial) -> None:
    while True:
        print("\n[Gripper Menu]")
        print("1. Open gripper")
        print("2. Close gripper")
        print("3. Motor status")
        print("q. Back")

        sel = input("Select> ").strip().lower()

        if sel == "1":
            send_command(ser, CMD_GRIPPER_OPEN)

        elif sel == "2":
            send_command(ser, CMD_GRIPPER_CLOSE)

        elif sel == "3":
            send_command(ser, CMD_MOTOR_STATUS)

        elif sel == "q":
            break

        else:
            print("[PC] Invalid selection.")


def dc_motor_menu(ser: serial.Serial) -> None:
    while True:
        print("\n[DC Motor Menu]")
        print("1. Run DC motor")
        print("2. Motor status")
        print("3. Emergency stop")
        print("q. Back")

        sel = input("Select> ").strip().lower()

        if sel == "1":
            send_command(ser, CMD_DC_MOTOR_RUN)

        elif sel == "2":
            send_command(ser, CMD_MOTOR_STATUS)

        elif sel == "3":
            send_command(ser, CMD_ESTOP)

        elif sel == "q":
            break

        else:
            print("[PC] Invalid selection.")


def sensor_menu(ser: serial.Serial) -> None:
    while True:
        print("\n[Sensor Menu]")
        print("1. Door status")
        print("q. Back")

        sel = input("Select> ").strip().lower()

        if sel == "1":
            send_command(ser, CMD_DOOR_STATUS)

        elif sel == "q":
            break

        else:
            print("[PC] Invalid selection.")


def raw_command_menu(ser: serial.Serial) -> None:
    print("\n[Raw Command Menu]")
    print("Available examples:")
    print(f"  {CMD_PING}")
    print(f"  {CMD_GRIPPER_OPEN}")
    print(f"  {CMD_GRIPPER_CLOSE}")
    print(f"  {CMD_DC_MOTOR_RUN}")
    print(f"  {CMD_MOTOR_STATUS}")
    print(f"  {CMD_DOOR_STATUS}")
    print(f"  {CMD_ESTOP}")
    print("q: back")

    while True:
        cmd = input("RAW> ").strip()

        if cmd.lower() == "q":
            break

        if not cmd:
            continue

        send_command(ser, cmd)


def main_menu(ser: serial.Serial) -> None:
    while True:
        print("\n=== PC to Arduino Test ===")
        print("1. Ping")
        print("2. Gripper")
        print("3. DC motor")
        print("4. Door sensor")
        print("5. Motor status")
        print("6. Emergency stop")
        print("7. Raw command")
        print("q. Quit")

        sel = input("Select> ").strip().lower()

        if sel == "1":
            send_command(ser, CMD_PING)

        elif sel == "2":
            gripper_menu(ser)

        elif sel == "3":
            dc_motor_menu(ser)

        elif sel == "4":
            sensor_menu(ser)

        elif sel == "5":
            send_command(ser, CMD_MOTOR_STATUS)

        elif sel == "6":
            send_command(ser, CMD_ESTOP)

        elif sel == "7":
            raw_command_menu(ser)

        elif sel == "q":
            send_command(ser, CMD_ESTOP)
            break

        else:
            print("[PC] Invalid selection.")


def main() -> None:
    list_serial_ports()

    port = input("\nSerial port ex) COM14: ").strip()

    if not port:
        print("[PC] Serial port is required.")
        return

    try:
        with open_serial(port) as ser:
            print(f"[PC] Connected to {port}")
            main_menu(ser)

    except serial.SerialException as exc:
        print(f"[PC] Serial open error: {exc}")

    except KeyboardInterrupt:
        print("\n[PC] Interrupted by user.")


if __name__ == "__main__":
    main()