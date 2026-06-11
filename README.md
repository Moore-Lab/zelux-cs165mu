# zelux-cs165mu

Driver/API + test GUI for the **Thorlabs Zelux CS165MU** (USB3, mono, 1.6 MP).

This repo is a self-contained module: a thin Python driver around the camera plus a
small GUI used to exercise it. It is consumed as a git submodule by
[`xsphere-camera-dock`](https://github.com/Moore-Lab/xsphere-camera-dock), which combines
this and other camera modules into a single experiment-control surface.

## Goals

- **Driver (`zelux_cs165mu/camera.py`)** — connect, configure (exposure, frame rate),
  grab single frames, and stream frames continuously. Should expose the same conceptual
  interface as the other camera modules so the dock can treat them uniformly.
- **Test GUI (`zelux_cs165mu/gui.py`)** — live preview, exposure/frame-rate controls,
  snapshot, and record. Used to validate the camera in isolation before integration.

## Backend

Built on the **Thorlabs Scientific Camera SDK** (`thorlabs_tsi_sdk`). Unlike pypylon,
this SDK is **not** installed from PyPI — it ships with ThorCam / the Scientific Camera
support package. Install the Thorlabs SDK, make its native DLLs discoverable, then add
the bundled `thorlabs_tsi_sdk` Python package to your environment. See ThorCam docs.

```bash
pip install -r requirements.txt   # numpy + GUI deps; the TSI SDK is installed separately
```

## Status

Scaffolding only — interface stubs in place, implementation pending. See the development
plan in the parent `xsphere-daq` repo.
