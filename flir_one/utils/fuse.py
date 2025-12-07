"""
Image fusion utilities for FLIR One Pro.

Provides functions to fuse visible and thermal images, and overlay
telemetry metrics on images.
"""
from __future__ import annotations
from typing import Tuple, List, Dict, Any
import cv2, numpy as np

__all__ = ["fuse_visible_and_thermal", "overlay_metrics"]

# Color palettes available in OpenCV
_PALETTES = {
    "inferno": cv2.COLORMAP_INFERNO,
    "turbo":   cv2.COLORMAP_TURBO,
    "hot":     cv2.COLORMAP_HOT,
    "jet":     cv2.COLORMAP_JET,
}


def _colorize_thermal(raw: np.ndarray, palette: str) -> np.ndarray:
    """
    Normalize and apply false-color palette to thermal data.

    Parameters
    ----------
    raw : np.ndarray
        Raw thermal data
    palette : str
        Palette name

    Returns
    -------
    np.ndarray
        Colorized BGR uint8 image
    """
    norm = cv2.normalize(raw, None, 0, 255, cv2.NORM_MINMAX)
    lut  = _PALETTES.get(palette.lower(), cv2.COLORMAP_INFERNO)
    return cv2.applyColorMap(norm.astype(np.uint8), lut)


def fuse_visible_and_thermal(
    visible_bgr : np.ndarray,
    thermal_raw : np.ndarray,
    *,
    alpha   : float = 0.40,
    palette : str   = "inferno",
) -> np.ndarray:
    """
    Alpha-blend colorized thermal over visible frame.

    Parameters
    ----------
    visible_bgr : np.ndarray
        Visible camera image (BGR)
    thermal_raw : np.ndarray
        Raw thermal data (uint16)
    alpha : float
        Blending factor for thermal overlay (0.0-1.0)
    palette : str
        Color palette for thermal ('inferno', 'turbo', 'hot', 'jet')

    Returns
    -------
    np.ndarray
        Fused BGR image at visible camera resolution
    """
    vis_h, vis_w = visible_bgr.shape[:2]

    therm_colour = _colorize_thermal(thermal_raw, palette)
    therm_up     = cv2.resize(therm_colour, (vis_w, vis_h),
                              interpolation=cv2.INTER_LINEAR)

    return cv2.addWeighted(visible_bgr, 1.0 - alpha, therm_up, alpha, 0)


def overlay_metrics(
    img        : np.ndarray,
    *,
    metrics    : Dict[str, Any] | None = None,
    fps        : float | None          = None,
    keys       : List[str] | None      = None,
    single_line: bool                  = False,
    anchor     : Tuple[int, int]       = (5, 15),
    colour     : Tuple[int, int, int]  = (255, 255, 255),
) -> np.ndarray:
    """
    Draw metrics dictionary and optional FPS onto image.

    Parameters
    ----------
    img : np.ndarray
        Image to draw on (modified in-place)
    metrics : Optional[Dict[str, Any]]
        Dictionary of metrics to display
    fps : Optional[float]
        Frame rate to display
    keys : Optional[List[str]]
        Specific metric keys to display (default: all)
    single_line : bool
        If True, display all metrics on one line
    anchor : Tuple[int, int]
        (x, y) position for text
    colour : Tuple[int, int, int]
        BGR color for text

    Returns
    -------
    np.ndarray
        Image with overlaid metrics (same as input img)
    """
    if metrics is None or not metrics:
        if fps is None:
            return img

    x, y = anchor
    lines: List[str] = []

    # FPS block
    if fps is not None:
        lines.append(f"FPS: {fps:4.1f}")

    # Metrics block
    if metrics:
        selected = keys if keys else list(metrics.keys())
        parts = [f"{k}={metrics[k]}" for k in selected if k in metrics]

        if parts:
            if single_line:
                lines.append(" ".join(parts))
            else:
                lines.extend(parts)

    # Render
    for ln in lines:
        cv2.putText(img, ln, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, colour, 1, cv2.LINE_AA)
        y += 20

    return img
