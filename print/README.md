# Printing the parts

Seven printed parts — **case**, **cover**, **two marquee trays**, **marquee plate**, **T-Display clamp**,
**exciter catch** — in PLA, no supports. Every file below comes with the print settings built in.

## Ready-to-print Bambu Studio projects

Pick the folder for your printer, open a file, press **Slice plate**, print.

| Folder | Printer |
|---|---|
| [`bambu-a1/`](bambu-a1/) | A1 (not the A1 mini — the case needs a 256 mm bed) |
| [`bambu-p1s/`](bambu-p1s/) | P1S / P1P |
| [`bambu-x1c/`](bambu-x1c/) | X1 Carbon / X1 / X1E |

| File | Contents | A1 time | PLA |
|---|---|---|---|
| `test_prints.3mf` | fit coupon (solenoid cradle, button hole, GX16 hole) + screw-post test — **print first** | ≈ 1.1 h | ≈ 34 g |
| `case.3mf` | the case, top face down, turned 90° | ≈ 12.6 h | ≈ 559 g |
| `cover.3mf` | the cover / electronics plate, feet side down, 4 mm brim | ≈ 5.2 h | ≈ 202 g |
| `marquee_trays.3mf` | both marquee trays, back down | ≈ 7.5 h | ≈ 338 g |
| `marquee_plate.3mf` | the plate that slides onto the case's rails | ≈ 2.2 h | ≈ 85 g |
| `small_parts.3mf` | T-Display clamp + exciter catch bridge | ≈ 0.3 h | ≈ 12 g |

All slice without warnings (checked with `tools/check_print_files.py`), with a 0.4 mm nozzle, Bambu PLA Matte (max flow 15 mm³/s — the case's solid top panel
under-extruded at the default) and 0.20 mm layers. Another Bambu printer with a 256 mm bed: open any of
them and switch the printer at the top-left of Bambu Studio — the process settings carry over.

## Other slicers (Prusa, Orca, Cura, …)

The plain models are in [`stl/`](stl/), already in print orientation. An STL can't carry settings, so use
the table below. Bed needed: 256 × 256 mm (the case is 235 × 254 as it lies on the bed).

| Setting | Case | Cover | Everything else |
|---|---|---|---|
| Orientation | as exported: top face down, **turned 90°** | as exported (feet recesses on the bed) | as exported |
| Layer / nozzle | 0.20 / 0.4 mm | same | same |
| Walls | 4 | 4 | 4 |
| Top / bottom layers | 5 / 5 | 5 / 5 | 5 / 5 |
| Infill | 20 % gyroid | 25 % gyroid | 20 % gyroid |
| Supports | none | none | none |
| Brim | **none** (no room) | 4 mm outer | none |
| Elephant-foot compensation | 0.15 mm | 0.15 mm | 0.15 mm |
| Seam | rear | rear | rear |
| Bed | 65 °C first layer, then 55 °C, textured PEI | same | same |
| Max volumetric speed | 15 mm³/s | 15 | 15 |

**The case** is the one to be careful with. It fills the bed, so it can't have a brim: wash the plate with
dish soap and water, keep fans, AC and open windows away, and let the bed cool before removing it. It is
exported turned 90° on purpose — printed the other way, the wide chamfered top layers reach the end of the
A1's X travel and the extruder faults at ~20 %.

## After printing

- **Heat-set inserts** (M3 × 5, Ø4.0 holes): ≈ 210 °C for PLA, press gently, keep the iron square.
- **Board posts** are blind 3.0 mm holes for M3 machine screws (2.35 for M2.5, 1.85 for M2): the first
  screw cuts the thread. Firm hand the first time, then stop when the board is snug.
- **Strikers**: glue a steel M4 washer on each striker face in the case side walls before the first knock.
- **PLA and heat**: fine at room temperature. If the cover's posts ever soften (hot room, endless flipper
  mashing), reprint only the cover in PETG.

## Rebuilding the files

After changing `model/pinball_controller_v2.scad`:

```
python tools/make_print_files.py
```

It exports every STL with OpenSCAD and builds the three printer folders with Bambu Studio (paths to both
programs can be given as arguments).
