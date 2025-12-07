# Getting Started with FLIR One Python

Quick start guide to get you up and running with the FLIR One Python library.

## Installation

### 1. Install from source

```bash
cd flir-one-python
pip install -e .
```

This installs the library in "editable" mode, so you can modify the code if needed.

### 2. Verify installation

```bash
python -c "from flir_one import Camera; print('Success!')"
```

## Testing Without a Camera

The library includes 109 test chunks for offline testing. Try them out:

```bash
# Using the CLI
python -m flir_one test_chunks/

# Or in Python
from flir_one import Camera

camera = Camera(offline_dir="test_chunks", repeat=-1)  # Loop forever
for frame in camera.stream():
    print(f"Frame {frame.idx}: Thermal shape {frame.thermal.shape if frame.thermal is not None else 'None'}")
```

## Quick Examples

### 1. Simple Live Stream

```python
from flir_one import Camera
import cv2

camera = Camera()

for frame in camera.stream():
    if frame.thermal is not None:
        # Normalize and colorize thermal data
        thermal_norm = cv2.normalize(frame.thermal, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
        thermal_color = cv2.applyColorMap(thermal_norm, cv2.COLORMAP_INFERNO)

        cv2.imshow("Thermal", thermal_color)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
```

### 2. Save Recording

```python
from flir_one import Camera

# Save raw USB chunks for later playback
camera = Camera(save_chunks=True, chunk_save_dir="./my_recording")

for frame in camera.stream():
    print(f"Recording frame {frame.idx}...")
    if frame.idx >= 100:  # Record 100 frames
        break
```

### 3. Access Thermal Data

```python
from flir_one import Camera
import numpy as np

camera = Camera(offline_dir="test_chunks")

for frame in camera.stream():
    if frame.thermal is not None:
        # Thermal data is uint16 (14-bit values)
        print(f"Min: {frame.thermal.min()}")
        print(f"Max: {frame.thermal.max()}")
        print(f"Mean: {frame.thermal.mean():.1f}")

        # Access specific pixel
        center_y, center_x = 30, 40  # 60×80 image
        pixel_value = frame.thermal[center_y, center_x]
        print(f"Center pixel: {pixel_value}")

        break  # Just check first frame
```

## Command Line Interface

The library includes a ready-to-use CLI:

```bash
# Live camera (requires camera connected)
python -m flir_one --live

# Test with included chunks
python -m flir_one test_chunks/

# Loop test chunks infinitely
python -m flir_one test_chunks/ --repeat -1

# Save while viewing live
python -m flir_one --live --save-chunks --chunk-dir ./my_session

# Customize palette
python -m flir_one test_chunks/ --palette turbo --alpha 0.6
```

### CLI Controls

- `q` - Quit
- `s` - Save screenshot

## Example Scripts

Check out the [examples/](examples/) directory:

```bash
cd examples

# Simple viewer
python simple_viewer.py

# Temperature analysis
python temperature_analysis.py

# Save thermal images
python save_thermal.py

# Record and replay
python record_session.py record ./my_data 200
python record_session.py replay ./my_data
```

## Understanding Thermal Data

### Data Format

- **Shape**: (60, 80) for raw thermal
- **Type**: uint16
- **Range**: 0-16383 (14-bit radiometric data)
- **Units**: Raw sensor values (not calibrated to temperature)

### Display Pipeline

1. **Normalize**: Scale to 0-255 for display
2. **Colorize**: Apply false-color palette
3. **Resize**: Upscale for better viewing

```python
import cv2

# Convert thermal to displayable image
thermal_norm = cv2.normalize(frame.thermal, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
thermal_color = cv2.applyColorMap(thermal_norm, cv2.COLORMAP_INFERNO)
thermal_display = cv2.resize(thermal_color, (320, 240))
```

## USB Permissions (Linux Only)

If using a real camera on Linux, set up udev rules:

```bash
sudo tee /etc/udev/rules.d/99-flir-one.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="09cb", ATTR{idProduct}=="1996", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger

# Verify camera is detected
lsusb | grep 09cb
```

## Troubleshooting

### "No module named 'flir_one'"

Install the library:
```bash
pip install -e .
```

### "USB device not found" (Live mode)

1. Check camera is connected: `lsusb | grep 09cb` (Linux)
2. Verify udev rules (Linux)
3. Try offline mode with test chunks first

### Import errors

```bash
pip install --upgrade numpy opencv-python libusb1
```

### Windows USB drivers

On Windows, you may need to install WinUSB drivers using [Zadig](https://zadig.akeo.ie/):

1. Download and run Zadig
2. Options → List All Devices
3. Select "FLIR One" (VID: 09CB, PID: 1996)
4. Select WinUSB driver
5. Click "Replace Driver"

## Next Steps

- Read the full [README.md](README.md)
- Explore [examples/](examples/)
- Check the API documentation
- Join the community discussions

## Common Patterns

### Find hottest pixel

```python
max_val = frame.thermal.max()
max_pos = divmod(frame.thermal.argmax(), frame.thermal.shape[1])
print(f"Hottest pixel at {max_pos}: {max_val}")
```

### Region of interest

```python
# Extract center 20×20 region
y, x = 20, 30  # Top-left corner
roi = frame.thermal[y:y+20, x:x+20]
print(f"ROI mean: {roi.mean():.1f}")
```

### Save as numpy array

```python
import numpy as np

np.save("thermal_frame.npy", frame.thermal)

# Load later
loaded = np.load("thermal_frame.npy")
```

## Support

- 📖 Documentation: [README.md](README.md)
- 💡 Examples: [examples/](examples/)
- 🐛 Issues: GitHub Issues (when published)

Happy thermal imaging! 🔥📷
