import time
import serial
from serial.tools import list_ports


BAUDRATE = 9600
TIMEOUT_S = 1.0


def list_serial_ports() -> None:
    ports = list(list_ports.comports())

    if not ports:
        print("No serial ports found.")
        return

    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")


def open_serial(port: str) -> serial.Serial:
    ser = serial.Serial(
        port=port,
        baudrate=BAUDRATE,
        timeout=TIMEOUT_S,
    )

    # Arduino Uno는 Serial 연결 시 리셋될 수 있음
    time.sleep(2.0)

    clear_startup_messages(ser)
    return ser


def clear_startup_messages(ser: serial.Serial) -> None:
    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if line:
            print(f"[Arduino] {line}")


def send_command(ser: serial.Serial, cmd: str) -> list[str]:
    ser.write((cmd + "\n").encode("utf-8"))
    ser.flush()

    time.sleep(0.05)

    responses = []
    while ser.in_waiting > 0:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if line:
            responses.append(line)

    for line in responses:
        print(f"[Arduino] {line}")

    return responses


def dc_motor_mode(ser: serial.Serial) -> None:
    print("\n[DC Motor Mode]")
    print("Input PWM: -255 ~ 255")
    print("Examples: 120, -120, 0")
    print("q: back")

    while True:
        user_input = input("DC PWM> ").strip()

        if user_input.lower() == "q":
            send_command(ser, "D 0")
            break

        try:
            pwm = int(user_input)
        except ValueError:
            print("Invalid PWM.")
            continue

        send_command(ser, f"D {pwm}")


def gripper_mode(ser: serial.Serial) -> None:
    print("\n[Gripper Servo Mode]")
    print("Commands:")
    print("  open")
    print("  close")
    print("  busy")
    print("  angle")
    print("  <0~180>")
    print("  q")

    while True:
        user_input = input("GRIPPER> ").strip()

        if user_input.lower() == "q":
            break

        if user_input.lower() == "open":
            send_command(ser, "G OPEN")
        elif user_input.lower() == "close":
            send_command(ser, "G CLOSE")
        elif user_input.lower() == "busy":
            send_command(ser, "G BUSY")
        elif user_input.lower() == "angle":
            send_command(ser, "G ANGLE")
        else:
            try:
                angle = int(user_input)
            except ValueError:
                print("Invalid gripper command.")
                continue

            send_command(ser, f"G {angle}")


def sensor_mode(ser: serial.Serial) -> None:
    print("\n[Sensor Mode]")
    print("Commands:")
    print("  door")
    print("  q")

    while True:
        user_input = input("SENSOR> ").strip()

        if user_input.lower() == "q":
            break

        if user_input.lower() == "door":
            send_command(ser, "S DOOR")
        else:
            print("Invalid sensor command.")


def raw_command_mode(ser: serial.Serial) -> None:
    print("\n[Raw Command Mode]")
    print("Examples:")
    print("  D 120")
    print("  G OPEN")
    print("  G CLOSE")
    print("  G 90")
    print("  G BUSY")
    print("  G ANGLE")
    print("  S DOOR")
    print("  STOP")
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
        print("\n=== Robot Control ===")
        print("1. DC motor mode")
        print("2. Gripper servo mode")
        print("3. Sensor mode")
        print("4. Raw command mode")
        print("5. Stop all")
        print("q. Quit")

        mode = input("Select> ").strip()

        if mode == "1":
            dc_motor_mode(ser)
        elif mode == "2":
            gripper_mode(ser)
        elif mode == "3":
            sensor_mode(ser)
        elif mode == "4":
            raw_command_mode(ser)
        elif mode == "5":
            send_command(ser, "STOP")
        elif mode.lower() == "q":
            send_command(ser, "STOP")
            break
        else:
            print("Invalid menu selection.")


def main() -> None:
    list_serial_ports()

    port = input("\nSerial port ex) COM12: ").strip()

    if not port:
        print("Serial port is required.")
        return

    try:
        with open_serial(port) as ser:
            print(f"Connected to {port}")
            main_menu(ser)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")


if __name__ == "__main__":
    main()