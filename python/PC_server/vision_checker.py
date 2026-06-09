# vision_checker.py

from collections import deque
from pathlib import Path

import cv2

import config
from vision_lid import create_aruco_detector, detect_marker, open_camera
from vision_paper_align import (
    load_config,
    load_background,
    process_frame,
)


class VisionChecker:
    """
    PC Vision 통합 wrapper.

    - check_vision_lid()
      ArUco marker 검출 기반 스캐너 뚜껑 open/close 판정

    - check_vision_align()
      ROI/background diff 기반 종이 위치·정렬 판정

    반환 원칙:
    - V LID 실패 시 LID_CLOSED
    - V PAPER 실패 시 PAPER_NG
    - V PAPER 정상 판정 시 PAPER_OK
    - 종이 없음 판정 시 PAPER_NOT_FOUND
    - 종이 위치 이탈 시 PAPER_SHIFTED_UP / DOWN / LEFT / RIGHT
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

            self.apply_camera_settings()
            self.warmup_camera()

            self.camera_ready = True
            print("[Vision] Camera and ArUco detector initialized.")

        except Exception as exc:
            self.cap = None
            self.aruco_setup = None
            self.camera_ready = False

            print(f"[Vision] Init failed: {type(exc).__name__}: {exc}")
            print("[Vision] Vision commands will return fail-safe status.")

    def _safe_set_camera_property(self, prop_name: str, value) -> None:
        """
        OpenCV 카메라 속성을 안전하게 설정한다.
        카메라/드라이버에 따라 일부 속성은 무시될 수 있다.
        """

        if self.cap is None:
            return

        prop_id = getattr(cv2, prop_name, None)

        if prop_id is None:
            print(f"[Vision] Camera property not found in cv2: {prop_name}")
            return

        ok = self.cap.set(prop_id, value)
        actual = self.cap.get(prop_id)

        print(
            "[Vision] Camera set "
            f"{prop_name}: requested={value}, actual={actual}, ok={ok}"
        )

    def apply_camera_settings(self) -> None:
        """
        카메라 노출/게인만 강제로 적용한다.

        적용 대상:
        - CAP_PROP_AUTO_EXPOSURE
        - CAP_PROP_EXPOSURE
        - CAP_PROP_GAIN

        건드리지 않는 항목:
        - brightness
        - contrast
        - white balance
        - backlight compensation

        주의:
        - CAP_PROP_EXPOSURE, CAP_PROP_GAIN의 실제 의미는 카메라/드라이버마다 다르다.
        - Logitech C270 + Windows DirectShow 기준으로 실제 화면을 보며 튜닝해야 한다.
        """

        if self.cap is None:
            return

        print("[Vision] Applying exposure/gain camera settings.")

        self._safe_set_camera_property(
            "CAP_PROP_AUTO_EXPOSURE",
            getattr(config, "CAMERA_AUTO_EXPOSURE", 0),
        )

        self._safe_set_camera_property(
            "CAP_PROP_EXPOSURE",
            getattr(config, "CAMERA_EXPOSURE", -6),
        )

        self._safe_set_camera_property(
            "CAP_PROP_GAIN",
            getattr(config, "CAMERA_GAIN", 0),
        )

    def warmup_camera(self) -> None:
        """
        설정 적용 직후 안정화되지 않은 프레임을 버린다.
        """

        if self.cap is None:
            return

        warmup_frames = int(getattr(config, "CAMERA_WARMUP_FRAMES", 30))

        print(f"[Vision] Camera warmup: discard {warmup_frames} frames.")

        for _ in range(warmup_frames):
            self.cap.read()

    def _init_paper_align(self) -> None:
        """
        paper align용 config/background를 로드한다.
        """

        try:
            config_path = Path(config.PAPER_CONFIG_PATH)
            background_path = Path(config.PAPER_BACKGROUND_PATH)

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

    def _read_latest_frame(self, flush_count: int | None = None):
        """
        오래된 카메라 버퍼 프레임을 버리고 최신 프레임에 가까운 이미지를 읽는다.
        """

        if self.cap is None:
            return False, None

        if flush_count is None:
            flush_count = int(getattr(config, "CAMERA_FLUSH_FRAMES", 3))

        frame = None
        ok = False

        for _ in range(max(1, flush_count)):
            ok, frame = self.cap.read()

        return ok, frame

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
            ok, frame = self._read_latest_frame()

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

    def _classify_paper_direction(self, result) -> str:
        """
        paper align 결과를 UR5e 응답 문자열로 변환한다.

        반환:
        - PAPER_OK
        - PAPER_NOT_FOUND
        - PAPER_SHIFTED_UP
        - PAPER_SHIFTED_DOWN
        - PAPER_SHIFTED_LEFT
        - PAPER_SHIFTED_RIGHT
        - PAPER_NG
        """

        status = result.raw_paper_status
        ratios = result.change_ratios

        if status == "PAPER_OK":
            return config.RESP_PAPER_OK

        if status == "PAPER_NOT_FOUND":
            return config.RESP_PAPER_NOT_FOUND

        if status != "PAPER_NG":
            return config.RESP_PAPER_NG

        if self.paper_cfg is None:
            return config.RESP_PAPER_NG

        excess = {
            "UP": ratios.get("OUT_TOP", 0.0) - self.paper_cfg.max_out_top_change_ratio,
            "LEFT": ratios.get("OUT_LEFT", 0.0) - self.paper_cfg.max_out_left_change_ratio,
            "RIGHT": ratios.get("OUT_RIGHT", 0.0) - self.paper_cfg.max_out_right_change_ratio,
            "DOWN": ratios.get("OUT_BOTTOM", 0.0) - self.paper_cfg.max_out_bottom_change_ratio,
        }

        exceeded = {
            direction: value
            for direction, value in excess.items()
            if value > 0.0
        }

        print(f"[Vision] Paper excess: {excess}")

        if not exceeded:
            return config.RESP_PAPER_NG

        main_direction = max(exceeded, key=exceeded.get)

        if main_direction == "UP":
            return config.RESP_PAPER_SHIFTED_UP

        if main_direction == "DOWN":
            return config.RESP_PAPER_SHIFTED_DOWN

        if main_direction == "LEFT":
            return config.RESP_PAPER_SHIFTED_LEFT

        if main_direction == "RIGHT":
            return config.RESP_PAPER_SHIFTED_RIGHT

        return config.RESP_PAPER_NG

    def check_vision_align(self) -> str:
        """
        ROI/background diff 기반 종이 정렬 판정.

        반환:
        - PAPER_OK
        - PAPER_NOT_FOUND
        - PAPER_SHIFTED_UP
        - PAPER_SHIFTED_DOWN
        - PAPER_SHIFTED_LEFT
        - PAPER_SHIFTED_RIGHT
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
            ok, frame = self._read_latest_frame()

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

            response = self._classify_paper_direction(result)

            print(
                "[Vision] Paper result: "
                f"stable={result.paper_status}, "
                f"raw={result.raw_paper_status}, "
                f"ratios={result.change_ratios}, "
                f"response={response}"
            )

            return response

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