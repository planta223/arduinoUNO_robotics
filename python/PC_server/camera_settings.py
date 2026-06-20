import cv2

import config


def _camera_settings():
    return [
        ("AUTO_EXPOSURE", cv2.CAP_PROP_AUTO_EXPOSURE, config.CAMERA_AUTO_EXPOSURE),
        ("EXPOSURE", cv2.CAP_PROP_EXPOSURE, config.CAMERA_EXPOSURE),
        ("GAIN", cv2.CAP_PROP_GAIN, config.CAMERA_GAIN),
        ("BRIGHTNESS", cv2.CAP_PROP_BRIGHTNESS, config.CAMERA_BRIGHTNESS),
        ("CONTRAST", cv2.CAP_PROP_CONTRAST, config.CAMERA_CONTRAST),
        ("AUTO_WB", cv2.CAP_PROP_AUTO_WB, config.CAMERA_AUTO_WB),
        ("WB_TEMPERATURE", cv2.CAP_PROP_WB_TEMPERATURE, config.CAMERA_WB_TEMPERATURE),
        ("BACKLIGHT", cv2.CAP_PROP_BACKLIGHT, config.CAMERA_BACKLIGHT),
    ]


def apply_camera_settings(cap):
    for name, prop, value in _camera_settings():
        ok = cap.set(prop, value)
        if not ok:
            print(f"[Camera] Warning: failed to set {name}={value}")


def warmup_camera(cap):
    for _ in range(config.CAMERA_WARMUP_FRAMES):
        cap.read()


def maybe_print_camera_settings(cap):
    print("[Camera] Reported camera settings (backend-dependent):")
    for name, prop, _ in _camera_settings():
        print(f"[Camera] {name}={cap.get(prop)}")
