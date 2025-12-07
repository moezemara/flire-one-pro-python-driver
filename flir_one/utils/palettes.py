"""
False-color palettes for FLIR thermal images.

Provides functions to colorize grayscale thermal data using
various color schemes.
"""

from __future__ import annotations
import numpy as np
import cv2
from typing import Literal

__all__ = ["Palette", "colorize"]

Palette = Literal["iron", "rainbow", "whitehot", "blackhot", "inferno", "turbo", "hot", "jet"]


def colorize(gray8: np.ndarray,
             palette: Palette = "iron") -> np.ndarray:
    """
    Apply false-color palette to grayscale thermal image.

    Parameters
    ----------
    gray8 : np.ndarray
        Grayscale thermal image (uint8)
    palette : Palette
        Color palette name

    Returns
    -------
    np.ndarray
        Colorized BGR image

    Raises
    ------
    ValueError
        If palette name is unknown
    """
    if gray8.dtype != np.uint8:
        gray8 = gray8.astype(np.uint8)

    if palette == "iron" or palette == "inferno":
        return cv2.applyColorMap(gray8, cv2.COLORMAP_INFERNO)
    elif palette == "rainbow":
        return cv2.applyColorMap(gray8, cv2.COLORMAP_RAINBOW)
    elif palette == "turbo":
        return cv2.applyColorMap(gray8, cv2.COLORMAP_TURBO)
    elif palette == "hot":
        return cv2.applyColorMap(gray8, cv2.COLORMAP_HOT)
    elif palette == "jet":
        return cv2.applyColorMap(gray8, cv2.COLORMAP_JET)
    elif palette == "whitehot":
        return cv2.cvtColor(gray8, cv2.COLOR_GRAY2BGR)
    elif palette == "blackhot":
        return cv2.cvtColor(255 - gray8, cv2.COLOR_GRAY2BGR)
    else:
        raise ValueError(f"unknown palette: {palette}")
