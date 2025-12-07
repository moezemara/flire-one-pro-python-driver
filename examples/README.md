# FLIR One Python Examples

This directory contains example scripts demonstrating various use cases of the FLIR One Python library.

## Examples

### [simple_viewer.py](simple_viewer.py)

Basic camera viewer that displays thermal and visible feeds.

```bash
python simple_viewer.py
```

**Features:**
- Real-time thermal and visible display
- Thermal colorization with INFERNO palette
- Battery status display

---

### [save_thermal.py](save_thermal.py)

Capture and save thermal images on demand.

```bash
python save_thermal.py
```

**Controls:**
- Press `s` to save current thermal image
- Press `q` to quit

**Output:**
- `saved_thermal/thermal_raw_NNNN.npy` - Raw 16-bit thermal data
- `saved_thermal/thermal_color_NNNN.png` - Colorized visualization

---

### [temperature_analysis.py](temperature_analysis.py)

Real-time temperature analysis with hot/cold spot detection.

```bash
python temperature_analysis.py
```

**Features:**
- Min/max/mean/median/std statistics
- Hotspot marker (red)
- Coldspot marker (blue)
- Real-time console output

---

### [record_session.py](record_session.py)

Record raw USB chunks and replay them later.

```bash
# Record 200 frames
python record_session.py record ./my_recording 200

# Replay once
python record_session.py replay ./my_recording

# Replay infinitely
python record_session.py replay ./my_recording -1
```

**Use Cases:**
- Offline analysis
- Testing without camera
- Sharing datasets

---

## Running Examples

### Requirements

Install the library first:

```bash
pip install -e ..
```

Or if installed from PyPI:

```bash
pip install flir-one-python
```

### USB Permissions (Linux)

Set up udev rules:

```bash
sudo tee /etc/udev/rules.d/99-flir-one.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="09cb", ATTR{idProduct}=="1996", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Running

```bash
cd examples
python simple_viewer.py
```

## Tips

- All examples use OpenCV for display (`cv2.imshow`)
- Press `q` to quit in all viewers
- Raw thermal data is uint16 with 14-bit values (0-16383)
- Visible images are BGR format (OpenCV convention)

## Custom Examples

Want to create your own? Here's a minimal template:

```python
from flir_one import Camera

camera = Camera()

for frame in camera.stream():
    if frame.thermal is not None:
        # Your processing here
        print(f"Frame {frame.idx}")
```

## Offline Testing

If you don't have a FLIR camera, you can use pre-recorded chunks:

```bash
# Use the chunks from the original project
cd examples
python simple_viewer.py --offline ../flir/chunks
```

(Note: Adjust the path based on where you have saved chunks)
