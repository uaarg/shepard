# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
git submodule update --init --recursive   # clones src/modules/mavctl only
pip install -r requirements.txt
```

`dep/labeller` is NOT a registered submodule — that directory is empty. Do not import from `dep.labeller`; use `src.modules.imaging.detector` instead.

## Commands

```bash
./scripts/lint.sh          # flake8, max-line-length 140
./scripts/fmt.sh           # yapf formatter
./scripts/type.sh          # mypy on src/modules/imaging/ and test/
./scripts/test.sh          # pytest (uses PYTHONPATH=".:dep/labeller")

# Run tests directly (preferred locally — avoids test_battery.py crash):
python -m pytest test/ --ignore=test/test_battery.py -v

# Run a single test:
python -m pytest test/test_analysis.py::test_analysis_subscriber -v

# Run a sample script:
samples/run.sh aruco_stream
```

CI runs lint and typecheck on every push; tests only run on push/PR to `main`.

## Architecture

Shepard runs on a Raspberry Pi or ODroid connected to a PixHawk via MAVLink. It serves an aiohttp web server that the Emu ground station connects to.

### Data flow

```
Camera (RPiCamera / OakdCamera / DebugCamera)
  └─► SharedFrameCamera          # single capture thread, shared frame
        ├─► VideoEmuStreamer      # encodes JPEG, pushes to Emu /video endpoint
        └─► ImageAnalysisDelegate # runs detector in background thread
              └─► BaseDetector.predict() → BoundingBox
                    └─► get_object_location() → (x, y) direction vector
                          └─► subscribers(image, bounding_box, pos)
```

### Key abstractions

- **`CameraProvider`** (`camera.py`): base class for all cameras. `capture()` returns `PIL.Image`. `SharedFrameCamera` wraps any provider and serves the latest frame to multiple consumers thread-safely.
- **`BaseDetector`** (`detector.py`): single method `predict(image) → Optional[BoundingBox]`. Implementations: `ArucoDetector` (cv2 DICT_4X4_50), `IrDetector` (brightness threshold), `BucketDetector` (YOLO via ultralytics).
- **`ImageAnalysisDelegate`** (`analysis.py`): runs `camera.capture() → detector.predict()` in a loop in a background thread. Subscribers receive `(image, bounding_box, pos)` — `pos` is currently a raw direction vector in meters (not lon/lat; `XY_To_LonLat` call is commented out in `inference_georeference.py`).
- **`Emu`** (`emu/emu.py`): aiohttp server. Routes: `/ws` (WebSocket for telemetry/commands), `/images/<path>` (static), `/video` (latest JPEG frame). `send_video_frame(jpeg_bytes)` updates the frame; `VideoEmuStreamer` calls this from a background thread.
- **`VideoEmuStreamer`** (`video_emu_stream.py`): pulls frames from `SharedFrameCamera.capture()`, encodes to JPEG, calls `emu.send_video_frame()`. Frame rate set by `fps` param.
- **`Navigator`** (`autopilot/navigator.py`): wraps DroneKit vehicle for flight control via MAVLink.
- **`LocationProvider`** / **`MAVLinkDelegate`** (`location.py`, `mavlink.py`): provide GPS, heading, altitude, orientation from MAVLink messages.

### Subscriber pattern

`ImageAnalysisDelegate.subscribe(callback)` — callback signature:
```python
def on_detection(image: Image, bounding_box: Optional[BoundingBox], pos: Optional[tuple[float, float]]):
    ...
```

### Testing without hardware

Use `DebugCamera("res/test-image.jpeg")` and `DebugLocationProvider()`. Run `samples/aruco_stream.py` then open `http://localhost:8080/video` to verify streaming.

`test_battery.py` is not a real test — it connects to a real drone at import time. Always `--ignore=test/test_battery.py` when running locally.
