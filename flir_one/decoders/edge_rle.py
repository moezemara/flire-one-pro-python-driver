"""
RLE-compressed edge mask decoder for FLIR One Pro.

Decodes run-length encoded edge masks from the visible camera.
These edge masks are used for MSX (Multi-Spectral Dynamic Imaging)
to overlay fine details on thermal images.

Format
------
- 4-byte little-endian length header
- 16-bit run lengths (alternating 0/1 values)
- Output: 1080×1440 boolean array
"""

import struct
import numpy as np

__all__ = ["decode"]

W, H = 1440, 1080
PIXELS = W * H


def decode(buf: bytes, w=W, h=H) -> np.ndarray:
    """
    Decode RLE-compressed edge mask.

    Parameters
    ----------
    buf : bytes
        Raw RLE-compressed edge mask data
    w : int
        Width of output mask (default: 1440)
    h : int
        Height of output mask (default: 1080)

    Returns
    -------
    np.ndarray
        (h, w) boolean array representing edge mask

    Raises
    ------
    ValueError
        If buffer is too short to contain valid RLE data
    """
    if len(buf) < 6:
        raise ValueError("edge slice too short")

    rle_len, = struct.unpack_from("<I", buf, 0)
    payload  = buf[4:4+rle_len]

    # ensure even length so iter_unpack("<H") never fails
    if len(payload) & 1:
        payload += b"\0"

    it = struct.iter_unpack("<H", payload)
    out = np.empty(PIXELS, np.bool_)
    pos, val = 0, False

    for (run,) in it:
        if pos >= PIXELS:
            break                        # ignore overflow padding
        end = min(pos+run, PIXELS)
        out[pos:end] = val
        pos  = end
        val  = not val

    if pos < PIXELS:                     # pad remainder with zeros
        out[pos:] = False

    return out.reshape(h, w)
