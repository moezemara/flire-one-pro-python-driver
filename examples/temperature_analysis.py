#!/usr/bin/env python3
"""
Temperature analysis example.

Analyzes thermal data and finds hot/cold spots.
"""

import cv2
import numpy as np
from flir_one import Camera


def analyze_thermal(thermal: np.ndarray) -> dict:
    """Analyze thermal image and extract statistics."""
    return {
        "min": thermal.min(),
        "max": thermal.max(),
        "mean": thermal.mean(),
        "median": np.median(thermal),
        "std": thermal.std(),
    }


def find_hotspot(thermal: np.ndarray) -> tuple:
    """Find the location of the hottest point."""
    max_val = thermal.max()
    max_loc = np.unravel_index(thermal.argmax(), thermal.shape)
    return max_loc, max_val


def find_coldspot(thermal: np.ndarray) -> tuple:
    """Find the location of the coldest point."""
    min_val = thermal.min()
    min_loc = np.unravel_index(thermal.argmin(), thermal.shape)
    return min_loc, min_val


def main():
    """Analyze thermal data in real-time."""
    print("FLIR Temperature Analysis")
    print("Press 'q' to quit")

    camera = Camera()

    for frame in camera.stream():
        if frame.thermal is None:
            continue

        # Analyze thermal data
        stats = analyze_thermal(frame.thermal)
        hot_loc, hot_val = find_hotspot(frame.thermal)
        cold_loc, cold_val = find_coldspot(frame.thermal)

        # Prepare display
        thermal_norm = cv2.normalize(
            frame.thermal, None, 0, 255, cv2.NORM_MINMAX
        ).astype('uint8')
        thermal_color = cv2.applyColorMap(thermal_norm, cv2.COLORMAP_INFERNO)

        # Upscale for better visualization
        thermal_display = cv2.resize(thermal_color, (480, 360))

        # Scale marker positions
        scale_y, scale_x = 6, 6  # 60*6=360, 80*6=480

        # Mark hotspot
        hot_y, hot_x = hot_loc
        cv2.circle(
            thermal_display,
            (hot_x * scale_x, hot_y * scale_y),
            10, (0, 0, 255), 2
        )
        cv2.putText(
            thermal_display,
            f"HOT: {hot_val}",
            (hot_x * scale_x + 15, hot_y * scale_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
        )

        # Mark coldspot
        cold_y, cold_x = cold_loc
        cv2.circle(
            thermal_display,
            (cold_x * scale_x, cold_y * scale_y),
            10, (255, 0, 0), 2
        )
        cv2.putText(
            thermal_display,
            f"COLD: {cold_val}",
            (cold_x * scale_x + 15, cold_y * scale_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1
        )

        # Display statistics
        y_offset = 20
        for key, value in stats.items():
            text = f"{key}: {value:.1f}"
            cv2.putText(
                thermal_display, text, (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
            y_offset += 20

        cv2.imshow("Temperature Analysis", thermal_display)

        # Also print to console
        print(f"\rFrame {frame.idx} | "
              f"Min: {stats['min']:6.1f} | "
              f"Max: {stats['max']:6.1f} | "
              f"Mean: {stats['mean']:6.1f} | "
              f"Std: {stats['std']:6.1f}",
              end="")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print()  # New line after loop
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
