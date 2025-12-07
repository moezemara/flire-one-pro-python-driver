"""
Streaming classifier for FLIR One Pro USB slices.

The classifier maintains state to properly handle multi-slice JPEG images
and associated telemetry data.

Behavior
--------
- Once an SOI (Start of Image, FFD8) is detected, the classifier locks into
  "collecting JPEG" mode
- Every following slice is labeled as "visible" until an EOI (End of Image,
  FFD9) is seen
- After EOI, the classifier expects one telemetry JSON slice (if present)
  and labels it "telemetry"
- Then it unlocks and normal classification resumes

This guarantees:
- JPEG parts never get mis-labeled as AGC/PACKETS/EDGE
- Telemetry immediately following a JPEG is associated with that image
  instead of the next frame
"""

MAGIC_EFBE = b"\xEF\xBE\x00\x00"

_collecting_jpeg = False
_waiting_tel     = False


def _looks_like_jpeg_start(buf: bytes) -> bool:
    """Check if buffer starts with JPEG SOI marker."""
    return (
        buf[0:2] == b"\xFF\xD8" and
        buf[2:4] == b"\xFF\xC0" and
        buf[4:6] == b"\x00\x11"
    )


def _looks_like_telemetry(buf: bytes) -> bool:
    """Check if buffer appears to be JSON telemetry data."""
    ln = len(buf)
    return (
        120 <= ln <= 512 and
        b'{' in buf and
        buf.rstrip(b"\0")[-1:] == b'}'
    )


def classify(buf: bytes) -> str:
    """
    Classify a USB slice based on its content.

    Parameters
    ----------
    buf : bytes
        Raw USB slice data (typically 32,768 bytes or less)

    Returns
    -------
    str
        Slice type: 'visible', 'telemetry', 'packets', 'agc', 'edge_rle',
        'sync', 'keep_alive', or 'unknown'
    """
    global _collecting_jpeg, _waiting_tel

    # ── Locked States ──────────────────────────────────────────────
    if _collecting_jpeg:
        if b"\xFF\xD9" in buf:             # end-of-image reached
            _collecting_jpeg = False
            _waiting_tel     = True        # expect telemetry next
        return "visible"

    if _waiting_tel:
        if _looks_like_telemetry(buf):
            _waiting_tel = False
            return "telemetry"
        # even if telemetry missing, unlock after one non-JPEG slice
        _waiting_tel = False

    # ── Normal Detection ───────────────────────────────────────────
    if _looks_like_jpeg_start(buf):
        _collecting_jpeg = True
        # immediate SOI+EOI in same slice?
        if b"\xFF\xD9" in buf:
            _collecting_jpeg = False
            _waiting_tel     = True
        return "visible"

    ln = len(buf)
    if ln == 0:                          return "keep_alive"
    if ln == 28 and buf.startswith(MAGIC_EFBE): return "sync"
    if 10_000 <= ln <= 11_000:           return "packets"
    if _looks_like_telemetry(buf):       return "telemetry"
    if 7_000 <= ln <= 25_000             \
       and buf[:2] != b"\xFF\xD8":       return "edge_rle"
    if ln == 32_768:                     return "agc"   # legacy / rarely used

    return "unknown"
