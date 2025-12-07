"""
Sync marker decoder for FLIR One Pro.

Decodes 28-byte EFBE sync records that mark frame boundaries
and contain frame metadata.
"""
import struct, collections

__all__ = ["Sync", "decode"]

Sync = collections.namedtuple(
    "Sync",
    "magic zero flag len_packet len_json ts_low ts_high reserved"
)

_FMT = struct.Struct("<I I I I I I I I")      # 32 B; last field seldom used


def decode(buf: bytes) -> Sync:
    """
    Decode a sync marker.

    Parameters
    ----------
    buf : bytes
        28-byte sync marker starting with EFBE

    Returns
    -------
    Sync
        Named tuple containing sync metadata

    Raises
    ------
    ValueError
        If buffer is not a valid sync marker
    """
    if len(buf) != 28 or buf[:2] != b"\xEF\xBE":
        raise ValueError("not sync")
    # pad to 32 B so Struct can unpack cleanly
    padded = buf + b"\0" * 4
    return Sync._make(_FMT.unpack(padded))
