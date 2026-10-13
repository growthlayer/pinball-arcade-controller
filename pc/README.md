# PC setup (Windows)

What the PC needs so that the controller plays Visual Pinball X (VPX) and arcade games, and so that the
marquee, the exciter and the status screen do their jobs. Everything here was set up and tested on a
Windows 11 PC running [RetroBat](https://www.retrobat.org/) with VPX 10.8. Standalone VPX works the same
way; only the file locations differ.

The controller shows up as five USB devices behind its hub:

| Device | USB ID | Used for |
|---|---|---|
| Zero-delay encoder ("DragonRise") | 0079:0006 | buttons + joystick (a normal gamepad) |
| Pinscape Pico | 1209:EAEB | nudge, as gamepad axes |
| PCM2704 "USB Audio DAC" | 08BB:2704 | table sounds for the exciter |
| ESP32 + CP2102 (ZeDMD) | 10C4:EA60 | the 128 × 32 LED marquee (a COM port) |
| LilyGO T-Display-S3 | 303A:1001 | the status screen (a COM port) |

Check them in PowerShell:

```powershell
Get-PnpDevice -PresentOnly | ? InstanceId -match 'VID_0079|VID_1209|VID_08BB|VID_10C4|VID_303A'
```

If the CP2102 shows an error (code 28), let Windows Update install the "Silicon Laboratories – Ports"
driver (Settings → Windows Update → Advanced options → Optional updates).

---

## 1. Python and the helper programs

Three small Python programs run in the background (no windows):

| Program | What it does |
|---|---|
| [`tools/synthwave/marquee_service.py`](../tools/synthwave/marquee_service.py) | drives the marquee: the neon synthwave show when idle, the game's logo while you browse RetroBat, and hands the marquee to VPX's DMD during pinball |
| [`status-display/host/exciter_relay.py`](../status-display/host/exciter_relay.py) | copies the table sounds from a virtual sound cable to the USB sound card (see section 3) |
| [`status-display/host/pinball_status.py`](../status-display/host/pinball_status.py) | feeds the status screen: nudge meter, tilt warnings, coil heat, table name |

1. Install Python 3 from python.org (tick **Add to PATH**).
2. `pip install pygame pyserial numpy pillow sounddevice`
3. Download **libzedmd** for Windows x64 from the [libzedmd releases](https://github.com/PPUC/libzedmd/releases)
   and put `zedmd64.dll` next to `marquee_service.py` (or in a folder on PATH).
4. Status screen: copy `status-display/host/config.example.json` to `config.json` (see
   [status-display/README.md](../status-display/README.md) for the settings).
5. Start them at login: in the Startup folder (`Win+R` → `shell:startup`) make three shortcuts to
   `pythonw.exe` with the launcher as the argument:
   `tools\synthwave\start_marquee.pyw`, `status-display\host\start_exciter_relay.pyw`,
   `status-display\host\start_status.pyw`. Each runs one copy only and logs to
   `%LOCALAPPDATA%\pinball-status\`.

---

## 2. Visual Pinball X

### Buttons and nudge

In VPX's **Preferences → Keys / Controller** (or `VPinballX.ini`, with VPX closed):

| Setting | Value | Why |
|---|---|---|
| Left / right flipper | button **10 / 9** | the side buttons (encoder slots ST / SE) |
| Start / add credit | **12 / 11** | the back-edge buttons |
| Plunger | **7** | bottom row, right — any free button works |
| Pause, Exit game buttons | **none** (0) | a stray press mid-game shouldn't stop the table |
| Nudge: X axis / Y axis | **Pinscape Pico slider 1 / slider 2** (`LRAxis = 8`, `UDAxis = 7`) | the accelerometer, as acceleration |
| Flip the Y axis | **on** (`UDAxisFlip = 1`) | so a shove away from you moves the ball away |
| Accelerometer enabled, normal mount, no rotation | `PBWEnabled = 1` | |
| Gain X / Y | **300** (`PBWAccelGainX/Y`) | |
| Dead zone | **10 %** | you need a real shove, not a finger tap |
| Nudge filter | **on** (`EnableNudgeFilter = 1`) | smooths the accelerometer |
| Velocity input | off (`AccelVelocityInput = 0`) | |

[`firmware/pinscape_config.json`](../firmware/pinscape_config.json) puts the nudge on the Pico's gamepad
**slider 1 / slider 2** — VPX 10.8 has no Open Pinball Device support, and the sliders keep the nudge off
the gamepad X/Y that arcade games use.

The solenoid knock jolts the box too (about a third of a hard shove on the accelerometer). With the
dead zone at 10 % it doesn't nudge the ball; if your tables tilt on flipper presses, raise the dead zone or
lower the gain.

**RetroBat users:** RetroBat rewrites `VPinballX.ini` from its own settings each launch. In
`emulationstation\.emulationstation\es_settings.cfg` set `vpinball.vp_analognudge = 1` and
`vpinball.nouse_joyaxis = 1` (so it keeps the analogue nudge and doesn't map the joystick to nudge), and in
`system\padtokey\vpinball.keys` remove the joystick-to-nudge-key lines.

### Sound: table sounds to the exciter

VPX sends **backglass** sound (music, callouts) to one device and **playfield** sound (flippers,
bumpers, the ball) to another. Playfield → the exciter makes the table felt through the palms.

Windows gives the PCM2704 a new name each time it moves USB port ("2- USB Audio DAC", "3- …") and makes
it the default output when it appears. So instead of pointing VPX at the DAC directly:

1. Install [VB-CABLE](https://vb-audio.com/Cable/) (free virtual audio cable).
2. VPX: **Playfield sound → CABLE Input**, **Backglass sound → your speakers**.
3. `exciter_relay.py` copies CABLE Output to whatever device's name contains "USB Audio DAC", and
   reconnects by itself when the DAC comes and goes.
4. If Windows switched your default output to the DAC, switch it back to your speakers once.

Optional, with [Equalizer APO](https://sourceforge.net/projects/equalizerapo/) installed on the DAC: a
`Copy: L=0.5*L+0.5*R R=0.5*L+0.5*R` line folds the stereo playfield sound to mono, so the one exciter
channel gets both sides.

Optional, if pinball ROM sound is much quieter on your speakers than everything else: create an empty
`C:\Program Files\EqualizerAPO\config\pinball_tv.txt` (make it writable for your user) and add
`Include: pinball_tv.txt` under your speakers' `Device:` line in Equalizer APO's `config.txt`. The marquee
service then writes a +18 dB preamp with a limiter into it while a table runs, and 0 dB otherwise (it
uses the free [LoudMax](https://loudmax.blogspot.com/) VST as the limiter: put `LoudMax64.dll` in
Equalizer APO's `VSTPlugins` folder).

### The DMD on the marquee

1. Install [dmd-extensions](https://github.com/freezy/dmd-extensions) (RetroBat includes it).
2. In `DmdDevice.ini`: enable **ZeDMD** on the ESP32's COM port. **Leave every flip / rotate option
   off** — the picture is already turned in the ESP32 firmware.
3. Turn off VPX's own small on-screen DMD window if you only want the DMD on the marquee.

The marquee service lets go of the COM port while a pinball table runs and takes the marquee back when the
table closes.

---

## 3. RetroBat (arcade games)

Map the controller in RetroBat's controller settings like any gamepad: joystick for the D-pad / left
stick, the six buttons, coin = select, start = start. The flipper buttons (9 / 10) make good shoulder
buttons. Coin + Start together is the usual hotkey to quit a game.

The marquee shows the selected game's logo (`roms/<system>/images/<game>-marquee.png`, or its name in
neon if there's no logo) while you browse.

---

## 4. Checking it all

| Check | How |
|---|---|
| Every button | `joy.cpl` → the DragonRise device → press each button; numbers match the table in [README Step 3.3](../README.md#step-3--wire-it-up) |
| Flippers knock | each flipper press gives one knock on its own side (no PC needed — it's hardware) |
| Nudge | Pinscape Config Tool → nudge view, or `python tools/nudge_watch.py`: shove right/left/away/toward = right/left/back/front |
| Exciter | play any sound to "USB Audio DAC" — you feel it in the palm rest |
| Marquee | the neon show plays when nothing else is running |
| Status screen | shows the nudge dot moving when you shove the box |
