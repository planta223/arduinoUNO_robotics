'''
이 코드는 Windows PC에서 실행됩니다.
PC가 서버, UR5e가 클라이언트입니다.

UR5e가 PolyScope에서 다음처럼 접속합니다.
socket_open("192.168.0.10", 5000)
socket_send_string("PING")

그러면 Python 서버가 PING을 받고 OK를 돌려주는 구조입니다.
'''

import socket

HOST = "0.0.0.0"
PORT = 5000


# 현재 handle_command는 미완성 코드이다. (더미 응답)
def handle_command(cmd: str) -> str:
    cmd = cmd.strip()        # 공백, 줄바꿈 제거
    print(f"[UR CMD] {cmd}") # 현재 실행 중인 명령어 출력

    if cmd == "PING":        # 연결 확인용 PING
        return "OK"

    if cmd == "G OPEN":      # 그리퍼 OPEN 요청
        return "OK"

    if cmd == "G CLOSE":     # 그리퍼 CLOSE 요청
        return "OK"

    if cmd == "D STOP":      # DC 모터 STOP 요청
        return "OK"

    if cmd == "D RUN":       # DC 모터 RUN 요청
        return "OK"

    if cmd == "S DOOR":      # 도어센서 값 요청
        return "DOOR 1"

    if cmd == "V CAMERA":    # 카메라 결과 요청
        return "PAPER 1"

    return "ERR UNKNOWN_CMD" # 그 외 명령은 에러 응답


def main() -> None:
    print(f"[SERVER] Listening on 0.0.0.0:{PORT}") # 서버 가동 시작 출력

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server: #IPv4 TCP 소켓 객체 생성
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1) # 소켓을 클라이언트의 연결 요청을 받아들일 수 있는 대기상태로 전환

        while True:
            print("[SERVER] Waiting for UR connection...") # UR 연결 대기 출력
            conn, addr = server.accept() # UR 연결 대기

            with conn:
                print(f"[SERVER] Connected by {addr}") # 연결에 성공한 클라이언트의 네트워크 주소 출력

                # 무한 루프
                while True:
                    data = conn.recv(1024)

                    if not data:
                        print("[SERVER] Connection closed.")  # 통신 정상 종료시 연결 종료 출력
                        break

                    cmd = data.decode("utf-8", errors="ignore").strip() #이진 데이터를 UTF-8 문자열로 변환(오류는 무시, 공백및개행 제거)
                    response = handle_command(cmd) # handle_command 함수 호출

                    conn.sendall((response + "\n").encode("utf-8")) # 개행문자 추가후 UTF-8 인코딩하여 전송
                    print(f"[SERVER RESP] {response}") # 응답 출력


if __name__ == "__main__":
    main()