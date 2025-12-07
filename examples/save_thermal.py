#!/usr/bin/env python3
"""
Save thermal images example.

Captures thermal images and saves them as PNG files.
"""

import cv2
import numpy as np
from pathlib import Path
from flir_one import Camera


def main():
    """Save thermal images on keypress."""
    print("FLIR Thermal Image Saver")
    print("Press 's' to save, 'q' to quit")

    # Create output directory
    output_dir = Path("saved_thermal")
    output_dir.mkdir(exist_ok=True)

    camera = Camera()
    save_count = 0

    for frame in camera.stream():
        if frame.thermal is None:
            continue

        # Prepare thermal for display
        thermal_norm = cv2.normalize(
            frame.thermal, None, 0, 255, cv2.NORM_MINMAX
        ).astype('uint8')
        thermal_color = cv2.applyColorMap(thermal_norm, cv2.COLORMAP_INFERNO)
        thermal_display = cv2.resize(thermal_color, (320, 240))

        cv2.imshow("Thermal (press 's' to save)", thermal_display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            # Save both raw data and colored visualization
            save_count += 1

            # Save raw 16-bit data
            raw_path = output_dir / f"thermal_raw_{save_count:04d}.npy"
            np.save(raw_path, frame.thermal)

            # Save colorized version
            color_path = output_dir / f"thermal_color_{save_count:04d}.png"
            cv2.imwrite(str(color_path), thermal_color)

            print(f"Saved image {save_count}: {raw_path} and {color_path}")

            # Show min/max values
            print(f"  Temperature range: {frame.thermal.min()} - {frame.thermal.max()}")

        elif key == ord('q'):
            break

    cv2.destroyAllWindows()
    print(f"\nTotal images saved: {save_count}")


if __name__ == "__main__":
    main()
