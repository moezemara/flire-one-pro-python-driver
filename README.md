# FLIR One Python

A clean, easy-to-use Python library for the **FLIR One Pro Gen-3** thermal camera.

## Features

- 🔥 **Simple API** - Get started with just a few lines of code
- 📷 **Dual Cameras** - Access both thermal (Lepton 3) and visible cameras
- 🎨 **Multiple Color Palettes** - Inferno, Turbo, Hot, Jet, and more
- 🔋 **Telemetry** - Battery status, temperature readings, and camera state
- 💾 **Record & Replay** - Save raw USB data for offline analysis
- 🖼️ **Image Fusion** - Blend thermal and visible images with MSX edge overlay
- ⚡ **High Performance** - Full 14-bit radiometric thermal data (60×80 → 160×120)

## Installation

### From PyPI (when published)

```bash
pip install flir-one-python
```

### From Source

```bash
git clone https://github.com/yourusername/flir-one-python.git
cd flir-one-python
pip install -e .
```

### USB Permissions (Linux)

On Linux, you need to set up udev rules to access the FLIR camera without root:

```bash
# Create udev rule
sudo tee /etc/udev/rules.d/99-flir-one.rules << EOF
# FLIR One Pro Gen-3
SUBSYSTEM=="usb", ATTR{idVendor}=="09cb", ATTR{idProduct}=="1996", MODE="0666"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Quick Start

### Live Camera Streaming

```python
from flir_one import Camera

# Create camera instance
camera = Camera()

# Stream frames
for frame in camera.stream():
    if frame.thermal is not None:
        print(f"Thermal: {frame.thermal.shape}")  # (60, 80) uint16
        print(f"Range: {frame.thermal.min()} - {frame.thermal.max()}")

    if frame.visible is not None:
        print(f"Visible: {frame.visible.shape}")  # (1080, 1440, 3) BGR

    if frame.telemetry is not None:
        print(f"Battery: {frame.telemetry.battery_percent}%")
```

### Offline Playback

```python
from flir_one import Camera

# Replay saved chunks
camera = Camera(offline_dir="./saved_chunks", repeat=-1)  # -1 = infinite loop

for frame in camera.stream():
    # Process frames
    pass
```

### Save Raw Data

```python
from flir_one import Camera

# Save USB chunks while streaming
camera = Camera(save_chunks=True, chunk_save_dir="./my_recording")

for frame in camera.stream():
    # Frames are automatically saved to ./my_recording/
    pass
```

## Command-Line Interface

The library includes a built-in viewer for quick testing:

```bash
# Live camera view
python -m flir_one --live

# Save chunks while viewing
python -m flir_one --live --save-chunks

# Replay saved chunks
python -m flir_one ./saved_chunks/

# Replay infinitely
python -m flir_one ./saved_chunks/ --repeat -1

# Customize display
python -m flir_one --live --palette turbo --alpha 0.5
```

### CLI Options

```
--live                 Stream from connected camera
--save-chunks          Save raw USB data
--chunk-dir DIR        Chunks directory (default: ./chunks)
--repeat N             Repeat offline chunks N times (-1 = infinite)
--palette PALETTE      Color palette (inferno, turbo, hot, jet)
--alpha ALPHA          Thermal blend factor for fused view (0.0-1.0)
--no-telemetry         Hide telemetry overlay
```

Press `q` to quit, `s` to save screenshot.

## Frame Data Structure

Each frame contains:

```python
@dataclass
class CameraFrame:
    idx: int                              # Frame number
    thermal: Optional[np.ndarray]         # Thermal data (60×80 uint16)
    visible: Optional[np.ndarray]         # Visible image (BGR)
    telemetry: Optional[Telemetry]        # Camera telemetry
    edge_mask: Optional[np.ndarray]       # Edge mask for MSX
    timestamp: Optional[int]              # Frame timestamp
```

### Telemetry Data

```python
@dataclass
class Telemetry:
    battery_voltage: Optional[float]      # Battery voltage (V)
    battery_percent: Optional[float]      # Battery percentage (0-100)
    shutter_tempK: Optional[float]        # Shutter temp (Kelvin)
    aux_tempK: Optional[float]            # Auxiliary temp (Kelvin)
    shutter_state: Optional[str]          # Shutter state
    ffc_state: Optional[str]              # Flat-field correction state
```

## Advanced Usage

### Display Utilities

```python
from flir_one import Camera
from flir_one.utils.display import prepare_displays
from flir_one.utils.fps import FPSMeter
import cv2

camera = Camera()
fps_meter = FPSMeter()

for frame in camera.stream():
    # Prepare display images
    displays = prepare_displays(
        frame,
        alpha=0.4,           # Thermal blend amount
        palette="inferno",   # Color palette
        fps={"thermal": fps_meter.update()},
    )

    # Show thermal, visible, and fused views
    for name, img in displays.items():
        cv2.imshow(name, img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

### Image Fusion

```python
from flir_one.utils.fuse import fuse_visible_and_thermal

# Blend thermal over visible
fused = fuse_visible_and_thermal(
    visible_bgr=frame.visible,
    thermal_raw=frame.thermal,
    alpha=0.4,
    palette="inferno"
)
```

### MSX Edge Overlay

```python
from flir_one.utils.msx import overlay

# Add visible edges to thermal image
if frame.edge_mask is not None:
    thermal_with_edges = overlay(
        thermal_colorized,
        frame.edge_mask,
        colour=(0, 255, 0),  # Green edges
        alpha=0.4
    )
```

## Technical Details

### Camera Specifications

- **Model**: FLIR One Pro Gen-3
- **Thermal Sensor**: Lepton 3 (60×80 pixels, 14-bit radiometric)
- **Visible Camera**: 1080×1440 JPEG
- **USB**: VID=0x09CB, PID=0x1996
- **Frame Rate**: ~8.7 Hz
- **Connection**: USB (libusb1)

### Thermal Data Format

- Raw thermal data: 60×80 pixels, uint16 (14-bit values)
- Display rendering: Auto-scaled to 160×120 with colormap
- Radiometric: Full temperature data preserved

### USB Protocol

The library implements the complete FLIR One Pro USB protocol:

1. **Handshake** - Initialize camera connection
2. **Slice Streaming** - Receive 32KB USB bulk transfers
3. **Slice Classification** - Identify data types (thermal, visible, telemetry, etc.)
4. **Decoding** - Parse VoSPI packets, JPEG, JSON telemetry
5. **Frame Assembly** - Combine slices into complete frames

## Architecture

```
flir_one/
├── camera.py              # High-level Camera API
├── cli.py                 # Command-line interface
├── usb/
│   ├── handshake.py       # USB initialization
│   ├── io.py              # USB I/O and chunk management
│   ├── slice_types.py     # Slice classification
│   └── assembler.py       # Frame assembly
├── decoders/
│   ├── packets.py         # VoSPI thermal decoder
│   ├── visible.py         # JPEG visible decoder
│   ├── telemetry.py       # JSON telemetry decoder
│   ├── sync.py            # Sync marker decoder
│   ├── agc.py             # AGC slice decoder
│   └── edge_rle.py        # RLE edge mask decoder
├── utils/
│   ├── display.py         # Display rendering
│   ├── fuse.py            # Image fusion
│   ├── msx.py             # MSX edge overlay
│   ├── palettes.py        # Color palettes
│   └── fps.py             # FPS meter
└── palettes/              # Palette data files
```

## Examples

See the [examples/](examples/) directory for complete working examples:

- [examples/simple_viewer.py](examples/simple_viewer.py) - Basic camera viewer
- [examples/save_thermal.py](examples/save_thermal.py) - Save thermal images
- [examples/temperature_analysis.py](examples/temperature_analysis.py) - Analyze temperature data
- [examples/record_session.py](examples/record_session.py) - Record and replay sessions

## Requirements

- Python >= 3.8
- numpy >= 1.20.0
- opencv-python >= 4.5.0
- libusb1 >= 2.0.0

### System Requirements

- **Linux**: libusb-1.0 (`sudo apt install libusb-1.0-0-dev`)
- **macOS**: libusb (`brew install libusb`)
- **Windows**: libusb drivers (use Zadig to install WinUSB driver)

## Troubleshooting

### Camera not detected

1. Check USB connection
2. Verify udev rules (Linux)
3. Install WinUSB driver with Zadig (Windows)
4. Check device appears: `lsusb | grep 09cb` (Linux)

### Permission denied

```bash
# Linux: Add user to plugdev group
sudo usermod -a -G plugdev $USER
# Log out and back in
```

### Import errors

```bash
# Reinstall dependencies
pip install --upgrade numpy opencv-python libusb1
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on reverse-engineering work of the FLIR One Pro USB protocol
- Inspired by community FLIR One projects
- Built for open-source thermal imaging research

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/moezemara/flire-one-pro-python-driver/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/moezemara/flire-one-pro-python-driver/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/moezemara/flire-one-pro-python-driver/wiki)
