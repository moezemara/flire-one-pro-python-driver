"""
AGC (Automatic Gain Control) slice decoder for FLIR One Pro.

Decodes 32,768-byte AGC slices into 8-bit thermal images.

Format
------
The frame is a 256 × 128 8-bit buffer padded for GPU alignment.
The active thermal image is the centered 160 × 120 region.

This decoder extracts only the active region, discarding the
padded border pixels.
"""

from __future__ import annotations
import numpy as np

__all__ = ["decode"]

_ACTIVE_W, _ACTIVE_H = 160, 120          # real Lepton-3 dimensions
_PADDED_W, _PADDED_H = 256, 128          # 32,768 B → 256×128


def _crop(img: np.ndarray) -> np.ndarray:
    """
    Extract center crop from padded image.

    Parameters
    ----------
    img : np.ndarray
        Padded (128, 256) image

    Returns
    -------
    np.ndarray
        Cropped (120, 160) image
    """
    y0 = (img.shape[0] - _ACTIVE_H) // 2
    x0 = (img.shape[1] - _ACTIVE_W) // 2
    return img[y0 : y0 + _ACTIVE_H, x0 : x0 + _ACTIVE_W].copy()


def decode(raw: bytes) -> np.ndarray:
    """
    Convert a 32,768-byte AGC slice into a (120, 160) uint8 image.

    Parameters
    ----------
    raw : bytes
        Raw AGC slice data (32,768 bytes)

    Returns
    -------
    np.ndarray
        (120, 160) uint8 thermal image

    Raises
    ------
    ValueError
        If slice is not exactly 32,768 bytes
    """
    if len(raw) != _PADDED_W * _PADDED_H:
        raise ValueError("AGC slice must be exactly 32,768 bytes")

    padded = np.frombuffer(raw, dtype=np.uint8).reshape(_PADDED_H, _PADDED_W)
    return _crop(padded)
