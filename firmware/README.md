# Firmware

Three boards get firmware. Nothing here needs compiling except the two ESP32 boards, which build with
[PlatformIO](https://platformio.org/) (`pip install platformio`).

## Raspberry Pi Pico — Pinscape Pico (nudge)

[Pinscape Pico](https://github.com/mjrgh/PinscapePico) by Michael Roberts turns the Pico + LIS3DH into a
nudge device. This build uses release **v1.0.2**.

1. Download the v1.0.2 release zip from the project's GitHub releases.
2. Hold BOOTSEL on the Pico, plug it in, and copy `PinscapePico-pico.uf2` onto the `RPI-RP2` drive. It
   restarts as **PinscapePico**.
3. Load [`pinscape_config.json`](pinscape_config.json) with the Config Tool from the same zip — either in
   the GUI (Main Config → open the file → Save to Pico) or from a command prompt:
   ```
   ConfigTool.exe --put-config firmware\pinscape_config.json
   ConfigTool.exe --reset
   ```
4. With the controller lying still on the desk, run the accelerometer calibration in the Config Tool.

What the config sets up: the LIS3DH on I²C0 (GP4 SDA / GP5 SCL, address 0x18), its axes turned to match
the box (the module sits lengthwise: x = −Y, y = +X), and the nudge acceleration on the gamepad's
**slider 1 / slider 2** (VPX reads those — see [pc/README.md](../pc/README.md)).

## Marquee ESP32 — ZeDMD with the turned picture and the attract show

[ZeDMD](https://github.com/PPUC/ZeDMD) by the PPUC team makes an ESP32 + HUB75 panels into a DMD that
dmd-extensions and VPX drive directly. The two panels sit upside down in the marquee trays, so this build
turns the picture in the firmware and adds a colour attract show for when no PC software is talking to it:

- [`zedmd-v5.1.8-pinball.patch`](zedmd-v5.1.8-pinball.patch) — adds the PlatformIO env `128x32_rot180`
  and the attract show hook
- [`attract_fx.h`](attract_fx.h), [`attract_text.h`](attract_text.h) — the show (plasma, fire, a pinball
  table, fireworks, matrix rain …, about a minute, loops). Change the words with `tools/attract_text.py`.

```
git clone https://github.com/PPUC/ZeDMD.git
cd ZeDMD
git checkout v5.1.8
git apply ../pinball-controller/firmware/zedmd-v5.1.8-pinball.patch
copy ..\pinball-controller\firmware\attract_*.h src\
pio run -e 128x32_rot180 -t upload
```

Board: a classic ESP32-WROOM-32 dev board with a CP2102 USB chip (USB-C). Wire it to the panel with the
map in [the marquee wiring picture](../images/wiring_marquee.png).

**Colour order:** many P2.5 panels swap green and blue. If red shows red but green shows blue, set ZeDMD's
RGB order to 3 (ZeDMD's on-device menu, or dmd-extensions' ZeDMD settings).

**Do not** also turn on the flip / rotate options in dmd-extensions' `DmdDevice.ini` — the picture would
turn back over.

## T-Display-S3 — the status screen

```
pio run -d status-display -t upload
```

Protocol, mounting and the PC helper: [status-display/README.md](../status-display/README.md).
`python status-display/tools/demo.py` shows fake data to check the screen on its own.
