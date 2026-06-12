"""Hardware smoke test for the Thorlabs Zelux CS165MU driver.

Run with the camera plugged in and the Thorlabs SDK installed::

    python smoke_test.py

It enumerates devices, opens the camera, reports info/ranges, sets a modest
exposure + frame rate, grabs a short burst, and prints the measured frame rate.
No GUI, no files written.
"""

from __future__ import annotations

import time

from zelux_cs165mu.camera import ZeluxCS165MU, _add_dll_directory


def list_devices() -> None:
    _add_dll_directory()
    try:
        from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
    except (ImportError, OSError) as exc:
        print(f"Thorlabs SDK not loadable: {exc}")
        return
    with TLCameraSDK() as sdk:
        serials = sdk.discover_available_cameras()
        if not serials:
            print("No Thorlabs cameras found.")
            return
        print(f"Found {len(serials)} device(s): {', '.join(serials)}")


def main() -> None:
    list_devices()

    with ZeluxCS165MU() as cam:
        print("\nConnected:", cam.device_info)
        print("Sensor size (w x h):", cam.sensor_size())
        print("Bit depth:", cam.bit_depth)
        print("Exposure range (us):", cam.exposure_range())
        print("Frame-rate range (fps):", cam.frame_rate_range())

        cam.set_exposure(5000.0)   # 5 ms
        cam.set_frame_rate(30.0)
        print(f"\nSet exposure -> {cam.get_exposure():.1f} us, "
              f"target fps -> {cam.get_frame_rate():.1f}")

        n = 60
        print(f"\nGrabbing {n} frames...")
        cam.start()
        t0 = time.perf_counter()
        shape = None
        for _ in range(n):
            frame = cam.grab()
            shape = frame.shape
        dt = time.perf_counter() - t0
        measured = cam.resulting_frame_rate()
        cam.stop()

        print(f"Grabbed {n} frames of shape {shape} in {dt:.3f} s "
              f"=> {n / dt:.1f} fps wall-clock, {measured:.1f} fps SDK-measured")
        print("\nSmoke test OK.")


if __name__ == "__main__":
    main()
