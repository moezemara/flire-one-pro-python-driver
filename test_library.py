#!/usr/bin/env python3
"""
Quick test script to verify the FLIR One Python library is working.

This script tests the library using the included test chunks.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from flir_one import Camera, CameraFrame
        from flir_one.utils import display, fuse, msx, palettes, fps
        from flir_one.decoders import packets, visible, telemetry
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_camera_offline():
    """Test camera with offline chunks."""
    print("\nTesting camera with test chunks...")
    try:
        from flir_one import Camera

        # Check if test chunks exist
        test_dir = Path("test_chunks")
        if not test_dir.exists():
            print("✗ test_chunks directory not found")
            return False

        # Try to stream a few frames
        camera = Camera(offline_dir=test_dir, repeat=1)
        frame_count = 0

        for frame in camera.stream():
            frame_count += 1
            print(f"  Frame {frame.idx}: ", end="")

            if frame.thermal is not None:
                print(f"Thermal {frame.thermal.shape} ", end="")
            if frame.visible is not None:
                print(f"Visible {frame.visible.shape} ", end="")
            if frame.telemetry is not None:
                print(f"Telemetry OK ", end="")
            print()

            if frame_count >= 3:  # Just test a few frames
                break

        if frame_count > 0:
            print(f"✓ Successfully streamed {frame_count} frames")
            return True
        else:
            print("✗ No frames received")
            return False

    except Exception as e:
        print(f"✗ Camera test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_display_utils():
    """Test display utilities."""
    print("\nTesting display utilities...")
    try:
        import numpy as np
        import cv2
        from flir_one.utils.palettes import colorize

        # Create dummy thermal data
        thermal = np.random.randint(0, 255, (60, 80), dtype=np.uint8)

        # Test colorization
        colored = colorize(thermal, "inferno")
        assert colored.shape == (60, 80, 3), "Unexpected output shape"

        print("✓ Display utilities working")
        return True

    except Exception as e:
        print(f"✗ Display utils test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("FLIR One Python Library Test")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Camera (offline)", test_camera_offline()))
    results.append(("Display utilities", test_display_utils()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Library is ready to use.")
        print("\nNext steps:")
        print("  - Try the CLI: python -m flir_one test_chunks/")
        print("  - Run examples: cd examples && python simple_viewer.py")
        print("  - Read GETTING_STARTED.md for more info")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
