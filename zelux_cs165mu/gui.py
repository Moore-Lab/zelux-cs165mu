"""Standalone test GUI for the Thorlabs Zelux CS165MU.

Lightweight harness to validate the driver in isolation: live preview plus
exposure / frame-rate controls, snapshot, and record. The GUI framework is
intentionally left open pending the planning discussion in ``xsphere-daq``.

Run with::

    python -m zelux_cs165mu.gui
"""

from __future__ import annotations

from .camera import ZeluxCS165MU


def main() -> None:
    raise NotImplementedError("Test GUI not implemented yet — see development plan.")


if __name__ == "__main__":
    main()
