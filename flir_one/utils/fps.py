"""
Lightweight FPS meter with rolling average.

Tracks frame rate over a window of recent frames.
"""
from __future__ import annotations
import collections, time

__all__ = ["FPSMeter"]


class FPSMeter:
    """
    Frame rate meter with rolling average.

    Maintains a rolling window of frame times to compute
    a smoothed FPS estimate.

    Parameters
    ----------
    max_samples : int
        Maximum number of samples to keep (default: 30)
    """

    def __init__(self, max_samples: int = 30) -> None:
        self.samples: collections.deque[float] = collections.deque(maxlen=max_samples)
        self._last_t: float | None = None

    def update(self) -> float:
        """
        Update meter with current frame.

        Call once per rendered frame.

        Returns
        -------
        float
            Current average FPS
        """
        now = time.time()
        if self._last_t is not None:
            self.samples.append(1.0 / (now - self._last_t))
        self._last_t = now

        return sum(self.samples) / len(self.samples) if self.samples else 0.0
