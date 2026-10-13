# tools

## Generators (Windows)

| Script | Makes |
|---|---|
| `make_wiring_diagrams.py` | `images/wiring*.png/svg` — the step-by-step wiring pictures. Its `CONTROLLER_WIRES` / `MARQUEE_WIRES` lists are the record of every connection |
| `make_overview.py` | `images/overview.png/svg` — "how it all connects" (uses the part renders) |
| `make_print_files.py` | `print/stl/*.stl` and `print/bambu-{a1,p1s,x1c}/*.3mf` (needs OpenSCAD + Bambu Studio) |
| `../renders/` | the Blender product renders: `export_stls.py`, `make_screens.py`, `blender -b -P render.py -- <repo> 128`, `annotate.py` |

## Test helpers

`encoder_watch.py` (buttons), `nudge_watch.py` (Pinscape nudge) run anywhere with Python. The rest of this
page is the original Mac bench tooling for the marquee and the Pico.

## zedmd_pattern - marquee orientation / colour test (Mac)

Shows a still test image on the marquee for N seconds: RED square top-left, GREEN top-right, BLUE bottom-left,
WHITE bottom-right, a white arrow pointing UP, colour bars R G B Y C M W, and a grey border.

Build once (needs libzedmd v0.9.7 built in ~/Projects/zedmd-src/libzedmd, see its README "MacOS (arm64)"):

    clang++ -std=c++17 -O2 -I ~/Projects/zedmd-src/libzedmd/src tools/zedmd_pattern.cpp \
      -L ~/Projects/zedmd-src/libzedmd/build -lzedmd \
      -Wl,-rpath,$HOME/Projects/zedmd-src/libzedmd/build \
      -Wl,-rpath,$HOME/Projects/zedmd-src/libzedmd/third-party/runtime-libs/macos/arm64 -o tools/zedmd_pattern

Run: `tools/zedmd_pattern 60` (seconds). It finds the ESP32 on USB by itself.

## zedmd_rgb - read / set the colour order
`tools/zedmd_rgb` prints it; `tools/zedmd_rgb 3` sets + saves it (our panels need 3: green/blue swapped).

## dmd_demo.py + zedmd_play - mock pinball show from the Mac
`python3 tools/dmd_demo.py` writes tools/dmd_demo.raw; `tools/zedmd_play tools/dmd_demo.raw 30 4` plays it 4 times.
Build zedmd_play / zedmd_rgb the same way as zedmd_pattern.

## attract_text.py + attract_sim - the ESP32's colour attract show
The show is code: firmware/attract_fx.h (effects + scene list), text images in firmware/attract_text.h.
Change the words in tools/attract_text.py and run it; preview: `clang++ -std=c++17 -O2 tools/attract_sim.cpp -o tools/attract_sim`,
run it inside tools/ (writes attract_sim.raw), then `tools/zedmd_play tools/attract_sim.raw 30 1`.
To put it on the ESP32: copy both headers into ZeDMD/src/, rebuild env 128x32_rot180, flash.

## encoder_watch.py - live button readout for the Zero Delay encoder
`.venv-esp/bin/python tools/encoder_watch.py 120` prints every button change against the rest state (buttons only;
the stick axes float when no joystick is connected). Needs `pip install hidapi` in .venv-esp.

## Pinscape Pico from the Mac

- `pinscape/pinscape_cli` - talks to the Pico's vendor interface: `log` (read its status log), `getconfig`,
  `putconfig <file.json>` (store + reboot), `reboot`. Built against the official PinscapePico LinuxAPI + libusb:
  ```
  git clone --depth 1 https://github.com/mjrgh/PinscapePico.git ~/Projects/PinscapePico
  brew install libusb pkgconf
  cd ~/Projects/PinscapePico/LinuxAPI && clang++ -std=c++17 -O1 -I/opt/homebrew/include $(pkg-config --cflags libusb-1.0) -I. -I.. -I../USBProtocol USBDevice.cpp PinscapeVendorInterface.cpp ~/Projects/pinball-controller/tools/pinscape/pinscape_cli.cpp $(pkg-config --libs libusb-1.0) -o ~/Projects/pinball-controller/tools/pinscape/pinscape_cli
  ```
- `nudge_watch.py` - reads the Pico's gamepad and prints each shove's direction (first jolt) and peak X/Y.

## Exciter level test

- `audio/make_exciter_test.py` writes `audio/exciter_test.wav` (22 s at -1 dBFS: bass sweep 25-160 Hz, flipper thumps,
  rolling-ball rumble, big hits).
- `audio/play_to.swift` plays a file on one named output device without touching the Mac's default output:
  `swiftc -O tools/audio/play_to.swift -o tools/audio/play_to && tools/audio/play_to "USB Audio DAC" tools/audio/exciter_test.wav`
- Set the amp knob with this at full volume: as high as it goes before anything buzzes or rattles.
