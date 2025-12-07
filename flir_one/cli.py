#!/usr/bin/env python3
"""
Command-line interface for FLIR One Pro camera.

Provides live camera preview and offline chunk playback with
thermal, visible, and fused display modes.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np

from .camera import Camera
from .utils.display import prepare_displays
from .utils.fps import FPSMeter

__all__ = ["main"]


def format_telemetry(tel) -> Dict[str, Any]:
    """Format telemetry object as a display dictionary."""
    if tel is None:
        return {}

    data = {}
    if tel.battery_percent is not None:
        data["BattPct"] = f"{tel.battery_percent:.0f}%"
    if tel.battery_voltage is not None:
        data["BattV"] = f"{tel.battery_voltage:.2f}V"
    if tel.shutter_tempK is not None:
        data["ShutterK"] = f"{tel.shutter_tempK:.1f}"
    if tel.aux_tempK is not None:
        data["AuxK"] = f"{tel.aux_tempK:.1f}"
    if tel.shutter_state:
        data["Shutter"] = tel.shutter_state
    if tel.ffc_state:
        data["FFC"] = tel.ffc_state

    return data


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="FLIR One Pro camera viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stream from live camera
  python -m flir_one.cli --live

  # Save chunks while streaming
  python -m flir_one.cli --live --save-chunks

  # Replay saved chunks
  python -m flir_one.cli chunks/

  # Replay chunks infinitely
  python -m flir_one.cli chunks/ --repeat -1
        """
    )

    parser.add_argument(
        "chunk_path",
        nargs="?",
        default=None,
        help="Directory containing saved chunks (offline mode)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Stream from connected FLIR camera"
    )
    parser.add_argument(
        "--save-chunks",
        action="store_true",
        help="Save raw USB chunks to disk (live mode only)"
    )
    parser.add_argument(
        "--chunk-dir",
        default="./chunks",
        help="Directory to save/load chunks (default: ./chunks)"
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Repeat offline chunks N times (-1 for infinite)"
    )
    parser.add_argument(
        "--palette",
        default="inferno",
        choices=["inferno", "turbo", "hot", "jet"],
        help="Thermal color palette"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.4,
        help="Thermal blend alpha for fused view (0.0-1.0)"
    )
    parser.add_argument(
        "--no-telemetry",
        action="store_true",
        help="Hide telemetry overlay"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.live and not args.chunk_path:
        parser.error("Either specify --live or provide a chunk_path")

    # Create camera
    print("[FLIR] Initializing camera...")
    if args.live:
        camera = Camera(
            save_chunks=args.save_chunks,
            chunk_save_dir=args.chunk_dir
        )
        print("[FLIR] Streaming from live camera")
        if args.save_chunks:
            print(f"[FLIR] Saving chunks to {args.chunk_dir}/")
    else:
        chunk_path = Path(args.chunk_path)
        if not chunk_path.exists():
            print(f"[ERROR] Chunk directory not found: {chunk_path}", file=sys.stderr)
            sys.exit(1)

        camera = Camera(
            offline_dir=chunk_path,
            repeat=args.repeat
        )
        print(f"[FLIR] Playing back chunks from {chunk_path}/")

    # FPS meters for each display
    fps_meters = {
        "visible": FPSMeter(),
        "thermal": FPSMeter(),
        "fused": FPSMeter()
    }

    # Telemetry overlay configuration
    telemetry_cfg = {
        "visible": {"single_line": False},
        "thermal": {"keys": ["BattPct"], "single_line": True},
        "fused": {"single_line": False},
    }

    print("[FLIR] Press 'q' to quit, 's' to save screenshot")
    print("[FLIR] Streaming...")

    try:
        for frame in camera.stream():
            # Build display outputs
            fps_dict = {k: v.update() for k, v in fps_meters.items()}

            telemetry_data = None
            if not args.no_telemetry:
                telemetry_data = format_telemetry(frame.telemetry)

            # Convert internal frame to assembler.Frame format
            # This is a bit hacky but allows reuse of prepare_displays
            from collections import namedtuple
            InternalFrame = namedtuple(
                "Frame",
                "idx ts packet_img agc_img telemetry edge_mask visible_img"
            )

            internal_frame = InternalFrame(
                idx=frame.idx,
                ts=frame.timestamp,
                packet_img=frame.thermal,
                agc_img=None,
                telemetry=frame.telemetry,
                edge_mask=frame.edge_mask,
                visible_img=frame.visible,
            )

            displays = prepare_displays(
                internal_frame,
                alpha=args.alpha,
                palette=args.palette,
                fps=fps_dict,
                telemetry_data=telemetry_data,
                telemetry_show=telemetry_cfg,
            )

            # Show available displays
            for name, img in displays.items():
                cv2.imshow(f"FLIR - {name.capitalize()}", img)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n[FLIR] Quit requested")
                break
            elif key == ord('s'):
                # Save screenshot
                timestamp = frame.idx
                for name, img in displays.items():
                    filename = f"flir_{name}_{timestamp}.png"
                    cv2.imwrite(filename, img)
                    print(f"[FLIR] Saved {filename}")

    except KeyboardInterrupt:
        print("\n[FLIR] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cv2.destroyAllWindows()
        print("[FLIR] Shutdown complete")


if __name__ == "__main__":
    main()
