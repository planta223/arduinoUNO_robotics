from __future__ import annotations

import argparse

try:
    import cv2
    import numpy as np
except ModuleNotFoundError:
    cv2 = None
    np = None


def create_aruco_detector(dict_name: str):
    if not hasattr(cv2, "aruco"):
        raise RuntimeError("OpenCV ArUco module not found. Install opencv-contrib-python.")

    dict_id = getattr(cv2.aruco, dict_name, None)
    if dict_id is None:
        raise ValueError(f"Unknown ArUco dictionary: {dict_name}")

    dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
    detector_params = cv2.aruco.DetectorParameters()

    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(dictionary, detector_params)
        return detector, dictionary, detector_params, True

    return None, dictionary, detector_params, False


def parse_backend(name: str):
    value = name.lower()
    if value == "auto":
        return None
    if value == "dshow":
        return cv2.CAP_DSHOW
    if value == "msmf":
        return cv2.CAP_MSMF
    raise ValueError(f"Unsupported backend: {name}")


def open_camera(camera_index: int, backend_name: str):
    backend = parse_backend(backend_name)
    if backend is None:
        cap = cv2.VideoCapture(camera_index)
    else:
        cap = cv2.VideoCapture(camera_index, backend)

    if not cap.isOpened():
        cap.release()
        raise RuntimeError(
            f"Failed to open camera index {camera_index} with backend '{backend_name}'. "
            "Try --backend dshow or a different --camera-index."
        )

    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        raise RuntimeError(
            f"Camera opened but no frames from index {camera_index} with backend '{backend_name}'. "
            "Try --backend dshow or a different --camera-index."
        )
    return cap


def detect_marker(gray: np.ndarray, aruco_setup, target_marker_id: int):
    detector, dictionary, params, is_new_api = aruco_setup
    if is_new_api:
        corners, ids, _ = detector.detectMarkers(gray)
    else:
        corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=params)

    marker_found = False
    if ids is not None and len(ids) > 0:
        marker_found = int(target_marker_id) in ids.flatten().tolist()

    return marker_found, corners, ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lid-only test using ArUco marker visibility")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index to open")
    parser.add_argument(
        "--aruco-dictionary",
        default="DICT_4X4_50",
        help="OpenCV ArUco dictionary name (example: DICT_4X4_50)",
    )
    parser.add_argument("--marker-id", type=int, default=0, help="Target ArUco marker ID")
    parser.add_argument(
        "--backend",
        choices=["auto", "dshow", "msmf"],
        default="auto",
        help="Camera backend. Use dshow on Windows when msmf cannot grab frames.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if cv2 is None or np is None:
        raise RuntimeError("Missing dependencies. Install with: pip install -r requirements.txt")

    aruco_setup = create_aruco_detector(args.aruco_dictionary)
    cap = open_camera(args.camera_index, args.backend)

    window_name = "Lid Test"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    last_lid_status = None

    try:
        while True:
            # LOGIC START: CAMERA INPUT -> STATUS DECISION -> STATUS OUTPUT
            # CAMERA INPUT: read the latest frame from the camera
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            # STATUS DECISION: detect the target ArUco marker and set lid status
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            marker_found, corners, ids = detect_marker(gray, aruco_setup, args.marker_id)
            lid_status = "LID_OPEN" if marker_found else "LID_CLOSED"

            if corners:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            cv2.putText(
                frame,
                f"LID: {lid_status}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "Keys: q=quit",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

            if lid_status != last_lid_status:
                # STATUS OUTPUT: print only when the lid status changes
                print(lid_status)
                last_lid_status = lid_status

            cv2.imshow(window_name, frame)
            # KEY INPUT: handle quit key
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
