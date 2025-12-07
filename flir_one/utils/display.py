"""
Display rendering utilities for FLIR One Pro camera frames.

Provides functions to build display-ready images from assembled frames,
including thermal colorization, visible camera overlays, and telemetry/FPS
metrics.
"""
from __future__ import annotations
import cv2, numpy as np
from typing import Dict, Any, Optional
from .fuse import fuse_visible_and_thermal, overlay_metrics

__all__ = ["prepare_displays"]


def _build_visible(img: np.ndarray,
                   metrics: Dict[str, Any] | None,
                   fps: float | None,
                   opts: Dict[str, Any]) -> np.ndarray:
    """Build visible camera display with optional overlays."""
    out = img.copy()
    return overlay_metrics(out, metrics=metrics, fps=fps, **opts)


def _build_thermal(
        raw: np.ndarray,
        metrics: Dict[str, Any] | None,
        fps: float | None,
        opts: Dict[str, Any],
        *,
        cold_clip_pct: float = 2.0,   # ignore the darkest N %
        hot_clip_pct:  float = 99.5   # ignore the brightest N %
) -> np.ndarray:
    """
    Convert a 16-bit (or 14-bit in 16-bit container) thermal frame to a
    color preview where only the warm objects stand out.

    Features
    --------
    - Per-frame auto-gain: stretch current min→max (or percentiles) to 0-255
    - Optional percentile clipping suppresses noise & very cold background
    - Uses OpenCV's built-in INFERNO LUT

    Parameters
    ----------
    raw : np.ndarray
        Raw thermal data (uint16)
    metrics : Optional[Dict[str, Any]]
        Telemetry data to overlay
    fps : Optional[float]
        Frame rate to display
    opts : Dict[str, Any]
        Additional overlay options
    cold_clip_pct : float
        Percentile for cold clipping (default: 2.0)
    hot_clip_pct : float
        Percentile for hot clipping (default: 99.5)

    Returns
    -------
    np.ndarray
        Colorized BGR thermal image (160×120)
    """
    # work in 32-bit to avoid precision loss
    frame = raw.astype(np.float32)

    # Robust min/max – clip a few % of extremes so background goes to black
    v_min = np.percentile(frame, cold_clip_pct)
    v_max = np.percentile(frame, hot_clip_pct)
    if v_max <= v_min:                         # degenerate scene (all same)
        v_max = v_min + 1.0

    # Linear stretch → 8-bit
    grey = ((frame - v_min) * 255.0 / (v_max - v_min)).clip(0, 255).astype(np.uint8)

    # Colorize – INFERNO starts almost black and ends white-hot
    colour = cv2.applyColorMap(grey, cv2.COLORMAP_INFERNO)

    # Optional: force very cold (≤5) to pure black so they disappear completely
    colour[grey <= 5] = (0, 0, 0)

    # Resize to exactly 160×120 px (even height for display pipeline)
    colour = cv2.resize(colour, (160, 120), interpolation=cv2.INTER_LINEAR)

    # Overlay FPS / telemetry if requested
    return overlay_metrics(colour, metrics=metrics, fps=fps, **opts)


def prepare_displays(
    frame,
    *,
    alpha          : float                       = 0.40,
    palette        : str                         = "inferno",
    fps            : Dict[str, float] | None     = None,
    telemetry_data : Dict[str, Any] | None       = None,
    telemetry_show : Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, np.ndarray]:
    """
    Prepare display images from an assembled frame.

    Returns a dictionary with 'visible', 'thermal', and/or 'fused' views
    depending on what data is available in the frame.

    Parameters
    ----------
    frame : Frame
        Assembled frame from FrameAssembler
    alpha : float
        Blending factor for thermal overlay (0.0-1.0)
    palette : str
        Color palette name ('inferno', 'turbo', 'hot', 'jet')
    fps : Optional[Dict[str, float]]
        FPS values for each view
    telemetry_data : Optional[Dict[str, Any]]
        Telemetry data to overlay
    telemetry_show : Optional[Dict[str, Dict[str, Any]]]
        Per-screen overlay configuration, e.g.:
        {
          "visible":  {"single_line": False},
          "thermal":  {"keys": ["BattPct"], "single_line": True},
          "fused":    {"single_line": False},
        }

    Returns
    -------
    Dict[str, np.ndarray]
        Dictionary with available display images
    """
    fps            = fps            or {}
    telemetry_show = telemetry_show or {}

    outputs: Dict[str, np.ndarray] = {}

    if frame.visible_img is not None:
        outputs["visible"] = _build_visible(
            frame.visible_img,
            telemetry_data,
            fps.get("visible"),
            telemetry_show.get("visible", {})
        )

    if frame.packet_img is not None and frame.packet_img.size:
        outputs["thermal"] = _build_thermal(
            frame.packet_img,
            telemetry_data,
            fps.get("thermal"),
            telemetry_show.get("thermal", {})
        )

    if ("visible" in outputs) and ("thermal" in outputs):
        fused = fuse_visible_and_thermal(frame.visible_img,
                                         frame.packet_img,
                                         alpha=alpha,
                                         palette=palette)
        outputs["fused"] = overlay_metrics(
            fused,
            metrics=telemetry_data,
            fps=fps.get("fused"),
            **telemetry_show.get("fused", {})
        )

    return outputs
