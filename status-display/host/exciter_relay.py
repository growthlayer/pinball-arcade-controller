#!/usr/bin/env python3
"""Exciter audio relay: VB-CABLE -> controller's USB Audio DAC (the exciter), reconnecting after USB resets.

VPX opens its playfield sound device once per table and never reopens it, so when the controller hub resets the exciter
goes silent for the rest of the game. VPX now plays into VB-CABLE (a virtual device that never disappears) and this
relay copies CABLE Output -> the DAC over WASAPI (~20 ms). If the DAC drops off USB the stream stalls; a watchdog
notices, waits for the DAC to come back and reopens it.

Each new USB port gives the DAC a NEW Windows endpoint ("7- USB Audio DAC"), which starts at 50 % volume and without
Equalizer APO - the exciter went near-silent after the 2026-10-15 hub swap. So the relay does both jobs itself: it
folds stereo to mono (the exciter is on amp channel L only; right-panned flippers/ramps/drains need it) and sets the
DAC endpoint to 100 % every time it (re)opens. APO on the DAC is no longer needed.

  python exciter_relay.py        (normally started windowless by start_exciter_relay.pyw from the Startup folder)
"""
import time
import numpy as np
import sounddevice as sd

SRC = "CABLE Output (VB-Audio Virtual Cable)"
DST = "USB Audio DAC"                            # Windows renames it "2- USB Audio DAC" etc. per USB port
RATE, CH = 48000, 2
STALL = 1.0                                    # seconds without a callback = the DAC went away
LATENCY = "low"                                # ~50 ms total; 0.03 s/side (90 ms) made the flippers feel late
GAIN = 0.77                                    # the ONE exciter level knob (Windows volume is pinned at 100 %);
                                               # 1.0 at full test level was "almost too much" (2026-10-15)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def find(name, kind):
    for i, d in enumerate(sd.query_devices()):
        if sd.query_hostapis(d["hostapi"])["name"] == "Windows WASAPI" and name in d["name"] and d[f"max_{kind}_channels"] > 0:
            return i
    return None


def full_volume():
    """set every present 'USB Audio DAC' endpoint to 100 %, unmuted (a new endpoint starts at 50 %)"""
    try:
        import warnings
        from pycaw.pycaw import AudioUtilities
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for d in AudioUtilities.GetAllDevices():
                if d.FriendlyName and DST in d.FriendlyName and str(d.state).endswith("Active"):
                    v = d.EndpointVolume
                    if v.GetMasterVolumeLevelScalar() < 0.999 or v.GetMute():
                        log(f"{d.FriendlyName.strip()} was at {v.GetMasterVolumeLevelScalar() * 100:.0f} % - set to 100 %")
                        v.SetMasterVolumeLevelScalar(1.0, None)
                        v.SetMute(0, None)
    except Exception as e:
        log("could not set the DAC volume:", e)


def _room():
    """the room speakers (Windows' default output must stay there): "room_output" in config.json, a name fragment"""
    try:
        import json, os
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), encoding="utf8") as f:
            return json.load(f).get("room_output") or None
    except Exception:
        return None

ROOM = _room()                                 # None = leave the default alone (only warn)

def keep_default_off_dac():
    """Windows makes a newly enumerated USB audio device the DEFAULT output - then VPX's backglass/ROM sound
    (SoundDeviceBG = default) plays through the exciter instead of the TV (2026-10-15). Put the default back."""
    try:
        import warnings
        from pycaw.pycaw import AudioUtilities
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cur = AudioUtilities.GetSpeakers().FriendlyName or ""
            if DST not in cur:
                return
            room = [d for d in AudioUtilities.GetAllDevices()
                    if ROOM and d.FriendlyName and ROOM in d.FriendlyName and str(d.state).endswith("Active")]
            if room:
                AudioUtilities.SetDefaultDevice(room[0].id)
                log(f"Windows had made '{cur.strip()}' the default output - set it back to '{room[0].FriendlyName}'")
            else:
                log(f"default output is the exciter DAC - set 'room_output' in config.json (now {ROOM!r}) to fix it automatically")
    except Exception as e:
        log("could not check the default output:", e)


def refresh():
    """PortAudio caches the device list at init - re-init to see a DAC that re-enumerated"""
    sd._terminate()
    sd._initialize()


def main():
    last = [time.monotonic()]
    glitches = [0]

    def cb(indata, outdata, frames, t, status):
        outdata[:] = GAIN * indata.mean(axis=1, keepdims=True)    # mono on both channels: the exciter is on L only
        last[0] = time.monotonic()
        if status.input_overflow or status.output_underflow:
            glitches[0] += 1

    missing_logged = False
    while True:
        refresh()
        i, o = find(SRC, "input"), find(DST, "output")
        if i is None or o is None:
            if not missing_logged:
                log("waiting for", "VB-CABLE" if i is None else "the exciter DAC")
                missing_logged = True
            time.sleep(1.0)
            continue
        missing_logged = False
        try:
            wasapi = sd.WasapiSettings(auto_convert=True)
            with sd.Stream(device=(i, o), samplerate=RATE, channels=CH, dtype="float32", latency=LATENCY,
                           extra_settings=(wasapi, wasapi), callback=cb) as s:
                log(f"relaying VB-CABLE -> exciter DAC (latency in {s.latency[0] * 1000:.0f} ms, out {s.latency[1] * 1000:.0f} ms)")
                full_volume()
                keep_default_off_dac()
                last[0] = time.monotonic()
                reported, next_report = 0, time.monotonic() + 30
                while s.active and time.monotonic() - last[0] < STALL:
                    time.sleep(0.25)
                    if time.monotonic() >= next_report:
                        next_report += 30
                        if glitches[0] != reported:
                            log(f"{glitches[0] - reported} audio glitches (over/underruns) in the last 30 s")
                            reported = glitches[0]
                log("stream stalled - DAC gone (USB reset?) - reopening")
        except Exception as e:                  # device vanished mid-open etc.
            log("stream error:", e)
        time.sleep(1.0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
