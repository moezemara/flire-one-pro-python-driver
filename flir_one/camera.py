"""
High-level API for FLIR One Pro camera.

Provides a simple Camera class for capturing and processing
thermal and visible images from the FLIR One Pro Gen-3 camera.

Example
-------
>>> from flir_one import Camera
>>>
>>> # Live camera streaming
>>> camera = Camera()
>>> for frame in camera.stream():
>>>     if frame.thermal is not None:
>>>         print(f"Thermal: {frame.thermal.shape}")
>>>     if frame.visible is not None:
>>>         print(f"Visible: {frame.visible.shape}")
>>>
>>> # Offline playback from saved chunks
>>> camera = Camera(offline_dir="./chunks")
>>> for frame in camera.stream():
>>>     ...
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Optional
from pathlib import Path
import numpy as np

from .usb import io as usb_io
from .usb import slice_types, assembler
from .decoders import packets, visible, telemetry, sync, agc, edge_rle
from .utils.fps import FPSMeter

__all__ = ["Camera", "CameraFrame"]


@dataclass
class CameraFrame:
    """
    A complete frame from the FLIR camera.

    Attributes
    ----------
    idx : int
        Frame index number
    thermal : Optional[np.ndarray]
        Thermal image data (60×80 uint16)
    visible : Optional[np.ndarray]
        Visible camera image (BGR, varies by camera)
    telemetry : Optional[telemetry.Telemetry]
        Camera telemetry data
    edge_mask : Optional[np.ndarray]
        Edge mask for MSX overlay
    timestamp : Optional[int]
        Frame timestamp
    """
    idx: int
    thermal: Optional[np.ndarray] = None
    visible: Optional[np.ndarray] = None
    telemetry: Optional[telemetry.Telemetry] = None
    edge_mask: Optional[np.ndarray] = None
    timestamp: Optional[int] = None


class Camera:
    """
    FLIR One Pro camera interface.

    Parameters
    ----------
    offline_dir : Optional[str | Path]
        Directory containing saved chunks for offline playback.
        If None, streams from live camera.
    save_chunks : bool
        If True, save raw USB chunks to disk (live mode only)
    chunk_save_dir : Optional[str | Path]
        Directory to save chunks (default: "./chunks")
    repeat : int
        Number of times to repeat offline chunks (default: 1, -1 for infinite)
    vid : int
        USB Vendor ID (default: 0x09CB)
    pid : int
        USB Product ID (default: 0x1996)
    """

    def __init__(
        self,
        offline_dir: Optional[str | Path] = None,
        save_chunks: bool = False,
        chunk_save_dir: Optional[str | Path] = None,
        repeat: int = 1,
        vid: int = 0x09CB,
        pid: int = 0x1996,
    ):
        self.offline_dir = Path(offline_dir) if offline_dir else None
        self.save_chunks = save_chunks
        self.chunk_save_dir = Path(chunk_save_dir or "./chunks")
        self.repeat = repeat
        self.vid = vid
        self.pid = pid

        self._assembler = assembler.FrameAssembler()
        self._fps_meter = FPSMeter()

    def stream(self) -> Iterator[CameraFrame]:
        """
        Stream frames from the camera.

        Yields
        ------
        CameraFrame
            Complete frames as they become available

        Examples
        --------
        >>> camera = Camera()
        >>> for frame in camera.stream():
        >>>     if frame.thermal is not None:
        >>>         # Process thermal data
        >>>         pass
        """
        # Get USB slice iterator
        if self.offline_dir:
            slice_iter = usb_io.load_chunks(self.offline_dir, self.repeat)
        else:
            save_dir = self.chunk_save_dir if self.save_chunks else None
            slice_iter = usb_io.live_chunks(
                save_dir=save_dir,
                vid=self.vid,
                pid=self.pid
            )

        # Process slices
        for raw_slice in slice_iter:
            label = slice_types.classify(raw_slice)

            if label == "keep_alive" or label == "unknown":
                continue

            # Decode the slice
            decoded = self._decode_slice(label, raw_slice)

            # Assemble into frame
            frame = self._assembler.push(label, decoded)

            if frame is not None:
                yield self._convert_frame(frame)

    def _decode_slice(self, label: str, raw: bytes):
        """Decode a raw USB slice based on its type."""
        decoders = {
            "packets": packets.decode,
            "visible": visible.decode,
            "telemetry": telemetry.decode,
            "sync": sync.decode,
            "agc": agc.decode,
            "edge_rle": edge_rle.decode,
        }

        decoder = decoders.get(label)
        if decoder:
            return decoder(raw)
        return None

    def _convert_frame(self, frame: assembler.Frame) -> CameraFrame:
        """Convert internal Frame to public CameraFrame."""
        # Handle visible: might be (img, tel) tuple or just img
        vis_img = None
        if frame.visible_img is not None:
            if isinstance(frame.visible_img, tuple):
                vis_img, _ = frame.visible_img
            else:
                vis_img = frame.visible_img

        return CameraFrame(
            idx=frame.idx,
            thermal=frame.packet_img,
            visible=vis_img,
            telemetry=frame.telemetry,
            edge_mask=frame.edge_mask,
            timestamp=frame.ts,
        )

    def get_fps(self) -> float:
        """
        Get current frame rate.

        Returns
        -------
        float
            Current FPS (frames per second)
        """
        return self._fps_meter.update()
