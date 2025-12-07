#!/usr/bin/env python3
"""
Record and replay session example.

Shows how to record raw USB chunks and replay them later.
"""

import sys
from pathlib import Path
from flir_one import Camera


def record_session(output_dir: str, duration_frames: int = 100):
    """Record a session to disk."""
    print(f"Recording {duration_frames} frames to {output_dir}/")
    print("Press Ctrl+C to stop early")

    camera = Camera(save_chunks=True, chunk_save_dir=output_dir)

    try:
        for frame in camera.stream():
            print(f"\rRecorded frame {frame.idx}/{duration_frames}", end="")

            if frame.idx >= duration_frames:
                break

    except KeyboardInterrupt:
        print("\nRecording stopped by user")

    print(f"\nRecording complete! Saved to {output_dir}/")


def replay_session(input_dir: str, repeat: int = 1):
    """Replay a recorded session."""
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: {input_dir} does not exist")
        sys.exit(1)

    if repeat == -1:
        print(f"Replaying {input_dir}/ infinitely (press Ctrl+C to stop)")
    else:
        print(f"Replaying {input_dir}/ {repeat} time(s)")

    camera = Camera(offline_dir=input_dir, repeat=repeat)

    try:
        for frame in camera.stream():
            print(f"\rPlaying frame {frame.idx}", end="")

            # Add your processing here
            # ...

    except KeyboardInterrupt:
        print("\nPlayback stopped by user")

    print("\nPlayback complete!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Record:  python record_session.py record <output_dir> [frames]")
        print("  Replay:  python record_session.py replay <input_dir> [repeat]")
        print()
        print("Examples:")
        print("  python record_session.py record ./my_session 200")
        print("  python record_session.py replay ./my_session")
        print("  python record_session.py replay ./my_session -1  # infinite loop")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "record":
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "./recorded_session"
        frames = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        record_session(output_dir, frames)

    elif mode == "replay":
        input_dir = sys.argv[2] if len(sys.argv) > 2 else "./recorded_session"
        repeat = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        replay_session(input_dir, repeat)

    else:
        print(f"Unknown mode: {mode}")
        print("Use 'record' or 'replay'")
        sys.exit(1)


if __name__ == "__main__":
    main()
