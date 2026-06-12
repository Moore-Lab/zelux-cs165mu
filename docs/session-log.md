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
