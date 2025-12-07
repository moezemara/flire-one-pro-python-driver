"""
Visible camera JPEG decoder for FLIR One Pro.

Decodes JPEG images from the visible light camera and extracts
associated telemetry data.

Format
------
Each USB slice is up to 32,768 bytes:
- JPEG starts at byte 0 (FF D8 ...)
- Optional telemetry JSON immediately follows the first FF D9
- Any remaining pad bytes are ignored

Streaming Behavior
------------------
The decoder maintains state across multiple calls:
- Accumulates bytes until an End-of-Image marker is seen
- When a full JPEG is available, returns (image, telemetry)
- On intermediate fragments, returns None
"""
from __future__ import annotations
from typing import Optional, Tuple
import cv2, numpy as np, json

__all__ = ["decode"]

# ── Module-level streaming buffer ──────────────────────────────────
_buf        = bytearray()
_collecting = False


def _extract_telemetry(tail: bytes) -> Optional[dict]:
    """
    Extract JSON telemetry from bytes following JPEG data.

    Parameters
    ----------
    tail : bytes
        Bytes after the JPEG EOI marker

    Returns
    -------
    Optional[dict]
        Parsed JSON telemetry, or None if not found
    """
    i = tail.find(b'{')
    j = tail.find(b'}', i + 1) if i != -1 else -1
    if i != -1 and j != -1:
        try:
            return json.loads(tail[i:j + 1].decode("ascii", "ignore"))
        except json.JSONDecodeError:
            pass
    return None


def decode(raw: bytes) -> Optional[Tuple[np.ndarray, Optional[dict]]]:
    """
    Decode a visible camera slice.

    Parameters
    ----------
    raw : bytes
        Raw USB slice data (up to 32,768 bytes)

    Returns
    -------
    Optional[Tuple[np.ndarray, Optional[dict]]]
        Tuple of (BGR image, telemetry dict) when complete JPEG is
        received, or None if still accumulating data
    """
    global _buf, _collecting

    # A new JPEG always starts with FF D8
    if raw.startswith(b"\xFF\xD8"):
        _buf.clear()
        _collecting = True

    if not _collecting:
        return None                # not inside a JPEG

    _buf.extend(raw)
    eoi = _buf.find(b"\xFF\xD9")   # first End-of-Image
    if eoi == -1:
        return None                # need more data

    # ── Carve out the payloads ─────────────────────────────────────
    jpeg_bytes = bytes(_buf[:eoi + 2])          # include FF D9
    tail       = bytes(_buf[eoi + 2:])          # possible telemetry

    # reset for next JPEG
    _buf.clear()
    _collecting = False

    # decode JPEG
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    tel = _extract_telemetry(tail)
    return (img, tel)
