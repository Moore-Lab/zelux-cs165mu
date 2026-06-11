"""Driver/API for the Thorlabs Zelux CS165MU (USB3, mono).

Wraps the Thorlabs Scientific Camera SDK (``thorlabs_tsi_sdk``) behind a small,
GUI-friendly interface: connect, configure (exposure, frame rate), grab single
frames, and stream.

The public surface here is intended to mirror the other camera modules so that
``xsphere-camera-dock`` can drive every camera through the same calls.
"""

from __future__ import annotations

from typing import Iterator, Optional

# from thorlabs_tsi_sdk.tl_camera import TLCameraSDK  # enable once the TSI SDK is installed


class ZeluxCS165MU:
    """Thin driver around a single Thorlabs Zelux CS165MU.

    Parameters
    ----------
    serial:
        Serial number of the target camera. If ``None``, the first device found
        is used.
    """

    def __init__(self, serial: Optional[str] = None) -> None:
        self.serial = serial
        self._sdk = None     # will hold the TLCameraSDK context
        self._camera = None  # will hold the opened TLCamera

    # --- lifecycle ---------------------------------------------------------
    def connect(self) -> None:
        """Open the SDK + camera and prepare it for acquisition."""
        raise NotImplementedError

    def disconnect(self) -> None:
        """Stop acquisition (if running), close the camera, and dispose the SDK."""
        raise NotImplementedError

    # --- configuration -----------------------------------------------------
    def set_exposure(self, microseconds: float) -> None:
        """Set exposure time in microseconds."""
        raise NotImplementedError

    def set_frame_rate(self, fps: float) -> None:
        """Set the target acquisition frame rate in frames per second."""
        raise NotImplementedError

    # --- acquisition -------------------------------------------------------
    def grab(self):
        """Grab and return a single frame as a 2-D ``numpy`` array."""
        raise NotImplementedError

    def frames(self) -> Iterator:
        """Yield frames continuously while acquisition is running."""
        raise NotImplementedError

    # --- context manager ---------------------------------------------------
    def __enter__(self) -> "ZeluxCS165MU":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()
