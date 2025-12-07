"""
Frame assembler for FLIR One Pro camera.

Collects decoded slices and assembles them into complete frames.
Handles partial visible slices and ensures telemetry is properly
associated with frames.
"""
import collections

Frame = collections.namedtuple(
    "Frame",
    "idx ts packet_img agc_img telemetry edge_mask visible_img"
)


class FrameAssembler:
    """
    Assembles decoded slices into complete frames.

    The assembler collects slices of different types (thermal, visible,
    telemetry, etc.) and emits a complete Frame object when a frame
    boundary is detected (indicated by receiving a new sync marker).

    Attributes
    ----------
    idx : int
        Current frame index (increments with each complete frame)
    """

    def __init__(self):
        self._cur = {}
        self._idx = 0

    def _flush_frame(self):
        """
        Flush the current accumulated slices as a complete frame.

        Returns
        -------
        Frame
            Named tuple containing all frame components
        """
        self._idx += 1
        idx = self._idx

        # visible entry may be img or (img, tel)
        vis_entry = self._cur.pop("visible", None)
        if isinstance(vis_entry, tuple):
            visible_img, vis_tel = vis_entry
        else:
            visible_img, vis_tel = vis_entry, None

        telemetry = self._cur.pop("telemetry", None) or vis_tel

        frame = Frame(
            idx         = idx,
            ts          = self._cur.get("sync").ts_low
                          if "sync" in self._cur else None,
            packet_img  = self._cur.pop("packets",   None),
            agc_img     = self._cur.pop("agc",       None),
            telemetry   = telemetry,
            edge_mask   = self._cur.pop("edge_rle",  None),
            visible_img = visible_img,
        )
        self._cur.clear()
        return frame

    def push(self, label: str, obj):
        """
        Push a decoded slice into the assembler.

        Parameters
        ----------
        label : str
            Type of slice ('sync', 'packets', 'visible', 'telemetry',
            'agc', 'edge_rle')
        obj : any
            Decoded slice data (type depends on label)

        Returns
        -------
        Frame or None
            Returns a complete Frame when a frame boundary is detected,
            otherwise returns None
        """
        # ignore interim visible == None (partial JPEG)
        if label == "visible" and obj is None:
            return None

        # incoming SYNC when one already present → frame done
        if label == "sync" and "sync" in self._cur:
            return self._flush_frame()

        self._cur[label] = obj
        return None
