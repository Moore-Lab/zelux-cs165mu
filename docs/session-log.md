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

## 2026-06-11 — Session log started; baseline

**Context.** First logged session. Recording the baseline.

**State:** scaffolding only. `zelux_cs165mu/camera.py` and `zelux_cs165mu/gui.py` are
stubs; no implementation yet. Backend is the Thorlabs Scientific Camera SDK
(`thorlabs_tsi_sdk`), installed separately (not from PyPI) — see README.

**Next (zelux):** implement the driver mirroring the dock's `CameraBase` surface
(`connect` / `disconnect` / `set_exposure` / `set_frame_rate` / `grab` / `frames`), using
the already-implemented `basler-acA1440` module as the reference shape, then a matching
OpenCV test GUI. Validate against hardware via ThorCam-installed SDK.
