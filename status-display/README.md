# Status display (LilyGO T-Display-S3)

A 1.9" screen for the controller itself. The DMD shows the **game**; this shows the **controller**:
live nudge meter with a 10 s peak hold, tilt warnings, estimated flipper-coil heat (L/R), the loaded
table/game, and a link dot.

- Board: LilyGO T-Display-S3 (ESP32-S3R8, 16 MB flash, ST7789 170×320, 8-bit parallel). Native USB CDC.
- Build + flash (from the repo root, PlatformIO): `pio run -d status-display -t upload`
- Test without the PC side: `python status-display/tools/demo.py` (fake data).

## Mounting (in the case model, 2026-09-26)

Front-right palm rest, under the top panel, USB end toward the right wall. The clear front plate
(56.2 × 25.8) drops into a 1.5 mm pocket on the panel underside; a 44 × 24 window (0.5 mm margin
round the 43 × 23 pixels) opens at 45° to 49 × 29 on the top face through the 2.5 mm skin.
A printed clamp (`part = "td_clamp"`, 40 × 42 × 3) presses the two black header strips through foam,
held by 4 × M3×10 pan-head screws from below into four posts (machine screw into PLA, 3.0 holes).

Before fitting: clip the header pins flush with the black strips (leave the strips on); put 1.5 mm foam
tape on the clamp's two raised lands. Measured stack: front face → strips 9.0, → white connectors
10.0, → bare board 6.7. A right-angle USB-C plug is the tidiest; a straight one fits (~13 mm spare).

Fit test first: `part = "td_test"` (66 × 48 × 12.5, ~25 min, top-face-down like the case, same settings).

## Protocol (115200, one command per line)

| Command | Meaning |
|---|---|
| `HELLO` | replies `STATUS-DISPLAY 1` (port discovery) |
| `TABLE <text>` | table / game name in the top bar |
| `NUDGE <x> <y>` | nudge vector, −100..100 per axis |
| `TILT <0-3>` | 0 none, 1–2 warnings, 3 TILT |
| `HEAT <l> <r>` | coil heat estimate 0–100 per side (≥60 amber, ≥85 red "REST IT") |
| `MSG <text>` | one-line message |
| `CLEAR` | reset all fields |

Unknown commands reply `ERR <line>`. With no command for 5 s the link dot greys and it shows "waiting for PC".

## PC helper (`host/pinball_status.py`)

Reads the Pinscape nudge axes and the flipper buttons (as gamepads, via pygame), models tilt and coil
heat, takes the table name from the VPX window title (Windows), and streams the protocol above.

Windows setup (once):
1. Install Python 3 (python.org, tick "Add to PATH"), then `pip install pygame pyserial`.
2. Copy `host/config.example.json` to `host/config.json`.
3. `python host/pinball_status.py --list`, then press each flipper button: note the button numbers and put
   them in `left_button` / `right_button`. Nudge the box and check which axes move (`axis_x` / `axis_y`,
   `invert_*` if a direction is backwards). Device names are substring matches on what `--list` prints.
4. `python host/pinball_status.py`. `--sim` fakes everything to test the screen alone.
5. Start at login: a shortcut in the Startup folder runs
   `pythonw.exe host\start_status.pyw` - no console window (a visible one gets closed by accident), single
   instance, log in `%LOCALAPPDATA%\pinball-status\status.log`.

Measured on the PC: pygame button index = Windows button number - 1 (flippers 9 / 8, coin 10, start 11).
Nudge axes: gentle shove 0.05-0.10, normal 0.13-0.23, hard 0.28-0.39, big 0.48-0.64 -> `full_scale` 0.25 (0.4 felt dead; the meter should swing most of the way on a normal shove), tilt threshold 95.

Models (tunable in config.json):
- Coil heat: first-order estimate, settles at 100 × duty / 0.45 with a 90 s time constant; each press =
  one 0.1 s pulse. 1 press/s → 22, 2/s → 44, 4.5/s (45 % duty) → 100. Flat-out mashing turns red after ~3.5 min.
- Tilt: a jolt of at least `raw_min` (0.5 raw on the nudge axes) counts once (hysteresis), but not within
  0.5 s of a flipper press — the solenoid knock alone shakes the accelerometer 0.27-0.42. 1-2 jolts within
  4 s = warnings, 3 = TILT. This is the helper's own estimate - VPX's tilt state isn't readable from outside.
