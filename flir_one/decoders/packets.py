"""
VoSPI row-packet decoder for FLIR Lepton 3 thermal sensor.

Decodes raw USB slices containing VoSPI packets into thermal images
with full 14-bit radiometric depth.

Format
------
Each 164-byte packet carries:
    ┌── 2 B ID ──┬── 2 B CRC ──┬──────── 160 B payload ────────┐
    │  12-bit row│            │   80 × uint16 (big-endian)     │
    └────────────┴────────────┴────────────────────────────────┘

A complete USB slice is 63 packets (60 image rows + 3 telemetry rows)
= 10,332 bytes.

Features
--------
- Masks out segment bits before using the 12-bit row number
- Skips the three telemetry packets (row-IDs 60-62)
- Views payload as big-endian uint16 (full radiometric depth)
- Fills ≤2 missing rows by copying the nearest neighbor
- Outputs a (60 × 80) uint16 image

Notes
-----
If more than two rows are missing, the function returns None,
allowing the caller to drop the corrupted frame.
"""

from __future__ import annotations
from typing import List, Optional
import numpy as np

# ─────────────────────────────── Constants ─────────────────────────
ROW_WORDS        = 80               # 80 × uint16 → 160 bytes
PACKET_LEN       = 164
IMAGE_ROWS       = 60               # 0-59 contain pixels
TELEMETRY_ROWS   = 3                # 60-62 contain telemetry
ROWS_PER_SLICE   = IMAGE_ROWS + TELEMETRY_ROWS
FRAME_BYTES      = ROWS_PER_SLICE * PACKET_LEN   # 10,332 B

__all__ = ["decode"]


# ─────────────────────────────── Helpers ───────────────────────────
def _extract_rows(buf: np.ndarray) -> List[Optional[np.ndarray]]:
    """
    Extract image rows from VoSPI packets.

    Returns
    -------
    List[Optional[np.ndarray]]
        List of 60 rows, each uint16[80] or None if missing
    """
    rows: List[Optional[np.ndarray]] = [None] * IMAGE_ROWS

    for packet in buf.reshape(-1, PACKET_LEN):
        # 12-bit row number; high nibble holds segment/discard flags
        row_id = ((packet[1] & 0x0F) << 8) | packet[0]

        # Discard telemetry (60-62) and any stray packets
        if row_id >= IMAGE_ROWS:
            continue

        payload = packet[4 : 4 + ROW_WORDS * 2]        # 160 B
        rows[row_id] = np.frombuffer(payload, dtype="<u2") & 0x3FFF

    return rows


def _assemble_frame(rows: List[Optional[np.ndarray]]) -> Optional[np.ndarray]:
    """
    Assemble rows into a frame, filling ≤2 missing rows.

    Parameters
    ----------
    rows : List[Optional[np.ndarray]]
        List of extracted rows

    Returns
    -------
    Optional[np.ndarray]
        (60, 80) uint16 array, or None if too many rows are missing
    """
    missing = [i for i, r in enumerate(rows) if r is None]
    if len(missing) > 2:
        return None

    for idx in missing:
        # prefer the preceding valid line, else the following one
        prev = next((rows[i] for i in range(idx - 1, -1, -1) if rows[i] is not None), None)
        nxt  = next((rows[i] for i in range(idx + 1, IMAGE_ROWS) if rows[i] is not None), None)
        rows[idx] = prev if prev is not None else nxt

    return np.vstack(rows).astype(np.uint16, copy=False)   # (60, 80) uint16


# ─────────────────────────────── Public API ────────────────────────
def decode(raw: bytes) -> Optional[np.ndarray]:
    """
    Convert one 10,332-byte USB slice into a (60 × 80) uint16 thermal image.

    Parameters
    ----------
    raw : bytes
        Raw USB slice data (10,332 bytes)

    Returns
    -------
    Optional[np.ndarray]
        (60, 80) uint16 thermal image, or None on length mismatch
        or too many missing rows
    """
    if len(raw) != FRAME_BYTES:
        return None

    buf   = np.frombuffer(raw, dtype=np.uint8)
    rows  = _extract_rows(buf)
    frame = _assemble_frame(rows)
    return frame
