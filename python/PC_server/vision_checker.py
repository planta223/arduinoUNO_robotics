# vision_checker.py

import cv2

import config
from vision_lid import create_aruco_detector, detect_marker, open_camera


class VisionChecker:
    """
    PC Vision 통합 wrapper.

    - check_vision_lid()
      ArUco marker 검출 기반 스캐너 뚜껑 open/close 판정

    - check_vision_align()
      추후 ROI/background diff 기반 종이 정렬 판정 연동 예정

    원칙:
    - 비전 내부 실패는 별도 ERR 응답으로 내보내지 않는다.
    - lid 판정 실패 시 LID_CLOSED 반환
    - paper align 판정 실패 또는 미구현 시 PAPER_NG 반환
    """

    def __init__(self):
        self.cap = None
        self.aruco_setup = None
        self.camera_ready = False

        self._init_camera_and_aruco()

    def _init_camera_and_aruco(self) -> None:
        """
        카메라와 ArUco detector를 초기화한다.

        초기화 실패 시 예외를 밖으로 던지지 않는다.
        그래야 카메라 문제로 main_server.py 전체가 죽지 않고,
        Arduino/UR5e 통신 테스트는 계속 가능하다.
        """

        try:
            self.aruco_setup = create_aruco_detector(config.ARUCO_DICTIONARY)
            self.cap = open_camera(config.CAMERA_INDEX, config.CAMERA_BACKEND)

            if config.CAMERA_FRAME_WIDTH is not None:
                self.cap.set(
                    cv2.CAP_PROP_FRAME_WIDTH,
                    int(config.CAMERA_FRAME_WIDTH),
                )

            if config.CAMERA_FRAME_HEIGHT is not None:
                self.cap.set(
                    cv2.CAP_PROP_FRAME_HEIGHT,
                    int(config.CAMERA_FRAME_HEIGHT),
                )

            self.camera_ready = True
            print("[Vision] Camera and ArUco detector initialized.")

        except Exception as exc:
            self.cap = None
            self.aruco_setup = None
            self.camera_ready = False

            print(f"[Vision] Init failed: {type(exc).__name__}: {exc}")
            print("[Vision] Vision commands will return fail-safe status.")

    def check_vision_lid(self) -> str:
        """
        ArUco marker visibility 기반 lid 상태 판정.

        반환:
        - LID_OPEN   : 목표 ArUco marker가 보임
        - LID_CLOSED : 목표 ArUco marker가 안 보임 또는 판정 실패
        """

        if not self.camera_ready or self.cap is None or self.aruco_setup is None:
            print("[Vision] Lid check failed: camera not ready. Return LID_CLOSED.")
            return config.RESP_LID_CLOSED

        try:
            ok, frame = self.cap.read()

            if not ok or frame is None:
                print("[Vision] Lid check failed: frame read failed. Return LID_CLOSED.")
                return config.RESP_LID_CLOSED

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            marker_found, _, _ = detect_marker(
                gray,
                self.aruco_setup,
                config.ARUCO_MARKER_ID,
            )

            if marker_found:
                return config.RESP_LID_OPEN

            return config.RESP_LID_CLOSED

        except Exception as exc:
            print(f"[Vision] Lid check exception: {type(exc).__name__}: {exc}")
            return config.RESP_LID_CLOSED

    def check_vision_align(self) -> str:
        """
        ROI/background diff 기반 종이 정렬 판정 연동 예정.

        현재는 main_server.py의 V PAPER 라우팅 테스트용 placeholder.
        추후 paper_align_check.py의 process_frame()과 result.change_ratios를 사용해
        PAPER_OK, PAPER_NOT_FOUND, PAPER_SHIFTED_*, PAPER_NG를 반환하도록 확장한다.
        """

        print("[Vision] Paper align check is not implemented yet. Return PAPER_NG.")
        return config.RESP_PAPER_NG

    def release(self) -> None:
        """
        서버 종료 시 카메라 자원 해제.
        """

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        self.camera_ready = False
        print("[Vision] Camera released.")