from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportMissingTypeArgument=false, reportMissingParameterType=false, reportUnknownParameterType=false, reportDeprecated=false, reportUnusedCallResult=false, reportUnnecessaryComparison=false, reportOptionalMemberAccess=false, reportCallIssue=false

import argparse
import json
import platform
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import cv2
    import numpy as np
else:
    try:
        import cv2
        import numpy as np
    except ModuleNotFoundError:
        cv2 = None
        np = None

Point = tuple[float, float]
Polygon = list[Point]

ROI_ORDER = (
    "PRESENCE",
    "ALIGN_IN",
    "OUT_TOP",
    "OUT_LEFT",
    "OUT_RIGHT",
    "OUT_BOTTOM",
)


@dataclass
class ManualCalibration:
    presence_roi: Polygon = field(default_factory=list)
    align_in_roi: Polygon = field(default_factory=list)
    out_top_roi: Polygon = field(default_factory=list)
    out_left_roi: Polygon = field(default_factory=list)
    out_right_roi: Polygon = field(default_factory=list)
    out_bottom_roi: Polygon = field(default_factory=list)

    @property
    def is_calibrated(self) -> bool:
        return all(
            len(roi) == 4
            for roi in (
                self.presence_roi,
                self.align_in_roi,
                self.out_top_roi,
                self.out_left_roi,
                self.out_right_roi,
                self.out_bottom_roi,
            )
        )


@dataclass
class AppConfig:
    camera_index: int = 0
    frame_width: Optional[int] = 1280
    frame_height: Optional[int] = 720
    backend: str = "dshow" if platform.system().lower() == "windows" else "auto"

    pixel_difference_threshold: int = 18
    min_presence_change_ratio: float = 0.10
    min_align_in_change_ratio: float = 0.90
    max_out_top_change_ratio: float = 0.08
    max_out_left_change_ratio: float = 0.08
    max_out_right_change_ratio: float = 0.08
    max_out_bottom_change_ratio: float = 0.08
    out_difference_mode: str = "bright_only"

    alignment_enabled: bool = True
    alignment_max_shift_px: float = 12.0
    alignment_min_response: float = 0.10
    alignment_downscale: float = 0.5

    vote_window: int = 10
    vote_required: int = 7

    magnifier_size: int = 9
    magnifier_zoom: int = 12

    calibration: ManualCalibration = field(default_factory=ManualCalibration)


@dataclass
class FrameResult:
    background_status: str
    calibration_status: str
    raw_paper_status: str
    paper_status: str
    polygons: dict[str, Any] = field(default_factory=dict)
    change_ratios: dict[str, float] = field(default_factory=dict)
    alignment: dict[str, Any] = field(default_factory=dict)


def point_to_dict(point: Point) -> dict[str, float]:
    return {"x": float(point[0]), "y": float(point[1])}


def point_from_dict(data: dict[str, Any]) -> Point:
    return float(data.get("x", 0.0)), float(data.get("y", 0.0))


def polygon_to_dict(points: Polygon) -> list[dict[str, float]]:
    return [point_to_dict(point) for point in points]


def polygon_from_dict(data: object) -> Polygon:
    if not isinstance(data, list):
        return []
    points = [point_from_dict(item) for item in data[:4] if isinstance(item, dict)]
    return points if len(points) == 4 else []


def optional_int(value, default: Optional[int]) -> Optional[int]:
    return default if value is None else int(value)


def default_background_path(config_path: Path) -> Path:
    return config_path.with_name(f"{config_path.stem}_background.png")


def to_config_dict(cfg: AppConfig) -> dict[str, object]:
    return {
        "camera_index": cfg.camera_index,
        "frame_width": cfg.frame_width,
        "frame_height": cfg.frame_height,
        "backend": cfg.backend,
        "pixel_difference_threshold": cfg.pixel_difference_threshold,
        "min_presence_change_ratio": cfg.min_presence_change_ratio,
        "min_align_in_change_ratio": cfg.min_align_in_change_ratio,
        "max_out_top_change_ratio": cfg.max_out_top_change_ratio,
        "max_out_left_change_ratio": cfg.max_out_left_change_ratio,
        "max_out_right_change_ratio": cfg.max_out_right_change_ratio,
        "max_out_bottom_change_ratio": cfg.max_out_bottom_change_ratio,
        "out_difference_mode": cfg.out_difference_mode,
        "alignment_enabled": cfg.alignment_enabled,
        "alignment_max_shift_px": cfg.alignment_max_shift_px,
        "alignment_min_response": cfg.alignment_min_response,
        "alignment_downscale": cfg.alignment_downscale,
        "vote_window": cfg.vote_window,
        "vote_required": cfg.vote_required,
        "magnifier_size": cfg.magnifier_size,
        "magnifier_zoom": cfg.magnifier_zoom,
        "calibration": {
            "presence_roi": polygon_to_dict(cfg.calibration.presence_roi),
            "align_in_roi": polygon_to_dict(cfg.calibration.align_in_roi),
            "out_top_roi": polygon_to_dict(cfg.calibration.out_top_roi),
            "out_left_roi": polygon_to_dict(cfg.calibration.out_left_roi),
            "out_right_roi": polygon_to_dict(cfg.calibration.out_right_roi),
            "out_bottom_roi": polygon_to_dict(cfg.calibration.out_bottom_roi),
        },
    }


def load_config(config_path: Path) -> AppConfig:
    cfg = AppConfig()
    if not config_path.exists():
        return cfg

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"WARNING_CONFIG_LOAD_FAILED: {exc}")
        return cfg

    cfg.camera_index = int(data.get("camera_index", cfg.camera_index))
    cfg.frame_width = optional_int(data.get("frame_width", cfg.frame_width), cfg.frame_width)
    cfg.frame_height = optional_int(data.get("frame_height", cfg.frame_height), cfg.frame_height)
    cfg.backend = str(data.get("backend", cfg.backend)).lower()
    cfg.pixel_difference_threshold = int(data.get("pixel_difference_threshold", cfg.pixel_difference_threshold))
    cfg.min_presence_change_ratio = float(data.get("min_presence_change_ratio", cfg.min_presence_change_ratio))
    cfg.min_align_in_change_ratio = float(data.get("min_align_in_change_ratio", cfg.min_align_in_change_ratio))

    out_fallback = float(data.get("max_align_out_change_ratio", cfg.max_out_top_change_ratio))
    cfg.max_out_top_change_ratio = float(data.get("max_out_top_change_ratio", out_fallback))
    cfg.max_out_left_change_ratio = float(data.get("max_out_left_change_ratio", out_fallback))
    cfg.max_out_right_change_ratio = float(data.get("max_out_right_change_ratio", out_fallback))
    cfg.max_out_bottom_change_ratio = float(data.get("max_out_bottom_change_ratio", out_fallback))

    cfg.out_difference_mode = str(data.get("out_difference_mode", cfg.out_difference_mode)).lower()
    if cfg.out_difference_mode not in {"absolute", "bright_only"}:
        cfg.out_difference_mode = "absolute"
    cfg.alignment_enabled = bool(data.get("alignment_enabled", cfg.alignment_enabled))
    cfg.alignment_max_shift_px = float(data.get("alignment_max_shift_px", cfg.alignment_max_shift_px))
    cfg.alignment_min_response = float(data.get("alignment_min_response", cfg.alignment_min_response))
    cfg.alignment_downscale = float(data.get("alignment_downscale", cfg.alignment_downscale))
    cfg.vote_window = max(1, int(data.get("vote_window", cfg.vote_window)))
    cfg.vote_required = max(1, min(cfg.vote_window, int(data.get("vote_required", cfg.vote_required))))
    cfg.magnifier_size = max(1, int(data.get("magnifier_size", cfg.magnifier_size)))
    cfg.magnifier_zoom = max(1, int(data.get("magnifier_zoom", cfg.magnifier_zoom)))

    calibration = data.get("calibration", {})
    if isinstance(calibration, dict):
        cfg.calibration = ManualCalibration(
            presence_roi=polygon_from_dict(calibration.get("presence_roi", [])),
            align_in_roi=polygon_from_dict(calibration.get("align_in_roi", [])),
            out_top_roi=polygon_from_dict(calibration.get("out_top_roi", [])),
            out_left_roi=polygon_from_dict(calibration.get("out_left_roi", [])),
            out_right_roi=polygon_from_dict(calibration.get("out_right_roi", [])),
            out_bottom_roi=polygon_from_dict(calibration.get("out_bottom_roi", [])),
        )
    return cfg


def save_config(cfg: AppConfig, config_path: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(to_config_dict(cfg), indent=2), encoding="utf-8")
    print(f"CONFIG_SAVED: {config_path}")


def parse_backend(name: str):
    name = name.lower()
    if name == "auto":
        return None
    if name == "dshow":
        return cv2.CAP_DSHOW
    if name == "msmf":
        return cv2.CAP_MSMF
    raise ValueError(f"Unsupported backend: {name}")


def open_camera(camera_index: int, backend_name: str):
    backend = parse_backend(backend_name)
    cap = cv2.VideoCapture(camera_index) if backend is None else cv2.VideoCapture(camera_index, backend)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Failed to open camera index {camera_index} with backend '{backend_name}'.")
    ok, frame = cap.read()
    if not ok or frame is None:
        cap.release()
        raise RuntimeError(f"Camera opened but no frame arrived from camera index {camera_index}.")
    return cap


def order_quad_points(points: Any) -> Any:
    """Return four clicked points in top-left, top-right, bottom-right, bottom-left order."""
    pts = np.asarray(points, dtype=np.float32).reshape(4, 2)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(-1)
    ordered = np.array(
        [
            pts[int(np.argmin(sums))],
            pts[int(np.argmin(diffs))],
            pts[int(np.argmax(sums))],
            pts[int(np.argmax(diffs))],
        ],
        dtype=np.float32,
    )
    if len({tuple(map(float, point)) for point in ordered}) != 4:
        raise ValueError("ROI points overlap or cannot form a quadrilateral")
    if abs(float(cv2.contourArea(ordered))) < 20.0:
        raise ValueError("ROI polygon is too small")
    return ordered


def points_from_array(points: Any) -> Polygon:
    return [(float(point[0]), float(point[1])) for point in points.reshape(-1, 2)]


def polygon_as_array(roi: Polygon) -> Optional[Any]:
    if len(roi) != 4:
        return None
    return np.asarray(roi, dtype=np.float32).reshape(4, 2)


def prepare_alignment_gray(image: Any, downscale: float) -> Any:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    gray = gray.astype(np.float32)
    if 0.0 < downscale < 1.0:
        height, width = gray.shape[:2]
        target_size = (max(1, int(round(width * downscale))), max(1, int(round(height * downscale))))
        gray = cv2.resize(gray, target_size, interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(gray, (5, 5), 0)


def align_frame_to_background(frame: Any, background: Any, cfg: AppConfig) -> tuple[Any, dict[str, Any]]:
    if not cfg.alignment_enabled:
        return frame, {"enabled": False, "accepted": False, "reason": "disabled"}
    if frame.shape != background.shape:
        return frame, {"enabled": True, "accepted": False, "reason": "shape_mismatch"}

    try:
        downscale = float(cfg.alignment_downscale)
        background_gray = prepare_alignment_gray(background, downscale)
        current_gray = prepare_alignment_gray(frame, downscale)
        window_size = (background_gray.shape[1], background_gray.shape[0])
        window = cv2.createHanningWindow(window_size, cv2.CV_32F)
        (dx, dy), response = cv2.phaseCorrelate(background_gray, current_gray, window)
    except cv2.error as exc:
        return frame, {"enabled": True, "accepted": False, "reason": "error", "error": str(exc)}

    if 0.0 < downscale < 1.0:
        dx /= downscale
        dy /= downscale

    info: dict[str, Any] = {
        "enabled": True,
        "accepted": False,
        "dx": float(dx),
        "dy": float(dy),
        "response": float(response),
    }
    if response < cfg.alignment_min_response:
        info["reason"] = "response"
        return frame, info
    if abs(dx) > cfg.alignment_max_shift_px or abs(dy) > cfg.alignment_max_shift_px:
        info["reason"] = "shift"
        return frame, info

    height, width = frame.shape[:2]
    matrix = np.asarray([[1.0, 0.0, -dx], [0.0, 1.0, -dy]], dtype=np.float32)
    aligned = cv2.warpAffine(
        frame,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    info["accepted"] = True
    info["reason"] = "accepted"
    return aligned, info


def make_change_masks(frame: Any, background: Any, cfg: AppConfig) -> tuple[Any, Any]:
    if frame.shape != background.shape:
        raise ValueError(f"BACKGROUND_SIZE_MISMATCH: frame={frame.shape}, background={background.shape}")
    current_blur = cv2.GaussianBlur(frame, (5, 5), 0)
    background_blur = cv2.GaussianBlur(background, (5, 5), 0)

    absolute_difference = cv2.absdiff(current_blur, background_blur)
    absolute_change = np.max(absolute_difference, axis=2).astype(np.uint8)
    absolute_mask = ((absolute_change >= int(cfg.pixel_difference_threshold)).astype(np.uint8)) * 255

    bright_difference = cv2.subtract(current_blur, background_blur)
    bright_change = np.max(bright_difference, axis=2).astype(np.uint8)
    bright_mask = ((bright_change >= int(cfg.pixel_difference_threshold)).astype(np.uint8)) * 255
    return absolute_mask, bright_mask


def ratio_in_polygon(binary_mask: Any, polygon: Any) -> float:
    roi_mask = np.zeros(binary_mask.shape[:2], dtype=np.uint8)
    points = np.round(polygon).astype(np.int32).reshape(-1, 1, 2)
    cv2.fillConvexPoly(roi_mask, points, 255)
    area = float(cv2.countNonZero(roi_mask))
    if area <= 0.0:
        return 0.0
    changed = float(cv2.countNonZero(cv2.bitwise_and(binary_mask, roi_mask)))
    return changed / area


def maybe_print_status(state: dict[str, Optional[str]], key: str, value: str) -> None:
    if state.get(key) != value:
        state[key] = value
        print(value)


def vote_status(history: deque[str], raw_status: str, cfg: AppConfig) -> str:
    if raw_status not in {"PAPER_OK", "PAPER_NG", "PAPER_NOT_FOUND"}:
        history.clear()
        return raw_status
    history.append(raw_status)
    counts = Counter(history)
    for status in ("PAPER_OK", "PAPER_NOT_FOUND", "PAPER_NG"):
        if counts[status] >= cfg.vote_required:
            return status
    return "PAPER_CHECKING"


def polygons_from_calibration(calibration: ManualCalibration) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, roi in (
        ("PRESENCE", calibration.presence_roi),
        ("ALIGN_IN", calibration.align_in_roi),
        ("OUT_TOP", calibration.out_top_roi),
        ("OUT_LEFT", calibration.out_left_roi),
        ("OUT_RIGHT", calibration.out_right_roi),
        ("OUT_BOTTOM", calibration.out_bottom_roi),
    ):
        polygon = polygon_as_array(roi)
        if polygon is not None:
            result[name] = polygon
    return result


def process_frame(
    frame: Any,
    background: Optional[Any],
    cfg: AppConfig,
    history: deque[str],
    last_state: dict[str, Optional[str]],
) -> FrameResult:
    background_status = "BACKGROUND_LOADED" if background is not None else "BACKGROUND_MISSING"
    calibration_status = "CALIBRATION_LOADED" if cfg.calibration.is_calibrated else "CALIBRATION_MISSING"
    polygons = polygons_from_calibration(cfg.calibration)
    ratios: dict[str, float] = {}
    alignment: dict[str, Any] = {"enabled": cfg.alignment_enabled, "accepted": False, "reason": "no_background"}

    if background is None:
        raw_status = "BACKGROUND_MISSING"
    elif not cfg.calibration.is_calibrated:
        raw_status = "CALIBRATION_MISSING"
    else:
        try:
            diff_frame, alignment = align_frame_to_background(frame, background, cfg)
            absolute_mask, bright_mask = make_change_masks(diff_frame, background, cfg)
        except ValueError as exc:
            print(exc)
            raw_status = "BACKGROUND_SIZE_MISMATCH"
        else:
            out_mask = bright_mask if cfg.out_difference_mode == "bright_only" else absolute_mask
            ratios = {name: ratio_in_polygon(absolute_mask, polygon) for name, polygon in polygons.items() if name in {"PRESENCE", "ALIGN_IN"}}
            ratios.update({name: ratio_in_polygon(out_mask, polygon) for name, polygon in polygons.items() if name.startswith("OUT_")})

            presence = ratios["PRESENCE"]
            align_in = ratios["ALIGN_IN"]

            if presence < cfg.min_presence_change_ratio:
                raw_status = "PAPER_NOT_FOUND"
            elif (
                align_in >= cfg.min_align_in_change_ratio
                and ratios["OUT_TOP"] <= cfg.max_out_top_change_ratio
                and ratios["OUT_LEFT"] <= cfg.max_out_left_change_ratio
                and ratios["OUT_RIGHT"] <= cfg.max_out_right_change_ratio
                and ratios["OUT_BOTTOM"] <= cfg.max_out_bottom_change_ratio
            ):
                raw_status = "PAPER_OK"
            else:
                raw_status = "PAPER_NG"

    stable_status = vote_status(history, raw_status, cfg)
    maybe_print_status(last_state, "background", background_status)
    maybe_print_status(last_state, "calibration", calibration_status)
    maybe_print_status(last_state, "paper", stable_status)

    return FrameResult(
        background_status=background_status,
        calibration_status=calibration_status,
        raw_paper_status=raw_status,
        paper_status=stable_status,
        polygons=polygons,
        change_ratios=ratios,
        alignment=alignment,
    )


def draw_polygon(out: Any, polygon: Any, color: tuple[int, int, int], label: str) -> None:
    points = np.round(polygon).astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(out, [points], True, color, 1)
    center = np.mean(polygon.reshape(-1, 2), axis=0)
    cv2.putText(out, label, tuple(np.round(center).astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1)


def ratio_text(ratios: dict[str, float], key: str) -> str:
    return "-" if key not in ratios else f"{ratios[key]:.2f}"


def roi_label(kind: str) -> str:
    return {
        "PRESENCE": "PRESENCE",
        "ALIGN_IN": "ALIGN IN",
        "OUT_TOP": "OUT TOP",
        "OUT_LEFT": "OUT LEFT",
        "OUT_RIGHT": "OUT RIGHT",
        "OUT_BOTTOM": "OUT BOTTOM",
    }[kind]


def roi_color(kind: str) -> tuple[int, int, int]:
    return {
        "PRESENCE": (255, 255, 0),
        "ALIGN_IN": (0, 255, 0),
        "OUT_TOP": (0, 0, 255),
        "OUT_LEFT": (255, 0, 0),
        "OUT_RIGHT": (0, 165, 255),
        "OUT_BOTTOM": (255, 0, 255),
    }[kind]


def draw_pending_polygon(out: Any, points: list[Point], kind: str) -> None:
    if not points:
        return
    color = roi_color(kind)
    int_points = [tuple(np.round(point).astype(int)) for point in np.asarray(points, dtype=np.float32)]
    for index, point in enumerate(int_points, start=1):
        cv2.circle(out, point, 5, color, -1)
        cv2.putText(out, str(index), (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1)
    for start, end in zip(int_points, int_points[1:]):
        cv2.line(out, start, end, color, 1)
    if len(int_points) >= 3:
        cv2.line(out, int_points[-1], int_points[0], color, 1)


def draw_magnifier(out: Any, frame: Any, cursor: Optional[Point], cfg: AppConfig) -> None:
    if cursor is None:
        return

    height, width = frame.shape[:2]
    sample_size = max(1, min(cfg.magnifier_size, width, height))
    if sample_size % 2 == 0 and sample_size > 1:
        sample_size -= 1

    center_x = int(round(cursor[0]))
    center_y = int(round(cursor[1]))
    half = sample_size // 2
    x0 = min(max(center_x - half, 0), max(0, width - sample_size))
    y0 = min(max(center_y - half, 0), max(0, height - sample_size))
    crop = frame[y0 : y0 + sample_size, x0 : x0 + sample_size]
    if crop.size == 0:
        return

    zoom = max(1, cfg.magnifier_zoom)
    magnified = cv2.resize(crop, (sample_size * zoom, sample_size * zoom), interpolation=cv2.INTER_NEAREST)
    box_height, box_width = magnified.shape[:2]
    if box_width > width or box_height > height:
        zoom = max(1, min(width // sample_size, height // sample_size))
        magnified = cv2.resize(crop, (sample_size * zoom, sample_size * zoom), interpolation=cv2.INTER_NEAREST)
        box_height, box_width = magnified.shape[:2]
        if box_width > width or box_height > height:
            return

    center_px = (box_width // 2, box_height // 2)
    cv2.line(magnified, (center_px[0], 0), (center_px[0], box_height - 1), (0, 255, 255), 1)
    cv2.line(magnified, (0, center_px[1]), (box_width - 1, center_px[1]), (0, 255, 255), 1)
    cv2.rectangle(magnified, (0, 0), (box_width - 1, box_height - 1), (255, 255, 255), 1)

    margin = 12
    x = center_x + margin
    y = center_y + margin
    if x + box_width > width:
        x = center_x - margin - box_width
    if y + box_height > height:
        y = center_y - margin - box_height
    x = max(0, min(x, width - box_width))
    y = max(0, min(y, height - box_height))
    out[y : y + box_height, x : x + box_width] = magnified


def alignment_text(alignment: dict[str, Any]) -> str:
    if not alignment.get("enabled", True):
        return "ALIGN: OFF"
    if alignment.get("accepted"):
        return "ALIGN: ON dx={:.1f} dy={:.1f} resp={:.2f}".format(
            float(alignment.get("dx", 0.0)),
            float(alignment.get("dy", 0.0)),
            float(alignment.get("response", 0.0)),
        )
    reason = str(alignment.get("reason", "pending"))
    return f"ALIGN: SKIP {reason}"


def draw_overlay(
    frame: Any,
    result: FrameResult,
    cfg: AppConfig,
    pending_points: Optional[list[Point]] = None,
    pending_kind: Optional[str] = None,
    selection_cursor: Optional[Point] = None,
) -> Any:
    out = frame.copy()
    for kind in ROI_ORDER:
        polygon = result.polygons.get(kind)
        if polygon is not None:
            draw_polygon(out, polygon, roi_color(kind), roi_label(kind))

    if pending_kind is not None:
        if pending_points:
            draw_pending_polygon(out, pending_points, pending_kind)
        draw_magnifier(out, frame, selection_cursor, cfg)

    ratios = result.change_ratios
    out_mode = cfg.out_difference_mode if cfg.out_difference_mode in {"absolute", "bright_only"} else "absolute"
    lines = [
        f"BACKGROUND: {result.background_status}",
        f"CALIBRATION: {result.calibration_status}",
        f"PAPER: {result.paper_status} (raw={result.raw_paper_status})",
        alignment_text(result.alignment),
        f"PRESENCE diff:  {ratio_text(ratios, 'PRESENCE')} >= {cfg.min_presence_change_ratio:.2f}",
        f"ALIGN IN diff:  {ratio_text(ratios, 'ALIGN_IN')} >= {cfg.min_align_in_change_ratio:.2f}",
        f"OUT TOP diff:   {ratio_text(ratios, 'OUT_TOP')} <= {cfg.max_out_top_change_ratio:.2f} ({out_mode})",
        f"OUT LEFT diff:  {ratio_text(ratios, 'OUT_LEFT')} <= {cfg.max_out_left_change_ratio:.2f} ({out_mode})",
        f"OUT RIGHT diff: {ratio_text(ratios, 'OUT_RIGHT')} <= {cfg.max_out_right_change_ratio:.2f} ({out_mode})",
        f"OUT BOTTOM diff:{ratio_text(ratios, 'OUT_BOTTOM')} <= {cfg.max_out_bottom_change_ratio:.2f} ({out_mode})",
        "Keys: b=save empty background, 1=PRESENCE, 2=ALIGN_IN, 3=OUT_TOP, 4=OUT_LEFT, 5=OUT_RIGHT, 6=OUT_BOTTOM",
        "      e=reload config, x=cancel points, z=undo, r=reset ROIs, s=save config, q=quit",
    ]
    if pending_points is not None and pending_kind is not None:
        lines.append(f"CLICK 4 POINTS FOR {roi_label(pending_kind)} ROI: {len(pending_points)}/4")

    y = 28
    for line in lines:
        cv2.putText(out, line, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1)
        y += 25
    return out


def set_clicked_roi(cfg: AppConfig, image_points: list[Point], kind: str) -> bool:
    try:
        polygon = points_from_array(order_quad_points(np.asarray(image_points, dtype=np.float32)))
    except ValueError as exc:
        print(f"ROI_NOT_SET: {exc}")
        return False

    if kind == "PRESENCE":
        cfg.calibration.presence_roi = polygon
    elif kind == "ALIGN_IN":
        cfg.calibration.align_in_roi = polygon
    elif kind == "OUT_TOP":
        cfg.calibration.out_top_roi = polygon
    elif kind == "OUT_LEFT":
        cfg.calibration.out_left_roi = polygon
    elif kind == "OUT_RIGHT":
        cfg.calibration.out_right_roi = polygon
    elif kind == "OUT_BOTTOM":
        cfg.calibration.out_bottom_roi = polygon
    else:
        raise ValueError(f"Unknown ROI kind: {kind}")

    print(f"{kind}_ROI_SET")
    return True


def undo_last_roi(cfg: AppConfig) -> None:
    for attr, message in (
        ("out_bottom_roi", "OUT_BOTTOM_ROI_REMOVED"),
        ("out_right_roi", "OUT_RIGHT_ROI_REMOVED"),
        ("out_left_roi", "OUT_LEFT_ROI_REMOVED"),
        ("out_top_roi", "OUT_TOP_ROI_REMOVED"),
        ("align_in_roi", "ALIGN_IN_ROI_REMOVED"),
        ("presence_roi", "PRESENCE_ROI_REMOVED"),
    ):
        if getattr(cfg.calibration, attr):
            setattr(cfg.calibration, attr, [])
            print(message)
            return
    print("NO_ROI_TO_UNDO")


def reset_calibration(cfg: AppConfig) -> None:
    cfg.calibration = ManualCalibration()
    print("CALIBRATION_RESET")


def save_background(frame: Any, path: Path) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame):
        raise RuntimeError(f"Failed to save background image: {path}")
    print(f"BACKGROUND_SAVED: {path}")
    return frame.copy()


def load_background(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    background = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if background is None:
        print(f"WARNING_BACKGROUND_LOAD_FAILED: {path}")
        return None
    print(f"BACKGROUND_LOADED: {path}")
    return background


def save_debug_image(path: Path, overlay: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), overlay)
    print(f"DEBUG_IMAGE_SAVED: {path}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Paper alignment check using six manual ROIs, saved empty background diff, and optional translation alignment.")
    p.add_argument("--camera-index", type=int, default=None)
    p.add_argument("--config", type=Path, default=Path("paper_align_config.json"))
    p.add_argument("--background", type=Path, default=None, help="Saved empty-scanner image path. Default: config stem + _background.png")
    p.add_argument("--backend", choices=["auto", "dshow", "msmf"], default=None)
    p.add_argument("--image", type=Path, default=None, help="Use a static image instead of the camera.")
    p.add_argument("--save-debug", type=Path, default=None)
    p.add_argument("--pixel-difference-threshold", type=int, default=None)
    p.add_argument("--min-presence-change-ratio", type=float, default=None)
    p.add_argument("--min-align-in-change-ratio", type=float, default=None)
    p.add_argument("--max-out-top-change-ratio", type=float, default=None)
    p.add_argument("--max-out-left-change-ratio", type=float, default=None)
    p.add_argument("--max-out-right-change-ratio", type=float, default=None)
    p.add_argument("--max-out-bottom-change-ratio", type=float, default=None)
    p.add_argument("--out-difference-mode", choices=["absolute", "bright_only"], default=None)
    p.add_argument("--disable-alignment", action="store_true", help="Disable translation-only live-frame alignment before background diff.")
    p.add_argument("--alignment-max-shift-px", type=float, default=None)
    p.add_argument("--alignment-min-response", type=float, default=None)
    p.add_argument("--alignment-downscale", type=float, default=None)
    p.add_argument("--magnifier-size", type=int, default=None)
    p.add_argument("--magnifier-zoom", type=int, default=None)
    return p


def apply_arg_overrides(cfg: AppConfig, args: argparse.Namespace) -> None:
    if args.camera_index is not None:
        cfg.camera_index = args.camera_index
    if args.backend is not None:
        cfg.backend = args.backend
    if args.pixel_difference_threshold is not None:
        cfg.pixel_difference_threshold = args.pixel_difference_threshold
    if args.min_presence_change_ratio is not None:
        cfg.min_presence_change_ratio = args.min_presence_change_ratio
    if args.min_align_in_change_ratio is not None:
        cfg.min_align_in_change_ratio = args.min_align_in_change_ratio
    if args.max_out_top_change_ratio is not None:
        cfg.max_out_top_change_ratio = args.max_out_top_change_ratio
    if args.max_out_left_change_ratio is not None:
        cfg.max_out_left_change_ratio = args.max_out_left_change_ratio
    if args.max_out_right_change_ratio is not None:
        cfg.max_out_right_change_ratio = args.max_out_right_change_ratio
    if args.max_out_bottom_change_ratio is not None:
        cfg.max_out_bottom_change_ratio = args.max_out_bottom_change_ratio
    if args.out_difference_mode is not None:
        cfg.out_difference_mode = args.out_difference_mode
    if args.disable_alignment:
        cfg.alignment_enabled = False
    if args.alignment_max_shift_px is not None:
        cfg.alignment_max_shift_px = args.alignment_max_shift_px
    if args.alignment_min_response is not None:
        cfg.alignment_min_response = args.alignment_min_response
    if args.alignment_downscale is not None:
        cfg.alignment_downscale = args.alignment_downscale
    if args.magnifier_size is not None:
        cfg.magnifier_size = max(1, args.magnifier_size)
    if args.magnifier_zoom is not None:
        cfg.magnifier_zoom = max(1, args.magnifier_zoom)


def event_loop(frame_source, cfg: AppConfig, args: argparse.Namespace, background_path: Path) -> int:
    main_window = "Paper Alignment Check"
    cv2.namedWindow(main_window, cv2.WINDOW_NORMAL)
    history: deque[str] = deque(maxlen=cfg.vote_window)
    last_state: dict[str, Optional[str]] = {"background": None, "calibration": None, "paper": None}
    last_frame: Optional[Any] = None
    last_result: Optional[FrameResult] = None
    last_overlay: Optional[Any] = None
    background: Optional[Any] = load_background(background_path)

    selection: dict[str, Any] = {
        "active": False,
        "kind": None,
        "points": [],
        "frame": None,
        "result": None,
        "mouse": None,
    }

    def clear_history() -> None:
        history.clear()
        last_state["background"] = None
        last_state["calibration"] = None
        last_state["paper"] = None

    def refresh_mouse_callback() -> None:
        cv2.setMouseCallback(main_window, on_mouse)

    def cancel_selection() -> None:
        if selection["active"]:
            print("ROI_SELECTION_CANCELLED")
        selection["active"] = False
        selection["kind"] = None
        selection["points"] = []
        selection["frame"] = None
        selection["result"] = None
        selection["mouse"] = None

    def begin_selection(kind: str) -> None:
        if last_frame is None or last_result is None:
            print("FRAME_NOT_READY: ROI_NOT_SET")
            return
        selection["active"] = True
        selection["kind"] = kind
        selection["points"] = []
        selection["frame"] = last_frame.copy()
        selection["result"] = last_result
        selection["mouse"] = None
        refresh_mouse_callback()
        print(f"CLICK_4_POINTS_FOR_{kind}_ROI")

    def reload_config_from_disk() -> None:
        nonlocal cfg, history
        calibration = cfg.calibration
        cfg = load_config(args.config)
        cfg.calibration = calibration
        apply_arg_overrides(cfg, args)
        history = deque(maxlen=cfg.vote_window)
        clear_history()
        print("CONFIG_RELOADED_KEEPING_ROIS")

    def on_mouse(event, x, y, flags, param) -> None:
        del flags, param
        if not selection["active"]:
            return
        if event in (cv2.EVENT_MOUSEMOVE, cv2.EVENT_LBUTTONDOWN):
            selection["mouse"] = (float(x), float(y))
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        selection["points"].append((float(x), float(y)))
        print(f"ROI_POINT_{len(selection['points'])}: {x}, {y}")
        if len(selection["points"]) < 4:
            return
        set_clicked_roi(cfg, list(selection["points"]), str(selection["kind"]))
        cancel_selection()
        clear_history()

    refresh_mouse_callback()

    try:
        while True:
            if selection["active"]:
                display_frame = selection["frame"]
                display_result = selection["result"]
                if display_frame is not None and display_result is not None:
                    last_overlay = draw_overlay(
                        display_frame,
                        display_result,
                        cfg,
                        pending_points=list(selection["points"]),
                        pending_kind=str(selection["kind"]),
                        selection_cursor=selection["mouse"],
                    )
                    if last_overlay is not None:
                        cv2.imshow(main_window, last_overlay)
                        refresh_mouse_callback()
            else:
                frame = frame_source()
                if frame is None:
                    continue
                last_frame = frame
                last_result = process_frame(frame, background, cfg, history, last_state)
                last_overlay = draw_overlay(frame, last_result, cfg)
                if last_overlay is not None:
                    cv2.imshow(main_window, last_overlay)
                    refresh_mouse_callback()

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("x") or key == 27:
                cancel_selection()
            elif key == ord("1"):
                begin_selection("PRESENCE")
            elif key == ord("2"):
                begin_selection("ALIGN_IN")
            elif key == ord("3"):
                begin_selection("OUT_TOP")
            elif key == ord("4"):
                begin_selection("OUT_LEFT")
            elif key == ord("5"):
                begin_selection("OUT_RIGHT")
            elif key == ord("6"):
                begin_selection("OUT_BOTTOM")
            elif key == ord("b") and not selection["active"]:
                if last_frame is None:
                    print("FRAME_NOT_READY: BACKGROUND_NOT_SAVED")
                else:
                    background = save_background(last_frame, background_path)
                    clear_history()
            elif key == ord("z") and not selection["active"]:
                undo_last_roi(cfg)
                clear_history()
            elif key == ord("r") and not selection["active"]:
                reset_calibration(cfg)
                clear_history()
            elif key == ord("s") and not selection["active"]:
                save_config(cfg, args.config)
                if background is None:
                    print("WARNING: remove paper and press b to save an empty-scanner background")
                if not cfg.calibration.is_calibrated:
                    print("WARNING: set ROI 1, ROI 2, ROI 3, ROI 4, ROI 5, and ROI 6")
                if args.save_debug is not None and last_overlay is not None:
                    save_debug_image(args.save_debug, last_overlay)
            elif key == ord("e") and not selection["active"]:
                reload_config_from_disk()
    finally:
        cv2.destroyAllWindows()
    return 0


def run_camera(cfg: AppConfig, args: argparse.Namespace, background_path: Path) -> int:
    cap = open_camera(cfg.camera_index, cfg.backend)
    if cfg.frame_width is not None:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
    if cfg.frame_height is not None:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)

    def next_frame() -> Optional[Any]:
        ok, frame = cap.read()
        return frame if ok else None

    try:
        return event_loop(next_frame, cfg, args, background_path)
    finally:
        cap.release()


def run_static_image(cfg: AppConfig, args: argparse.Namespace, background_path: Path) -> int:
    frame = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"Failed to read image: {args.image}")

    def next_frame() -> Any:
        return frame.copy()

    return event_loop(next_frame, cfg, args, background_path)


def main() -> int:
    args = parser().parse_args()
    if cv2 is None or np is None:
        raise ModuleNotFoundError("Install dependencies: pip install numpy opencv-python")
    cfg = load_config(args.config)
    apply_arg_overrides(cfg, args)
    background_path = args.background if args.background is not None else default_background_path(args.config)
    return run_static_image(cfg, args, background_path) if args.image is not None else run_camera(cfg, args, background_path)


if __name__ == "__main__":
    raise SystemExit(main())
