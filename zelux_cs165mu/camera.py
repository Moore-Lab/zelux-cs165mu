"""Driver/API for the Thorlabs Zelux CS165MU (USB3, mono, 1.6 MP).

Wraps the Thorlabs Scientific Camera SDK (``thorlabs_tsi_sdk``) behind the same
small, GUI-friendly interface the other camera modules expose, so that
``xsphere-camera-dock`` can drive every camera through identical calls
(``connect`` / ``disconnect`` / ``set_exposure`` / ``set_frame_rate`` /
``grab`` / ``frames``). The public surface here mirrors ``BaslerACA1440``.

Backend notes
-------------
* The ``thorlabs_tsi_sdk`` Python package is **not** on PyPI. It ships in the
  Thorlabs "Scientific Camera Support" / Windows SDK download (a wheel under the
  Python Toolkit). Install that wheel into your environment.
* The package loads native DLLs (``thorlabs_tsi_camera_sdk.dll`` & friends) at
  import time, so their directory must be on the DLL search path. This module
  adds it automatically (see :func:`_add_dll_directory`): it honours the
  ``THORLABS_TSI_DLL_DIR`` environment variable and otherwise falls back to the
  default ThorCam install directory. The SDK import is therefore deferred until
  :meth:`connect`, so ``import zelux_cs165mu`` works even on machines without the
  SDK installed (e.g. for the dock to inspect the interface).

Pixel format
------------
Unlike the Basler driver (Mono8 ``uint8``), frames here are **``uint16``** — the
Zelux digitises to ``bit_depth`` bits packed in the low bits of each 16-bit
sample. Callers that need 8-bit (e.g. for display) should scale by
``bit_depth``; the test GUI does this.
"""

from __future__ import annotations

import os
from time import perf_counter
from typing import Iterator, Optional, Tuple

import numpy as np

# Default location of the Thorlabs native DLLs on a standard ThorCam install.
_DEFAULT_DLL_DIR = r"C:\Program Files\Thorlabs\Scientific Imaging\ThorCam"


def _add_dll_directory() -> None:
    """Put the Thorlabs native-DLL directory on the search path.

    Honours ``THORLABS_TSI_DLL_DIR`` if set, else falls back to the default
    ThorCam install directory. No-op if the directory cannot be found (the
    subsequent SDK import will then raise a clear error).
    """
    dll_dir = os.environ.get("THORLABS_TSI_DLL_DIR", _DEFAULT_DLL_DIR)
    if os.path.isdir(dll_dir):
        try:
            os.add_dll_directory(dll_dir)  # Python 3.8+; the SDK loads via ctypes
        except (OSError, AttributeError):
            pass
        # Also prepend to PATH for any helper DLLs resolved the old way.
        os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")


class ZeluxCS165MU:
    """Thin driver around a single Thorlabs Zelux CS165MU.

    Parameters
    ----------
    serial:
        Serial number of the target camera. If ``None``, the first discovered
        device is used.

    Notes
    -----
    The Thorlabs SDK allows only one ``TLCameraSDK`` instance at a time. Each
    driver instance owns its own SDK handle between :meth:`connect` and
    :meth:`disconnect`; don't hold two connected drivers in one process.
    """

    def __init__(self, serial: Optional[str] = None) -> None:
        self.serial = serial
        self._sdk = None      # TLCameraSDK
        self._camera = None   # TLCamera

    # --- lifecycle ---------------------------------------------------------
    def connect(self) -> None:
        """Open the SDK + camera and prepare it for continuous acquisition."""
        _add_dll_directory()
        try:
            from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
            from thorlabs_tsi_sdk.tl_camera_enums import OPERATION_MODE
        except (ImportError, OSError) as exc:  # OSError: DLLs not found
            raise RuntimeError(
                "Could not load the Thorlabs SDK (thorlabs_tsi_sdk). Install the "
                "wheel from the Thorlabs Scientific Camera SDK and ensure the "
                "native DLLs are discoverable (set THORLABS_TSI_DLL_DIR or install "
                "ThorCam). Original error: " + str(exc)
            ) from exc

        self._sdk = TLCameraSDK()
        serials = self._sdk.discover_available_cameras()
        if not serials:
            self._sdk.dispose()
            self._sdk = None
            raise RuntimeError("No Thorlabs cameras found.")

        target = str(self.serial) if self.serial else serials[0]
        if target not in serials:
            available = ", ".join(serials)
            self._sdk.dispose()
            self._sdk = None
            raise RuntimeError(f"Camera {target} not found. Available: {available}")

        self._camera = self._sdk.open_camera(target)

        # Free-running continuous video: software-triggered, unlimited frames.
        self._camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED
        self._camera.frames_per_trigger_zero_for_unlimited = 0
        self._camera.image_poll_timeout_ms = 1000

        # Decouple frame rate from exposure where the model supports it.
        try:
            if self._camera.frame_rate_control_value_range.max > 0:
                self._camera.is_frame_rate_control_enabled = True
        except Exception:
            pass  # frame-rate control not available on this firmware

    def disconnect(self) -> None:
        """Disarm (if armed), close the camera, and dispose the SDK."""
        try:
            if self._camera is not None:
                if self._camera.is_armed:
                    self._camera.disarm()
                self._camera.dispose()
        finally:
            self._camera = None
            if self._sdk is not None:
                self._sdk.dispose()
                self._sdk = None

    @property
    def is_connected(self) -> bool:
        return self._camera is not None

    def _require(self):
        if self._camera is None:
            raise RuntimeError("Camera is not connected. Call connect() first.")
        return self._camera

    # --- device info -------------------------------------------------------
    @property
    def device_info(self) -> dict:
        cam = self._require()
        return {
            "model": cam.model,
            "serial": cam.serial_number,
            "vendor": "Thorlabs",
        }

    def sensor_size(self) -> Tuple[int, int]:
        """Return ``(width, height)`` of the current image region."""
        cam = self._require()
        return int(cam.image_width_pixels), int(cam.image_height_pixels)

    @property
    def bit_depth(self) -> int:
        """Significant bits per pixel in the (16-bit) image buffer."""
        return int(self._require().bit_depth)

    # --- configuration -----------------------------------------------------
    def set_exposure(self, microseconds: float) -> None:
        """Set exposure time in microseconds (clamped to the valid range)."""
        cam = self._require()
        rng = cam.exposure_time_range_us
        value = int(round(min(max(microseconds, rng.min), rng.max)))
        cam.exposure_time_us = value

    def get_exposure(self) -> float:
        return float(self._require().exposure_time_us)

    def exposure_range(self) -> Tuple[float, float]:
        rng = self._require().exposure_time_range_us
        return float(rng.min), float(rng.max)

    def set_frame_rate(self, fps: float) -> None:
        """Set the target acquisition frame rate in frames per second.

        No-op if the connected model doesn't support frame-rate control.
        """
        cam = self._require()
        rng = cam.frame_rate_control_value_range
        if rng.max <= 0:
            return
        if not cam.is_frame_rate_control_enabled:
            cam.is_frame_rate_control_enabled = True
        cam.frame_rate_control_value = float(min(max(fps, rng.min), rng.max))

    def get_frame_rate(self) -> float:
        """Target frame rate (what we asked for)."""
        cam = self._require()
        try:
            return float(cam.frame_rate_control_value)
        except Exception:
            return self.resulting_frame_rate()

    def frame_rate_range(self) -> Tuple[float, float]:
        rng = self._require().frame_rate_control_value_range
        return float(rng.min), float(rng.max)

    def resulting_frame_rate(self) -> float:
        """Frame rate actually delivered to the host (measured by the SDK).

        Unlike the Basler ``ResultingFrameRate`` estimate, this is a *live*
        measurement: it reads ~0 until acquisition is running.
        """
        try:
            return float(self._require().get_measured_frame_rate_fps())
        except Exception:
            return 0.0

    # --- acquisition -------------------------------------------------------
    def start(self) -> None:
        """Begin continuous grabbing (arm + one software trigger)."""
        cam = self._require()
        if not cam.is_armed:
            cam.frames_per_trigger_zero_for_unlimited = 0
            cam.arm(2)
            cam.issue_software_trigger()

    def stop(self) -> None:
        """Stop continuous grabbing (disarm)."""
        cam = self._require()
        if cam.is_armed:
            cam.disarm()

    @property
    def is_grabbing(self) -> bool:
        return self._camera is not None and self._camera.is_armed

    def _poll(self, timeout_ms: int) -> np.ndarray:
        """Block up to ``timeout_ms`` for the next frame; return it as 2-D uint16."""
        cam = self._camera
        deadline = perf_counter() + timeout_ms / 1000.0
        while True:
            frame = cam.get_pending_frame_or_null()
            if frame is not None:
                buf = np.copy(frame.image_buffer)
                return buf.reshape(cam.image_height_pixels, cam.image_width_pixels)
            if perf_counter() >= deadline:
                raise RuntimeError("Timed out waiting for a frame from the Zelux.")

    def grab(self, timeout_ms: int = 5000) -> np.ndarray:
        """Grab and return a single frame as a 2-D ``numpy`` array (uint16, mono).

        Works whether or not a continuous grab is already running: if not armed
        it briefly runs acquisition for a one-shot, otherwise it pulls the latest
        frame from the running stream.
        """
        cam = self._require()
        if cam.is_armed:
            return self._poll(timeout_ms)
        self.start()
        try:
            return self._poll(timeout_ms)
        finally:
            self.stop()

    def frames(self, timeout_ms: int = 5000) -> Iterator[np.ndarray]:
        """Yield frames continuously while acquisition is running.

        Starts grabbing if not already started. Stops when :meth:`stop` is
        called (or the camera otherwise leaves the armed state).
        """
        cam = self._require()
        self.start()
        while cam.is_armed:
            frame = cam.get_pending_frame_or_null()
            if frame is not None:
                buf = np.copy(frame.image_buffer)
                yield buf.reshape(cam.image_height_pixels, cam.image_width_pixels)

    # --- context manager ---------------------------------------------------
    def __enter__(self) -> "ZeluxCS165MU":
        self.connect()
        return self

    def __exit__(self, *exc) -> None:
        self.disconnect()
