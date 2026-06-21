# vision_checker.py

from collections import deque
from pathlib import Path

import cv2

import config
from camera_settings import (
    apply_camera_settings,
    maybe_print_camera_settings,
    warmup_camera,
)
from vision_lid import create_aruco_detector, detect_marker, open_camera
from vision_paper_align import (
    load_config,
    load_background,
    draw_overlay,
    process_frame,
)


def server_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path

    return Path(__file__).resolve().parent / path


class VisionChecker:
    """
    PC Vision 통합 wrapper.

    - check_vision_lid()
      ArUco marker 검출 기반 스캐너 뚜껑 open/close 판정

    - check_vision_align()
      ROI/background diff 기반 종이 위치·정렬 판정

    원칙:
    - 비전 내부 실패는 별도 ERR 응답으로 내보내지 않는다.
    - lid 판정 실패 시 LID_CLOSED 반환
    - paper align 판정 실패 시 PAPER_NG 반환
    """

    def __init__(self):
        self.cap = None
        self.aruco_setup = None
        self.camera_ready = False

        self.paper_cfg = None
        self.paper_background = None
        self.paper_history = None
        self.paper_last_state = None

        self._init_camera_and_aruco()
        self._init_paper_align()

    def _init_camera_and_aruco(self) -> None:
        """
        카메라와 ArUco detector를 초기화한다.
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

            apply_camera_settings(self.cap)
            warmup_camera(self.cap)
            maybe_print_camera_settings(self.cap)

            self.camera_ready = True
            print("[Vision] Camera and ArUco detector initialized.")

        except Exception as exc:
            self.cap = None
            self.aruco_setup = None
            self.camera_ready = False

            print(f"[Vision] Init failed: {type(exc).__name__}: {exc}")
            print("[Vision] Vision commands will return fail-safe status.")

    def _init_paper_align(self) -> None:
        """
        paper align용 config/background를 로드한다.
        """

        try:
            config_path = server_path(config.PAPER_CONFIG_PATH)
            background_path = server_path(config.PAPER_BACKGROUND_PATH)

            self.paper_cfg = load_config(config_path)
            self.paper_background = load_background(background_path)

            self.paper_history = deque(maxlen=self.paper_cfg.vote_window)
            self.paper_last_state = {
                "background": None,
                "calibration": None,
                "paper": None,
            }

            if self.paper_background is None:
                print("[Vision] Paper background missing. V PAPER will return PAPER_NG.")
            elif not self.paper_cfg.calibration.is_calibrated:
                print("[Vision] Paper calibration missing. V PAPER will return PAPER_NG.")
            else:
                print("[Vision] Paper align config and background loaded.")

        except Exception as exc:
            self.paper_cfg = None
            self.paper_background = None
            self.paper_history = None
            self.paper_last_state = None

            print(f"[Vision] Paper align init failed: {type(exc).__name__}: {exc}")
            print("[Vision] V PAPER will return PAPER_NG.")

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
            frame = None
            ok = False

            for _ in range(3):
                ok, frame = self.cap.read()

            if not ok or frame is None:
                print("[Vision] Lid check failed: frame read failed. Return LID_CLOSED.")
                return config.RESP_LID_CLOSED

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            marker_found, _, ids = detect_marker(
                gray,
                self.aruco_setup,
                config.ARUCO_MARKER_ID,
            )

            if ids is None:
                print("[Vision] ArUco ids: None")
            else:
                print(f"[Vision] ArUco ids: {ids.flatten().tolist()}")

            if marker_found:
                return config.RESP_LID_OPEN

            return config.RESP_LID_CLOSED

        except Exception as exc:
            print(f"[Vision] Lid check exception: {type(exc).__name__}: {exc}")
            return config.RESP_LID_CLOSED

    def classify_paper_response(self, result) -> str:
        raw_status = getattr(result, "raw_paper_status", None)

        if raw_status == "PAPER_NOT_FOUND":
            return config.RESP_PAPER_NOT_FOUND

        if raw_status == "PAPER_OK":
            return config.RESP_PAPER_OK

        if raw_status == "PAPER_NG":
            change_ratios = getattr(result, "change_ratios", {}) or {}

            if change_ratios.get("OUT_TOP", 0) > self.paper_cfg.max_out_top_change_ratio:
                return config.RESP_PAPER_SHIFTED_UP

            if change_ratios.get("OUT_LEFT", 0) > self.paper_cfg.max_out_left_change_ratio:
                return config.RESP_PAPER_SHIFTED_LEFT

            if change_ratios.get("OUT_RIGHT", 0) > self.paper_cfg.max_out_right_change_ratio:
                return config.RESP_PAPER_SHIFTED_RIGHT

            if change_ratios.get("OUT_BOTTOM", 0) > self.paper_cfg.max_out_bottom_change_ratio:
                return config.RESP_PAPER_SHIFTED_DOWN

        return config.RESP_PAPER_NG

    def check_vision_align(self) -> str:
        """
        ROI/background diff 기반 종이 정렬 판정.

        반환:
        - PAPER_OK
        - PAPER_NOT_FOUND
        - PAPER_NG
        """

        if not self.camera_ready or self.cap is None:
            print("[Vision] Paper check failed: camera not ready. Return PAPER_NG.")
            return config.RESP_PAPER_NG

        if (
            self.paper_cfg is None
            or self.paper_background is None
            or self.paper_history is None
            or self.paper_last_state is None
        ):
            print("[Vision] Paper check failed: paper align not ready. Return PAPER_NG.")
            return config.RESP_PAPER_NG

        try:
            frame = None
            ok = False

            for _ in range(3):
                ok, frame = self.cap.read()

            if not ok or frame is None:
                print("[Vision] Paper check failed: frame read failed. Return PAPER_NG.")
                return config.RESP_PAPER_NG

            result = process_frame(
                frame=frame,
                background=self.paper_background,
                cfg=self.paper_cfg,
                history=self.paper_history,
                last_state=self.paper_last_state,
            )

            overlay = draw_overlay(frame, result, self.paper_cfg)
            cv2.imshow("Paper Align Debug", overlay)
            cv2.waitKey(1)

            print(
                "[Vision] Paper result: "
                f"stable={result.paper_status}, "
                f"raw={result.raw_paper_status}, "
                f"ratios={result.change_ratios}"
            )

            return self.classify_paper_response(result)

        except Exception as exc:
            print(f"[Vision] Paper check exception: {type(exc).__name__}: {exc}")
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
