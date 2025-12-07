"""
Telemetry decoder for FLIR One Pro camera.

Extracts camera telemetry from JSON-formatted USB slices, including
battery status, shutter state, and temperature readings.
"""
import json, string, dataclasses, typing as T

_PRINTABLE = set(string.printable)          # ASCII 0x20-0x7E plus \t\r\n\x0b\f
_decoder   = json.JSONDecoder()

__all__ = ["Telemetry", "decode"]


@dataclasses.dataclass
class Telemetry:
    """
    FLIR One Pro telemetry data.

    Attributes
    ----------
    shutter_state : Optional[str]
        Shutter state (e.g., "open", "closed")
    ffc_state : Optional[str]
        Flat field correction state
    shutter_tempK : Optional[float]
        Shutter temperature in Kelvin
    aux_tempK : Optional[float]
        Auxiliary temperature in Kelvin
    t_notify : Optional[float]
        USB notification timestamp
    t_enqueue : Optional[float]
        USB enqueue timestamp
    battery_voltage : Optional[float]
        Battery voltage in volts
    battery_percent : Optional[float]
        Battery percentage (0-100)
    """
    shutter_state   : T.Optional[str] = None
    ffc_state       : T.Optional[str] = None
    shutter_tempK   : T.Optional[float] = None
    aux_tempK       : T.Optional[float] = None
    t_notify        : T.Optional[float] = None
    t_enqueue       : T.Optional[float] = None
    battery_voltage : T.Optional[float] = None
    battery_percent : T.Optional[float] = None


def _strip_ctl(bs: bytes) -> str:
    """
    ASCII-decode and remove control chars that break JSON parsing.

    Parameters
    ----------
    bs : bytes
        Raw telemetry bytes

    Returns
    -------
    str
        Cleaned ASCII string
    """
    txt = bs.decode("ascii", "ignore")
    return "".join(c for c in txt if c in _PRINTABLE)


def _iter_json_objs(s: str):
    """
    Yield every JSON object found in string.

    Robust against invalid bytes and malformed JSON.

    Parameters
    ----------
    s : str
        String potentially containing multiple JSON objects

    Yields
    ------
    dict
        Parsed JSON objects
    """
    i = 0
    while True:
        j = s.find("{", i)
        if j == -1:
            break
        try:
            obj, end = _decoder.raw_decode(s[j:])
            yield obj
            i = j + end
        except json.JSONDecodeError:
            i = j + 1


def decode(buf: bytes) -> T.Optional[Telemetry]:
    """
    Decode telemetry from raw USB slice.

    Prefers battery voltage frames when present, falls back to
    legacy shutter/temperature telemetry.

    Parameters
    ----------
    buf : bytes
        Raw telemetry slice data

    Returns
    -------
    Optional[Telemetry]
        Parsed telemetry data, or None if no valid telemetry found
    """
    s = _strip_ctl(buf.lstrip(b"\x00").rstrip(b"\x00"))
    if "{" not in s:
        return None

    first_fallback: T.Optional[Telemetry] = None

    try:
        for obj in _iter_json_objs(s):

            # ── Highest priority: power telemetry ──────────────────
            if obj.get("type") == "batteryVoltageUpdate":
                data = obj.get("data", {})
                return Telemetry(
                    battery_voltage = data.get("voltage"),
                    battery_percent = data.get("percentage"),
                )

            # ── Legacy telemetry (record first one as fallback) ────
            if first_fallback is None and (
                "shutterState" in obj or "ffcState" in obj
            ):
                first_fallback = Telemetry(
                    shutter_state   = obj.get("shutterState"),
                    ffc_state       = obj.get("ffcState"),
                    shutter_tempK   = obj.get("shutterTemperature"),
                    aux_tempK       = obj.get("auxTemperature"),
                    t_notify        = obj.get("usbNotifiedTimestamp"),
                    t_enqueue       = obj.get("usbEnqueuedTimestamp"),
                )

        # No battery voltage update found – return first legacy frame
        return first_fallback

    except Exception:
        return None
