# zelux-cs165mu — Development Session Log

Running, chronological record of development for **this repo only** (`zelux-cs165mu`,
the Thorlabs Zelux CS165MU driver/API + test GUI). Write here for any change to this
module; dock- or top-level changes go in their own repos' logs.

This is a low-level camera module: once the driver + GUI are validated against hardware
and stable, this log will largely stop accruing entries — development moves up to the
dock.

Newest entries first. Keep entries short and factual; convert relative dates to absolute.
See the [README](../README.md) for goals and backend setup.

---

## 2026-06-11 — Hardware validation PASS; SDK installed

**Context.** Resolved the wheel blocker and validated against the real camera.

**SDK install.** The `thorlabs_tsi_sdk` wheel was *on disk all along*, zipped inside
`C:\Program Files\Thorlabs\Scientific Imaging\Scientific Camera Support\
Scientific_Camera_Interfaces.zip` → `SDK\Python Toolkit\
thorlabs_tsi_camera_python_sdk_package.zip`. Earlier searches missed it because they
looked for the *extracted* `tl_camera.py`, not the zip. Installed with
`pip install thorlabs_tsi_camera_python_sdk_package.zip` → `thorlabs_tsi_sdk-0.0.8`.
Per the toolkit README, the examples' DLL-copy step is **not** needed for us — the
driver's `_add_dll_directory()` points at the ThorCam dir, which already holds the
native DLLs.

**Camera:** CS165MU, s/n 32943, Thorlabs. Sensor 1440×1080, **bit depth 10** (uint16
buffer, 10 significant bits). Exposure range 40 µs – 26.8 s. Frame-rate range
0.91 – 34.81 fps.

**`smoke_test.py`:** PASS. 5 ms exposure, 30 fps target → 60-frame burst at **29.5 fps
wall-clock**.

**Max-rate check** (2 ms exposure, target = range max 34.81): **34.6 fps wall-clock**
over 200 frames — the CS165MU full-frame max, matching spec.

**GUI I/O paths (headless):** verified without opening a window — `grab` → uint16
(1080,1440); `_to_8bit` → uint8; 16-bit TIFF snapshot round-trips bit-identical;
`_open_writer` opens and a 10-frame AVI writes (~5 MB). Only the live preview window +
trackbars are unexercised (needs a desktop; can't drive over SSH).

**Quirk found + handled.** `get_measured_frame_rate_fps()` returns **0.0** on this unit
(SDK 0.0.8), even mid-stream. Fixed `resulting_frame_rate()` to fall back to the target
rate when the SDK reports <= 0, mirroring the Basler driver (so the GUI overlay shows a
useful number, not 0.0). Wall-clock timing confirms true throughput regardless.

**Verdict:** Zelux driver validated end-to-end against hardware. Module effectively
done; remaining gap is only the live-window GUI interaction (low risk — the production
UI is the dock web app anyway).

## 2026-06-11 — Driver + GUI + smoke test implemented

**Context.** Implemented the module against the Thorlabs TSI SDK API, mirroring
`basler-acA1440`. API grounded in the installed reference
(`Thorlabs_Camera_Python_API_Reference.pdf`, SDK 0.0.8 Rev. D), not from memory.

**Implemented:**

- `zelux_cs165mu/camera.py` — `ZeluxCS165MU` over `thorlabs_tsi_sdk`. Same public
  surface as the Basler driver: connect/disconnect, device info, sensor size,
  exposure get/set/range, frame-rate get/set/range + `resulting_frame_rate()`,
  start/stop, one-shot **and** streaming `grab()`, `frames()` generator, context
  manager. Continuous video = `operation_mode=SOFTWARE_TRIGGERED`,
  `frames_per_trigger_zero_for_unlimited=0`, `arm(2)` + one `issue_software_trigger()`.
- `zelux_cs165mu/gui.py` — OpenCV test GUI mirroring Basler's (geometric exposure
  slider, fps slider, snapshot, record, fps overlay).
- `smoke_test.py` — headless enumerate/open/configure/grab-burst check.

**Key differences from Basler (documented in code):**

- Frames are **`uint16`** (Zelux digitises to `bit_depth` bits in the low bits of a
  16-bit sample), vs Basler's Mono8 `uint8`. GUI scales to 8-bit for display/record;
  snapshots saved at full 16-bit (TIFF).
- Frame rate via `frame_rate_control_value` (+ enable flag); `resulting_frame_rate()`
  is the SDK's **live measured** fps (≈0 until streaming), not a pre-grab estimate
  like Basler's `ResultingFrameRate`.
- Native DLLs load at SDK import → `connect()` calls `_add_dll_directory()` first
  (honours `THORLABS_TSI_DLL_DIR`, else the default ThorCam dir). SDK import is
  deferred to `connect()` so `import zelux_cs165mu` works without the SDK installed.

**Verified (no hardware):** module imports cleanly; `ZeluxCS165MU` passes
`isinstance(..., CameraBase)` against the dock protocol; `connect()` raises a clear
"install the wheel" `RuntimeError` rather than a raw `ImportError`.

**BLOCKER — hardware validation pending.** The `thorlabs_tsi_sdk` **Python wheel is
not installed** and not present anywhere on disk (it ships in the Thorlabs Scientific
Camera SDK "Python Toolkit", not on PyPI). The camera itself **is** connected (USB
"Thorlabs Camera Zelux", status OK) and the native DLLs **are** installed at
`C:\Program Files\Thorlabs\Scientific Imaging\ThorCam`. **TODO:** install the wheel,
then run `smoke_test.py` + the GUI and log results (measured fps, bit depth, exposure
range, any node quirks). Once it runs, double-check the `image_buffer` reshape and the
frame-rate-control behaviour while armed (couldn't be exercised here).

## 2026-06-11 — Session log started; baseline

**Context.** First logged session. Recording the baseline.

**State:** scaffolding only. `zelux_cs165mu/camera.py` and `zelux_cs165mu/gui.py` are
stubs; no implementation yet. Backend is the Thorlabs Scientific Camera SDK
(`thorlabs_tsi_sdk`), installed separately (not from PyPI) — see README.

**Next (zelux):** implement the driver mirroring the dock's `CameraBase` surface
(`connect` / `disconnect` / `set_exposure` / `set_frame_rate` / `grab` / `frames`), using
the already-implemented `basler-acA1440` module as the reference shape, then a matching
OpenCV test GUI. Validate against hardware via ThorCam-installed SDK.
