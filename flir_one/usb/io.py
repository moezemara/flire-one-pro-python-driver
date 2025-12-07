"""
USB I/O operations for FLIR One Pro thermal camera.

Provides generators that yield raw USB slices either from saved chunks
(offline playback) or directly from the camera (live streaming).

Functions
---------
load_chunks(dir_path, repeat=1) -> Iterator[bytes]
    Load saved chunks from disk for offline playback

live_chunks(save_dir=None, vid=VID, pid=PID) -> Iterator[bytes]
    Stream live data from connected FLIR camera
"""
from __future__ import annotations

import pathlib, binascii, time, sys
from contextlib import suppress
from typing import Iterator, Optional

import usb1
from .handshake import attempt_handshake


# ── Constants ──────────────────────────────────────────────────────
VID, PID      = 0x09CB, 0x1996          # FLIR One Pro Gen-3
THERM_EP      = 0x85                    # main bulk endpoint
NOISY_EPS     = (0x81, 0x83)            # zero-length chatter endpoints
SLICE_BYTES   = 32_768                  # size of every bulk read


# ── Offline Loader ─────────────────────────────────────────────────
def load_chunks(path: pathlib.Path, repeat: int = 1) -> Iterator[bytes]:
    """
    Read `*.txt` files containing hex-encoded USB slices.

    Each file contains one USB slice in hexadecimal format.
    Files should be named numerically (1.txt, 2.txt, etc.).

    Parameters
    ----------
    path : pathlib.Path
        Directory containing numbered .txt chunk files
    repeat : int
        Number of times to replay the chunks (use -1 for infinite loop)

    Yields
    ------
    bytes
        One 32,768-byte USB slice per iteration

    Raises
    ------
    FileNotFoundError
        If the path does not exist
    ValueError
        If the path is not a directory
    """
    if not path.exists():
        raise FileNotFoundError(path)

    if not path.is_dir():
        raise ValueError(f"{path} is not a directory of chunks")

    if repeat == -1:
        # Infinite loop
        print(f"[INFO] Replaying {path} indefinitely", file=sys.stderr)
        counter = 1
        while True:
            print(f"[INFO] Replaying {path} (iteration {counter})", file=sys.stderr)
            for fp in sorted(path.iterdir(), key=lambda p: int(p.stem)):
                yield binascii.unhexlify(fp.read_text().strip())
            counter += 1
    else:
        # Finite repeats
        while repeat > 0:
            print(f"[INFO] Replaying {path} ({repeat} times left)", file=sys.stderr)
            for fp in sorted(path.iterdir(), key=lambda p: int(p.stem)):
                yield binascii.unhexlify(fp.read_text().strip())
            repeat -= 1


# ── Live Camera Generator ──────────────────────────────────────────
def live_chunks(
    save_dir: Optional[pathlib.Path] = None,
    vid: int = VID,
    pid: int = PID,
) -> Iterator[bytes]:
    """
    Stream raw slices from a connected FLIR One Pro camera.

    Automatically handles USB errors and reconnection. Each slice is
    exactly 32,768 bytes of raw data from the camera's bulk endpoint.

    Parameters
    ----------
    save_dir : Optional[pathlib.Path]
        If provided, each slice is saved as hex text (1.txt, 2.txt, ...)
        for later offline playback
    vid : int
        USB Vendor ID (default: 0x09CB for FLIR)
    pid : int
        USB Product ID (default: 0x1996 for FLIR One Pro Gen-3)

    Yields
    ------
    bytes
        One 32,768-byte USB bulk slice on every iteration

    Notes
    -----
    This function runs indefinitely and automatically reconnects if the
    USB connection is lost. Press Ctrl+C to stop.
    """
    ctx = usb1.USBContext()
    file_idx = 1

    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)

    while True:                                 # reconnect loop
        dev = None
        try:
            dev = attempt_handshake(ctx, vid, pid)
            usb_buf = bytearray()

            while True:                         # stream loop
                # read one full 32 kB slice
                try:
                    usb_buf.extend(dev.bulkRead(THERM_EP, SLICE_BYTES, timeout=100))
                except usb1.USBErrorTimeout:
                    pass                        # benign – nothing ready
                except usb1.USBErrorIO:         # endpoint stalled
                    with suppress(usb1.USBError):
                        dev.clearHalt(THERM_EP)
                    continue

                # drain dummy endpoints quickly
                for ep in NOISY_EPS:
                    with suppress(usb1.USBErrorTimeout):
                        dev.bulkRead(ep, 4096, timeout=1)

                if not usb_buf:
                    continue

                chunk = bytes(usb_buf)
                usb_buf.clear()

                # optional dump to disk
                if save_dir:
                    (save_dir / f"{file_idx}.txt").write_text(chunk.hex())
                    file_idx += 1

                yield chunk

        except usb1.USBError as e:
            print(f"[WARN] USB error: {e} – reconnect in 2 s",
                  file=sys.stderr)
            time.sleep(2)
        finally:
            if dev:
                for i in (0, 1, 2):
                    with suppress(usb1.USBError):
                        dev.releaseInterface(i)
                with suppress(usb1.USBError):
                    (hasattr(dev, "resetDevice") and dev.resetDevice()) or \
                    (hasattr(dev, "reset") and dev.reset())
                dev.close()
