#!/usr/bin/env python3
"""Exciter audio relay: VB-CABLE -> controller's USB Audio DAC (the exciter), reconnecting after USB resets.

VPX opens its playfield sound device once per table and never reopens it, so when the controller hub resets the exciter
goes silent for the rest of the game. VPX now plays into VB-CABLE (a virtual device that never disappears) and this
relay copies CABLE Output -> the DAC over WASAPI (~20 ms). If the DAC drops off USB the stream stalls; a watchdog
notices, waits for the DAC to come back and reopens it. Equalizer APO's mono fold-down on the DAC still applies.

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


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def find(name, kind):
    for i, d in enumerate(sd.query_devices()):
        if sd.query_hostapis(d["hostapi"])["name"] == "Windows WASAPI" and name in d["name"] and d[f"max_{kind}_channels"] > 0:
            return i
    return None


def refresh():
    """PortAudio caches the device list at init - re-init to see a DAC that re-enumerated"""
    sd._terminate()
    sd._initialize()


def main():
    last = [time.monotonic()]
    glitches = [0]

    def cb(indata, outdata, frames, t, status):
        outdata[:] = indata
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
