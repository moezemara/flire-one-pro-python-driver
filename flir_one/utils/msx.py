"""
MSX (Multi-Spectral Dynamic Imaging) overlay utility.

Overlays edge masks from the visible camera onto thermal images
to add fine detail.
"""

from __future__ import annotations
import cv2, numpy as np
from typing import Tuple

__all__ = ["overlay"]

_EDGE_COLOUR: Tuple[int, int, int] = (0, 255, 0)   # BGR green
_ALPHA: float = 0.40                               # 40% edge weight


def _or_block(mask: np.ndarray, v: int, h: int) -> np.ndarray:
    """
    Logical-OR down-sample by v rows and h columns.

    Parameters
    ----------
    mask : np.ndarray
        Binary mask
    v : int
        Vertical block size
    h : int
        Horizontal block size

    Returns
    -------
    np.ndarray
        Down-sampled mask

    Raises
    ------
    ValueError
        If mask dimensions not divisible by block size
    """
    mh, mw = mask.shape
    if mh % v or mw % h:
        raise ValueError("mask dims not divisible by block size")
    return (mask.reshape(mh // v, v, mw // h, h)
                .any(axis=(1, 3))
                .astype(np.uint8) * 255)


def overlay(bgr: np.ndarray,
            mask: np.ndarray,
            *,
            colour: Tuple[int, int, int] = _EDGE_COLOUR,
            alpha: float = _ALPHA) -> np.ndarray:
    """
    Blend edge mask onto BGR image using alpha compositing.

    Supported size combinations:
    - Thermal 120×160 ↔ Mask 120×160
    - Thermal  60×160 ↔ Mask 120×160  (mask down-samples 2× vertically)
    - Thermal 120×160 ↔ Mask 1080×1440 (mask down-samples 9× both directions)

    Parameters
    ----------
    bgr : np.ndarray
        BGR image to overlay on
    mask : np.ndarray
        Binary edge mask
    colour : Tuple[int, int, int]
        BGR color for edges (default: green)
    alpha : float
        Blending factor (default: 0.4)

    Returns
    -------
    np.ndarray
        Image with edge overlay

    Raises
    ------
    ValueError
        If mask size doesn't match image or isn't a supported combination
    TypeError
        If mask is not uint8 or bool
    """
    h_img, w_img = bgr.shape[:2]

    # 1) Shrink full-HD mask → 120×160
    if mask.shape == (1080, 1440):
        mask = _or_block(mask, 9, 9)

    # 2) If thermal is 60×160 (row-packet), shrink mask 2× vertically
    if h_img == 60 and mask.shape == (120, 160):
        mask = _or_block(mask, 2, 1)   # 2× vertical, keep horizontal

    # 3) Final sanity-check
    if mask.shape != (h_img, w_img):
        raise ValueError(f"mask {mask.shape} ≠ image {bgr.shape[:2]}")
    if mask.dtype not in (np.uint8, np.bool_):
        raise TypeError("mask must be uint8 or bool")

    painted = bgr.copy()
    painted[mask.astype(bool)] = colour
    return cv2.addWeighted(painted, alpha, bgr, 1.0 - alpha, 0.0)
