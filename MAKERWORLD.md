# MakerWorld listing — copy/paste kit

Everything needed to publish this on MakerWorld. Files to upload are listed at the bottom.

---

## Title

Visual Pinball Controller — Desktop Virtual Pinball + Arcade Controller with Solenoid Knock, Haptics, Nudge and LED Marquee

## Category / tags

Category: **Gadgets → Computers & Accessories** (or Toys & Games → Game accessories)

Tags: `pinball`, `virtual pinball`, `vpx`, `visual pinball`, `arcade`, `arcade controller`, `joystick`,
`retrobat`, `mame`, `solenoid`, `haptic`, `pinscape`, `raspberry pi pico`, `esp32`, `zedmd`, `dmd`,
`led matrix`, `synthwave`

## License

**CC BY-SA 4.0** (Attribution-ShareAlike).

---

## Description (paste into the description box)

**Virtual pinball you can feel — on your desk.**

A 3D-printed controller for **Visual Pinball X** and arcade games. Every flip fires a **real solenoid**
that knocks the box, an **exciter** under your palms turns the table's sounds into vibration, and you
**nudge** the table by shoving the box (accelerometer, Pinscape Pico). A slide-on **128 × 32 LED
marquee** shows the game's DMD in pinball, the game's logo while you browse RetroBat, and a neon
synthwave show when it's idle. A small **status screen** shows the nudge meter, tilt warnings and
flipper-coil heat.

**Features**
- Flipper buttons in the side walls, each with a 12 V solenoid knock — pure hardware, no lag, no setup
- Haptic table sounds through a 50 mm exciter
- Nudge + tilt via a Raspberry Pi Pico + LIS3DH running Pinscape Pico
- Arcade layout: joystick, 6 buttons, coin + start (a normal gamepad)
- 128 × 32 LED marquee (2 × P2.5 HUB75 panels, ESP32 with ZeDMD) that slides onto the back
- One cable in: 12 V + USB on a GX16-8 connector
- Every printed joint is an M3 heat-set insert + screw; prints **without supports**

**Print settings** (built into the 3MFs): 0.20 mm layers, 4 walls, 20 % gyroid (cover 25 %), 5 top /
5 bottom layers, no supports, seam at the rear, elephant-foot compensation 0.15 mm, PLA Matte at
15 mm³/s. The case fills a 256 mm bed (no brim — wash the plate); the cover has a 4 mm brim. Print the
test coupon first.

**You'll also need** two XY-J02 timer relays, two JF-1039 12 V solenoids, an XH-M543 amp, a 50 mm
exciter, a PCM2704 USB sound card, a 7-port USB hub board, a 480 Mbps USB isolator, a Raspberry Pi Pico
H, an LIS3DH, a LilyGO T-Display-S3, a zero-delay encoder kit (joystick + 10 buttons), GX16-8
connectors, a 12 V 6 A+ supply, and for the marquee two P2.5 64 × 32 panels, an ESP32 and a 10 A 5 V
converter. **Full parts list with links, step-by-step wiring pictures, firmware and PC setup:**

👉 **https://github.com/growthlayer/visual-pinball-controller**

**Assembly in short**
1. Print the test coupon, then the cover, case, marquee trays, plate and small parts; melt in the M3 inserts.
2. Program the relays (P1.1, 0.1 s), set the converters to 5 V, flash the Pico, the marquee ESP32 and the screen.
3. Wire the cover on the bench (six step-by-step pictures) and bench-test.
4. Fit the buttons, joystick, exciter and screen in the case; close it onto the cover with 6 screws.
5. Build the marquee, slide it onto the back, set up VPX / RetroBat and the helper programs on the PC.

---

## Images to upload (in this order)

1. `images/hero.png` — cover
2. real photo of the finished controller
3. real photo / video of it in use (a flip with the knock, the marquee DMD)
4. `images/render_top.png`
5. `images/render_rear.png` — the GX16 sockets and the marquee from behind
6. `images/exploded.png` — exploded view with part numbers
7. `images/cutaway.png` — inside
8. `images/layout_cover.png` — every board on the cover
9. `images/overview.png` — how it connects
10. `images/wiring.png` — complete wiring
11. `images/wiring_marquee.png` — the marquee

## Files to upload

- **Print profiles:** the 3MFs in `print/bambu-a1/` (or the P1S / X1C folders) — upload each as a Bambu
  Studio project; MakerWorld reads the plate and settings from it
- **Model files:** `print/stl/*.stl`
- Optional "other files": `model/pinball_controller_v2.scad` (editable source)

Firmware and the PC software stay on GitHub (MakerWorld only hosts print files); the description links to it.
