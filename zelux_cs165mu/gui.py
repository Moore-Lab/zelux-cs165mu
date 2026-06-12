"""Standalone test GUI for the Thorlabs Zelux CS165MU.

Thin shell over the shared, camera-agnostic harness in ``camera_dock.preview`` —
so the test GUI, the dock, and the DAQ share one implementation (no duplication).
All the real logic (threaded acquisition, decoupled preview, hybrid recording at
full data rate, snapshot) lives in the dock and is driven here with the Zelux
driver. The Zelux's 16-bit frames are handled by the shared harness via the
driver's ``bit_depth`` (scaled to 8-bit for preview/video; snapshots stay 16-bit).

Run with::

    python -m zelux_cs165mu.gui

Controls: exposure/fps trackbars, ``s`` snapshot, ``r`` record, ``q``/ESC quit.
"""

from __future__ import annotations

import os
import sys

# Shared harness lives in the parent dock repo; this package sits at
# .../xsphere-camera-dock/zelux-cs165mu/zelux_cs165mu, so the dock root is three
# directories up. Add it so ``camera_dock`` imports inside the dock checkout. The
# driver itself never imports the dock — only this test shell does.
_DOCK_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _DOCK_ROOT not in sys.path:
    sys.path.insert(0, _DOCK_ROOT)

from .camera import ZeluxCS165MU

FPS_CAP = 60.0   # fps-slider top; camera full-frame max ~34.8


def main() -> None:
    try:
        from camera_dock.preview import run
    except ImportError as exc:
        raise SystemExit(
            "Could not import the shared GUI (camera_dock.preview). Run this from "
            "within the xsphere-camera-dock checkout. Original error: " + str(exc))
    run(ZeluxCS165MU(), fps_cap=FPS_CAP)


if __name__ == "__main__":
    main()
