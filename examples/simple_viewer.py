#!/usr/bin/env python3
"""
Simple FLIR camera viewer example.

Shows thermal and visible camera feeds in real-time.
"""

import cv2
from flir_one import Camera


def main():
    """Simple camera viewer."""
    print("FLIR One Simple Viewer")
    print("Press 'q' to quit")

    camera = Camera()

    for frame in camera.stream():
        # Display thermal (if available)
        if frame.thermal is not None:
            # Normalize to 8-bit for display
            thermal_norm = cv2.normalize(
                frame.thermal, None, 0, 255, cv2.NORM_MINMAX
            ).astype('uint8')

            # Apply colormap
            thermal_color = cv2.applyColorMap(thermal_norm, cv2.COLORMAP_INFERNO)

            # Resize for better viewing
            thermal_display = cv2.resize(
                thermal_color, (320, 240),
                interpolation=cv2.INTER_LINEAR
            )

            cv2.imshow("Thermal", thermal_display)

        # Display visible (if available)
        if frame.visible is not None:
            # Resize for display
            visible_display = cv2.resize(
                frame.visible, (640, 480),
                interpolation=cv2.INTER_AREA
            )

            cv2.imshow("Visible", visible_display)

        # Print telemetry
        if frame.telemetry is not None and frame.telemetry.battery_percent:
            print(f"Frame {frame.idx}: Battery {frame.telemetry.battery_percent:.0f}%")

        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
