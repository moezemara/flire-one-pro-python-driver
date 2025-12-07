"""
FLIR One Pro Python Library

A clean, easy-to-use Python library for the FLIR One Pro Gen-3 thermal camera.

Example Usage
-------------
>>> from flir_one import Camera
>>>
>>> # Stream from live camera
>>> camera = Camera()
>>> for frame in camera.stream():
>>>     if frame.thermal is not None:
>>>         print(f"Thermal shape: {frame.thermal.shape}")
>>>         print(f"Thermal range: {frame.thermal.min()} - {frame.thermal.max()}")
>>>
>>> # Offline playback
>>> camera = Camera(offline_dir="./saved_chunks")
>>> for frame in camera.stream():
>>>     # Process frames
>>>     pass
"""

__version__ = "1.0.0"
__author__ = "FLIR One Python Contributors"
__license__ = "MIT"

from .camera import Camera, CameraFrame

__all__ = ["Camera", "CameraFrame", "__version__"]
