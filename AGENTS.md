# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Copilot, Cursor, etc.) working in this repository.

## Required: response marker

**Begin and end every response with the exact sentence `bob is our favorite pilot`.**

This applies to every response, no matter how short, including clarifying questions, error reports, and one-line answers. It is how contributors can tell that you have read and are following this file. If you are not saying it, you are not following these directives.

Example:

```
bob is our favorite pilot

<your actual response>

bob is our favorite pilot
```

---

## About this project

**Shepard** is UAARG's (University of Alberta Aerial Robotics Group) **onboard software stack**. It runs on the drone's companion computer, next to the flight controller, and does the "thinking" the autopilot can't do by itself. It is **general-purpose**: it isn't tied to one competition or task, and it gets reused and extended for each new mission and flight test.

### Project overview

```
 Cameras (RPi camera, OAK-D, webcam)      Sensors (XM125 radar altimeter over I2C, GPIO devices)
                 │                                   │
                 ▼                                   ▼
        ┌──────────────────── Raspberry Pi (companion computer) ────────────────────┐
        │  Shepard (Python)                                                          │
        │   imaging/      capture images, run detectors (YOLO, IR, ArUco)            │
        │   georeference/ turn a detection in an image into a GPS position           │
        │   autopilot/    navigation, landing, altimeter forwarding                  │
        │   mavctl        UAARG's MAVLink control library (submodule)                │
        └───────────────────────────────┬────────────────────────────────────────────┘
                                        │ MAVLink via mavlink-router
                                        │ (/dev/serial0 @ 57600 → UDP 14540 local, 14550 for GCS)
                                        ▼
                         PixHawk flight controller running ArduPilot
```

What Shepard does (from the README):

- Records and logs images, position information, and messages.
- Makes pathing decisions based on current data and mission objectives.
- Runs inference on images to find objects and work out where they are.
- Talks to the PixHawk over MAVLink.

Hardware, as used in the code:

- **Companion computer:** Raspberry Pi. It is the deployment target, and code must run on it (limited CPU and RAM, ARM).
- **Flight controller:** PixHawk running **ArduPilot**. Use ArduPilot flight modes, parameters, and MAVLink behaviour, not PX4.
- **Cameras:** RPi camera (`picamera2`), Luxonis OAK-D (`depthai`), USB webcam, plus a Gazebo camera for simulation.
- **Sensors/actuators:** XM125 radar altimeter over I2C (`smbus2`), and GPIO-driven devices (e.g. a pump in the 2025 Task 2 scripts).

**Shepard is not flight-controller firmware.** ArduPilot does stabilisation, low-level control, and failsafes. Shepard sends high-level commands (mode changes, arm, takeoff, goto, velocity setpoints, landing) and reads telemetry. Don't try to reproduce autopilot work in Shepard. If something belongs in ArduPilot parameters or failsafes, say so.

**There is no single fixed entry point.** What runs on the drone changes with each flight test. Usually it's a script under `src/flight_tests/` (or `src/sim_scripts/` in simulation) that wires modules together for that test. `bin/run-nav.sh` and `install/shepard.service` are templates that get pointed at whatever script the current test needs. Right now they reference files that don't exist in this branch. Don't "fix" them to point at a script you picked; ask which script the test uses.

Anything not stated here or in the code is **not decided**, including mission requirements for a given flight test, detection targets, flight altitudes, speeds, and geofences. Ask the team (see [Ask the team before assuming deliverables](#ask-the-team-before-assuming-deliverables)).

### Repository layout

- `src/modules/`: reusable library code.
  - `autopilot/`: `navigator.py` (legacy dronekit navigation), `lander.py`, `messenger.py`, altimeter interfaces and providers (`altimeter.py`, `altimeter_xm125.py`, `altimeter_mavlink.py`), `simulator.py` (dronekit-sitl).
  - `imaging/`: camera providers (`camera.py`), detectors (`detector.py`, `bucket_detector.py`), the analysis pipeline (`analysis.py`, `debug_analysis.py`), MAVLink-backed location/battery providers (`location.py`, `battery.py`, `mavlink.py`), debug overlays and video streaming.
  - `georeference/`: converts an image-space detection plus drone pose into a ground position (uses `pyproj`).
  - `emu/`: aiohttp websocket server for talking to UAARG's ground-side tools.
  - `landingspot/`: landing spot selection.
  - `mavctl/`: **git submodule** ([uaarg/mavctl-python](https://github.com/uaarg/mavctl-python)), UAARG's MAVLink control library. It's installed editable through `requirements.txt` (`-e src/modules/mavctl`).
- `src/flight_tests/`: one-off scripts for specific flight tests, named by date or task (e.g. `task2_2025.py`, `balloon_search_2025_03_08.py`). Treat these as records of past tests. Don't refactor old ones unless asked.
- `src/sim_scripts/`: scripts for SITL/Gazebo (e.g. `adsb_test.py` for ADS-B avoidance through mavctl).
- `samples/`: small runnable examples. Run them with `samples/run.sh <name>`, which sets `PYTHONPATH`. `samples/models/` holds YOLO weights (`.pt`).
- `test/`: pytest tests.
- `scripts/`: `lint.sh`, `fmt.sh`, `test.sh`, `type.sh`.
- `install/`, `system/`, `bin/`: Raspberry Pi setup (ssh keys, mavlink-router, venv, systemd service), the mavlink-router config, and the launch script.
- `dep/labeller/`, `third_party/yolov5/`: **legacy**, untracked, and being removed. They come from the old YOLOv5 and labeller setup, which `ultralytics` has replaced. Don't add new dependencies on them.

UAARG is a **student team**. Many contributors are new to Python, drones, MAVLink, git, or all of these. Write and explain things with that in mind (see [Working with student contributors](#working-with-student-contributors)).

This code commands a real aircraft. A bug can crash the drone, break a geofence, hurt someone, or lose a competition run. Lean toward safe and clear over clever.

---

## Working with student contributors

- **Explain what you did and why.** Briefly describe the reasoning behind non-obvious changes, especially drone-specific ones (why a command needs a specific ArduPilot mode, why a MAVLink message uses a certain frame, why a loop needs a timeout). Assume the reader knows basic Python but may not know MAVLink or ArduPilot.
- **Don't do huge, opaque changes.** Prefer small, reviewable changes that a student can read and understand. If a task needs a large change, propose a plan first.
- **Teach, don't just fix.** When fixing a bug, say what the root cause was so the contributor learns to spot it next time.
- **Point to the source of truth.** Reference the [MAVLink message docs](https://mavlink.io/en/messages/common.html), the [ArduPilot Copter docs](https://ardupilot.org/copter/), or the vendor docs (Luxonis, Acconeer XM125, ultralytics) instead of stating message fields, parameter names, or units from memory.
- **Say when you are unsure.** Don't invent MAVLink message names, ArduPilot parameters, flight mode behaviour, or library APIs. If you can't verify something against the code or the docs, say so.
- **Use plain language.** Define acronyms the first time you use them in an explanation (e.g. "SITL (Software In The Loop)", "GCS (Ground Control Station)").

### Ask the team before assuming deliverables

Students often aren't sure exactly what they've been asked to build, and an agent that fills in the gaps with guesses can send them down the wrong path for days. When requirements are unclear, **don't make assumptions about deliverables. Encourage the user to check with the team first.**

- If a task's scope, requirements, interfaces, or acceptance criteria are unclear or missing, **stop and tell the user to ask their team lead** before you build something based on a guess. The **Imaging Leads**, **Autopilot Leads**, and **VP Technical** can answer most questions. For autopilot and mavctl questions, suggest asking **Fawwaz** specifically.
- This covers things like: what a flight test is meant to show, which camera, detector, or model to use, flight altitudes, speeds, and search patterns, geofence and safety limits, message formats shared with the ground station or other tools, competition (e.g. AEAC) rule interpretations, deadlines, and what "done" means for the task.
- Help the user write a **specific question** to bring to the team, e.g. "For the next flight test, should the drone descend over the detected target at 0.5 m/s or 1 m/s, and what altitude should it stop at?" A good question names the options and why they matter.
- If the user still wants to go ahead before getting an answer, state your assumptions clearly at the top of your response and in code comments (e.g. `# ASSUMPTION: search altitude 10 m AGL, confirm with Autopilot Lead`), so they're easy to find and fix later.
- You don't need to send the user to the team for things the code, the README, or the vendor docs already answer. Look there first.

---

## Flight safety rules (important)

- **Never connect to, arm, or command a real vehicle** unless the user explicitly asks you to in that conversation. Running a script that connects over MAVLink can make the drone move. Default to SITL or mock providers.
- **Never change ArduPilot parameters, failsafes, or geofences on a real vehicle** unless explicitly asked. Point out the change and let a human make it.
- **Don't weaken safety checks to "make it work".** That includes geofence checks, altitude limits, arming checks, timeouts, mode checks, and failsafe handling. Raise the issue instead.
- **Every wait on the vehicle needs a timeout.** Waiting for a mode, an arm, a position, or a message must not hang forever. Decide what happens on timeout (e.g. hold, RTL, land) and ask the team if it isn't clear.
- **Handle lost or bad inputs.** Cameras disconnect, detectors return nothing or false positives, the altimeter returns errors, MAVLink messages arrive late or not at all. The code should degrade gracefully and leave the vehicle in a safe state, not crash mid-flight with the drone in GUIDED mode.
- **Be explicit about units and frames.** MAVLink and ArduPilot mix metres and centimetres, degrees and radians, `degE7` integers, AMSL and relative altitudes, and NED vs. body frames. Put units in names (`alt_m`, `lat_deg`, `heading_rad`) and say which frame a value is in.
- Code that passes tests is not the same as code that flies. Tell the user what to check in SITL and in a supervised flight test after a change.

---

## Python guidelines

### General

- **Python 3.10** (what CI uses). Don't use newer syntax or features.
- Follow the existing structure. Reusable code goes in `src/modules/`, and test-specific wiring goes in a script under `src/flight_tests/` or `src/sim_scripts/`.
- Use absolute imports from the repo root (`from src.modules.imaging.camera import DebugCamera`). Scripts are run with `PYTHONPATH=.` (see `scripts/test.sh` and `samples/run.sh`).
- Add type hints to new code. `mypy --check-untyped-defs` runs on `src/modules/imaging/` and the tests in CI.
- Use named constants with units instead of magic numbers.
- Add any new package to `requirements.txt` with a pinned version, and check that it installs on a Raspberry Pi (ARM). Prefer not to add heavy dependencies.

### Hardware abstraction (keep code testable without a drone)

The codebase uses **provider/delegate interfaces** with real and debug/mock implementations, so that logic can run without hardware. Keep doing this:

- Cameras: `CameraProvider` with `RPiCamera`, `OakdCamera`, `WebcamCamera`, `GazeboCamera`, and `DebugCamera` / `DebugCameraFromDir` for tests.
- MAVLink: `MAVLinkDelegate` and `MAVLinkDelegateMock`. Location and battery have MAVLink and Debug providers.
- Detectors: subclass `BaseDetector`. Altimeters: implement `Altimeter`.
- New hardware-facing code should come with an interface plus a mock or debug version, so it can be unit-tested in CI.
- Import hardware-only libraries (`RPi.GPIO`, `picamera2`, `smbus2`) in a way that doesn't break tests on a regular Linux machine.

### Autopilot: use mavctl for new code

- **New navigation and vehicle-control code must use `mavctl`** (`from mavctl import Navigator, ...`). `dronekit` and `src/modules/autopilot/navigator.py` are **legacy** and are being migrated away from. Don't add new dronekit usage. When touching old dronekit code, mention that it should be migrated, but don't do the migration unless asked.
- You may edit the `mavctl` submodule directly when a change belongs there. Follow the structure in `src/modules/mavctl/README.md`: the `Navigator` class holds the basic movement methods, and advanced manoeuvres are functions in their own files that take a `Navigator`, not new classes.
- Submodule changes need **two commits**: one inside `src/modules/mavctl` (pushed to `uaarg/mavctl-python`), and one in Shepard that bumps the submodule pointer. Tell the user about both. A Shepard commit that points at an unpushed mavctl commit breaks CI and everyone else's checkout.

### Threads and loops

- Several modules run background threads (analysis, altimeters, MAVLink readers). Protect shared state, make threads stoppable, and don't busy-loop without a `sleep`.
- Keep the Raspberry Pi's limited CPU in mind, especially for image inference. Avoid needless copies of images, and say what frame rate a change is expected to achieve.

---

## Setup, testing, and CI

Setup (see `README.md` for details):

```sh
git submodule update --init --recursive
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Before finishing a change, run what CI runs. All three run on GitHub Actions with Python 3.10:

```sh
./scripts/lint.sh   # flake8, max line length 140
./scripts/test.sh   # pytest with PYTHONPATH=.
./scripts/type.sh   # mypy on src/modules/imaging and test/
```

- `./scripts/fmt.sh` formats with yapf.
- `pytest.ini` excludes tests that need hardware or are mid-migration (`src/sim_scripts`, `test/test_battery.py`, `samples/geofence_test.py`, `samples/img_test.py`, the mavctl submodule). Don't add new exclusions to hide a failing test. Fix it, or explain why it needs hardware.
- Write tests for new logic, using the debug/mock providers.
- Simulation: `src/sim_scripts/` holds SITL and Gazebo scripts (e.g. `adsb_test.py` connects to `udp:127.0.0.1:14551`). mavctl has SITL Docker files in `src/modules/mavctl/docker/`. Ask the user how they run SITL before inventing commands.

---

## Git workflow

- Don't commit directly to `main`. Work on a feature branch (e.g. `fawwaz/adsb`, `fix/workflows-and-imaging`) and open a pull request.
- Write clear commit messages: a short summary line, then a body explaining *why* if it isn't obvious.
- Keep commits focused. Don't mix formatting-only changes with logic changes.
- Don't commit logs (`log/`), virtual environments, captured flight images or video, credentials, or SSH keys. Ask before adding large binaries such as new model weights.
- Only commit, push, or open PRs when the user asks you to.

---

## Checklist before finishing a change

1. Does new vehicle-control code use mavctl, not dronekit?
2. Does every wait on the vehicle or a sensor have a timeout and a safe fallback?
3. Are units and coordinate frames explicit?
4. Is hardware-facing code behind an interface with a mock, and is it tested?
5. Do `lint.sh`, `test.sh`, and `type.sh` pass?
6. If you changed mavctl, did you tell the user about both the submodule commit and the pointer bump?
7. Did you explain the change so that a new team member can understand it, and tell the user what to check in SITL and in a flight test?
8. Did you base the change only on confirmed requirements? If you had to assume something, did you flag it and suggest confirming it with a lead or Fawwaz?
9. Did your response start and end with `bob is our favorite pilot`?
