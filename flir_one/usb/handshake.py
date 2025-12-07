"""USB handshake protocol for FLIR One Pro Gen-3 thermal camera."""
import os, sys, time, struct, pathlib, usb1
from contextlib import suppress


def attempt_handshake(ctx, VID, PID) -> usb1.USBDeviceHandle:
    """
    Performs the exact FLIR handshake sequence to initialize the camera.

    Parameters
    ----------
    ctx : usb1.USBContext
        USB context from libusb1
    VID : int
        Vendor ID (0x09CB for FLIR)
    PID : int
        Product ID (0x1996 for FLIR One Pro Gen-3)

    Returns
    -------
    usb1.USBDeviceHandle
        Configured device handle ready for bulk streaming
    """
    dev = ctx.openByVendorIDAndProductID(VID, PID, skip_on_error=False)

    if hasattr(dev, "setAutoDetachKernelDriver"):
        dev.setAutoDetachKernelDriver(True)
    dev.setConfiguration(3)
    for i in (0, 1, 2):
        with suppress(usb1.USBError):
            if dev.kernelDriverActive(i):
                dev.detachKernelDriver(i)
        dev.claimInterface(i)

    ctl = lambda alt, iface, wlen=0: dev.controlWrite(1, 0x0B, alt, iface,
                                                      b'\0\0'[:wlen])
    def if1(data: bytes):
        dev.bulkWrite(0x02, data, timeout=500)

    ctl(0, 2); ctl(0, 1); ctl(1, 1)
    if1(b"\xCC\x01\0\0\1\0\0\0A\0\0\0\xF8\xB3\xF7\0")
    if1(b'{"type":"openFile","data":{"mode":"r","path":"CameraFiles.zip"}}\0')
    if1(b"\xCC\x01\0\0\1\0\0\0\x33\0\0\0\xEF\xDB\xC1\xC1")
    if1(b'{"type":"readFile","data":{"streamIdentifier":10}}\0')
    ctl(1, 2, 2)
    print("[INFO] handshake OK – streaming on EP 0x85")
    return dev
