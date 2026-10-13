// =====================================================================
//  Pinball / arcade controller case — v2
//  Bigger box, second side button per side (nudge), solenoid mounts,
//  rounded grip edges, DC jack + USB on the back wall.
//
//  Units: mm.  Coordinates are "as used", arcade orientation:
//     X = left -> right (as the player sees it)
//     Y = front (0) -> back      (coin/start and the USB port are at the back)
//     Z = bottom (cover) -> top panel
//  For pinball the box is turned 180° so the side (flipper/nudge) buttons and
//  coin/start are at the player's hands.
//  The original STEP was modelled top-face-down. Print the CASE top-face
//  down (rotate 180° about X in the slicer); print the COVER as-is.
//
//  Original values are noted as "(orig ...)" so you can compare.
// =====================================================================

part = "print_all";   // ["print_all", "td_clamp", "td_test", "hub_carrier", "case", "case_print", "cover", "test_fit", "assembly", "cover_loaded", "case_loaded", "marquee", "marquee_loaded", "marquee_left", "marquee_right", "screw_test", "joy_clamp"]
show_components = true;   // draw the non-printed parts (buttons, boards, solenoids...) in "assembly" and "cover_loaded" only

// ---------------- Overall size ----------------
W = 254;              // width  (orig 254)  -> max for a 256 mm bed
D = 230;              // depth  (orig 190)  -> extra depth hosts solenoids/electronics
H = 85;               // height (orig 64)   -> taller sides = better grip

wall     = 5;         // side wall thickness (orig 5)
top_t    = 4;         // top panel thickness (orig 4)
cover_t  = 4;         // cover thickness (orig 3)
ledge    = 2;         // width of the ledge the cover sits on
corner_r = 10;        // vertical corner radius (orig 5 mm chamfer)
edge_c   = 2;         // top-edge 45° chamfer: 6 -> 2 mm (2026-09-30: the 6 mm chamfer printed rough with curled corners - it is the first overhang off the bed) (orig 5). Chamfer, not a fillet, so the case prints top-face-down cleanly. Must be < corner_r
clr      = 0.2;       // clearance per side for the cover

// ---------------- Buttons ----------------
btn_d      = 28;      // arcade button hole (orig 28; use 30 for Sanwa OBSF-30)
btn_drop   = 35;      // side button centre below the top face (orig 34)
start_d    = 28;      // coin/start button hole (STEP says 28 — set 24 if yours are the small ones)
flipper_yb = 40.9;    // flipper button centre from the BACK face (orig 40.9)
nudge_off  = 0;       // nudge button this far in front of the flipper; 0 = none (nudging is done by the accelerometer)
nudge_d    = 28;      // nudge button hole (24 if you want smaller buttons)

// ---------------- Top layout (kept from original) ----------------
// All positions are measured from the LEFT edge and the BACK edge (yb), exactly
// as in the original 254 x 190 box, so coin/start, flippers, USB and the PCB
// stay put and the extra depth becomes palm rest at the front.
dx = (W - 254) / 2;         // if W grows, the layout stays centred
layout_shift = 0;           // move the whole top layout toward the front (mm), e.g. 20
function fb(p) = [p[0] + dx, D - p[1] - layout_shift];   // (x, yb) -> model coords

start_btns_b = [[81, 26.75], [173, 26.75]];              // coin / start, back edge
six_btns_b   = [[138.1,113.01],[138.1,158.01],
                [178.1, 93.01],[178.1,138.01],
                [218.1, 73.01],[218.1,118.01]];
joy_c_b      = [57, 113.97];
joy_c        = fb(joy_c_b);
joy_pitch  = [40, 81];    // screw pattern (orig 40 x 81)
joy_shaft  = 20;          // shaft hole (orig 20; Sanwa JLF prefers 24)
joy_mount  = "countersunk"; // ["countersunk", "clamp"]
//   "clamp":       hidden — the joystick plate is pressed against the panel underside by a printed
//                  frame (part = "joy_clamp") screwed into bosses outside the plate. Stick height unchanged.
//   "countersunk": original — screws through the top with countersinks.
joy_plate    = [54, 95];  // joystick mounting plate w x d - maker drawing 2026-09-30 (95 x 54; body 35 below the plate)
joy_plate_t  = 1.6;       // plate thickness
joy_overlap  = 6;         // how far the clamp frame overlaps the plate edge (keep clear of the stick body)
joy_boss_d   = 8;         // boss diameter
joy_boss_hole = 4.0;      // 4.0 = M3 heat-set insert, 2.5 = M3 self-tapping
joy_boss_gap = 1;         // gap between plate edge and boss
joy_frame_t  = 4;         // clamp frame thickness (use 6 if joy_mid_bosses = false)
joy_mid_bosses = true;    // add a boss mid-way along each long side (6 screws) so the frame can't bow; false = 4 corners
joy_screw_d  = 3.4;       // M3 clearance in the frame
joy_screw  = 5.4;         // countersunk mode: through hole (orig 5.4)
joy_csk    = 8.4;         // countersunk mode: countersink dia at surface (orig 8.4)

// PCB standoffs under the top panel (orig 29.4 x 80.3 pattern, 7.2 od, 3.6 hole)
pcb_posts_b   = [[112.3,10.5],[141.7,10.5],[112.3,90.8],[141.7,90.8]];
pcb_posts     = [for (p = pcb_posts_b) fb(p)];
pcb_post_od   = 7.2;
pcb_post_hole = 3.0;     // M3 machine screw straight into PLA (screw test 2026-09-26); was 3.6 (inherited, too loose for M3)
pcb_post_h    = 6;
pcb_hole_into_panel = 2;  // blind hole continues 2 mm into the 4 mm top panel -> 8 mm deep: M3x8 through a 1.6 mm board

// Second PCB mount for the solenoid driver board (set drv_size = [0,0] to disable)
drv_size   = [0, 0];          // generic 4-post PCB mount, disabled (XY-J02 boards use card guides below)
drv_centre = [W/2, wall+25];     // front centre, under the palm rest (back centre is taken by the encoder)
drv_inset  = 3.5;             // hole inset from board edge

// ---------------- Rear wall ports ----------------
enc_usb_cutout = false;       // original cutout for the encoder's own USB socket — not needed now the encoder plugs into the internal hub
usb_w = 12.3; usb_h = 10.9;   // USB cutout (orig 12.3 x 10.9)
usb_top_drop = 8.9;           // top of cutout below top face (orig 8.9)
usb_flange_w = 19.4; usb_flange_h = 19.75; usb_flange_deep = 3; // flange pocket (orig)
usb_x = W/2;                  // lines up with the encoder board USB socket, as original
dc_jack_d = 11.5;             // DC-099 jack with 11 mm mounting hole (5.5x2.5, 10 A)
port_wall = "back";           // ["back", "left"]  Back wall, low and side by side (below every button housing).
port_z    = 22;               // connector centres above the cover (the lower wall is clear of all button housings)
dc_y      = 83;               // along the left wall, from the arcade front
usb_panel_y = 55;
dc_x = 172;                   // back wall, low, beside the USB port — one cable exit
dc_drop = H - 22;             // jack centre 22 mm above the cover: the lower back wall is clear of every button housing
mq_gx_x = 197;                // 2026-10-01: ONE cable to the marquee - a 2nd GX16-8 socket ("DMD") where the
                              //   USB-C port was; replaces the DC jack + USB-C panel port. 0 = the old jack + USB-C pair.
                              //   Same pinout as the tether (1-2 +12 V, 3-4 0 V, 5 VBUS, 6 D-, 7 D+, 8 USB GND).
gx_label = true;              // debossed "DMD" / "IN" under the two GX16 sockets
gx_d = 16.3;                  // GX16-8 tether socket from the table node (12 V + USB on one cable); 0 = no socket
gx_x = 222;                   // right of the USB-C port, same 22 mm line. NOT the suggested ~140: left of the jack
                              // the hole clips the back mid-tab (x 121-133) and the socket's ~22 mm body runs into
                              // the amp (cover, x 93-161, y to 212). Pinout contract in CLAUDE.md - both tether ends
                              // are wired pin-for-pin; never change one end alone.

// ---------------- Solenoids (JF-1039 / JF-1039B 12 V) ----------------
use_solenoids = true;
sol_mount = "cover";    // ["cover", "rib"]
//  "cover": solenoid bolted to the cover plate, lying on its side against the side wall, plunger
//           aimed at a striker block between the flipper and nudge buttons. Best feel, wires need a
//           connector so the cover can come off.  "rib": older front-strip rib mount, kept for reference.
sol_body       = [39, 20, 26];  // body L (along plunger axis) x W x H — JF-1039B is 39 x 20 x 26
sol_hole_pitch = 22;    // JF-1039 datasheet: 2-M4 tapped holes, DIAGONAL pattern in the 39.5 x 20 face:
sol_hole_lat   = 14;    //   22 apart along the plunger axis, 14 apart across it (3 in from each edge),
sol_hole_face  = 16.5;  //   pair centre 16.5 behind the rod-end face (holes at 5.5 and 27.5 from it).
sol_slot_w     = 4.5;   // M4 clearance — the frame is tapped M4, machine screws thread straight in
sol_slot_len   = 36;    // both slots full length at +/-7 lateral: catches the holes on EITHER diagonal
                        //   (chirality-immune) and leaves +/-7 mm of rod-gap adjustment
sol_rod_out    = 25;    // MEASURED 2026-09-08: fork tip 25 out at rest, 15 pressed (10 mm stroke).
                        // NOTE: these units are PULL-type — energize retracts the fork; nothing exits the
                        // rear. The knock comes from the plunger hitting the internal end-stop (real-knocker
                        // style); the wall strikers are inert unless the slotted-pylon upgrade happens.
sol_gap        = -3;    // 3 mm spring PRELOAD against the striker — NOT a gap. Bench-tested 2026-09-08:
                        // the plunger is NOT captive (nothing stops the out-stroke), so the striker is
                        // structural: it retains the plunger and takes the spring-launched knock when the
                        // relay drops. Never fire a solenoid without the striker (or a hand) in front of
                        // it. Slots tune preload depth; the tip must always touch at rest.
striker_t      = 6;     // striker block thickness on the inside of the side wall
sol_offset     = 29;    // solenoid centre this far in front of the flipper button centre (just clear of its housing)
sol_pad_h      = 2;     // raised pad under the solenoid on the cover
sol_rail_h     = 6;     // locating rails either side of the body
// rib-mode leftovers
sol_rib_t = 4; sol_rib_h = 40; sol_rib_y = wall + 30; sol_rib_gap = 14;

// ---------------- XY-J02 timer relay boards ----------------
// Boards stand on edge along the front wall in vertical slots and slide UP from below (cover off)
// until they hit the top panel. No screw holes needed; components face the box interior.
xyj_n      = 0;             // 0 = relay boards live on the cover instead (see cover_pcbs)
xyj_board  = [62, 38, 1.6];   // length between the slots (X), height (Z), PCB thickness
xyj_clr    = 0.4;             // slot width allowance
xyj_pos    = [[22, 12], [W - 22 - 70, 12]];   // front corners, clear of the 14 mm corner posts: [x of left slot post, y of board plane]; each pair spans 70 mm in X
xyj_post   = 6;               // slot post size (X and Y)
xyj_groove = 2.2;             // groove depth into each post

// ---------------- Bass exciter (SSF) ----------------
// Glues to the underside of the top panel; a low ring locates it. Set exc_d = 0 to remove.
exc_d   = 50;                 // 50 mm vibration speaker (ALIA 25 W 4 ohm), adhesive face, body must stay free
exc_pos = [110, 34];          // under the palms; ring clears the front wall by 1.5 mm and the front-most button housing by ~3 mm

// ---------------- Status display: LilyGO T-Display-S3 in the top panel, front-right palm rest ----------------
// Chosen 2026-09-26 (only spot clear of the fixed layout). The clear front plate drops into a pocket
// on the panel underside, a 45°-chamfered window shows the pixels, and a printed clamp (part = "td_clamp")
// presses the two black header strips (pins clipped flush) through foam, screwed to four posts. The clamp
// stays off both board ends: the USB end carries three white connectors (B = 10 mm, 1 mm below the strips).
td_on       = true;
td_win_c    = [180, 32];      // visible-area centre (case coords); USB end toward +X (reads correctly that way)
td_active   = [43, 23];       // visible pixels, MEASURED (FRAME mode) 2026-09-26
td_win_m    = 0.5;            // window margin per side, so +/-0.5 misalignment can't clip pixels
td_board    = [56.2, 25.8];   // clear plate / board outline, MEASURED
td_act_off  = 0.6;            // pixels sit this far toward the LILYGO (-X) end of the board centre (photo estimate)
td_pocket_d = 1.5;            // plate sinks this far into the 4 mm panel -> 2.5 mm skin at the window
td_pocket_clr = 0.2;
td_A        = 9.0;            // front face -> bottom of the header strips, MEASURED (6.7 at the bare-board end)
td_foam     = 1.0;            // compressed foam between clamp and strips (1.5 mm foam tape)
td_clamp    = [40, 42, 3];    // clamp plate: along X, across Y, thickness
td_clamp_dx = -2;             // clamp centre vs board centre: nudged toward the LILYGO end, away from the connectors
td_post_xy  = [15, 18.5];     // post offsets from the clamp centre
td_post_od  = 7;
td_relief   = [19, 1.0];      // clamp top-face groove (width across Y, depth): only the strips touch
td_clamp_raise = 0;           // raised lands under the header strips (fit test 2026-09-26: no foam -> 1-2 mm loose;
                              //   variants at 1.2 / 1.8 exist; foam tape was chosen instead -> keep 0, use ~2 mm foam)
td_bc       = [td_win_c[0] + td_act_off, td_win_c[1]];                 // board centre
td_cc       = [td_bc[0] + td_clamp_dx, td_bc[1]];                      // clamp centre
td_post_h   = td_A + td_foam - td_pocket_d;                            // panel underside -> clamp top face

// ---------------- Small PCBs hanging from the top panel ----------------
// [cx, cy, hole_pitch_x, hole_pitch_y, hole_d, post_od]
misc_pcbs = [];               // nothing left under the panel — see cover_pcbs
misc_post_h = 6;

// ---------------- Electronics on the COVER plate (posts up) ----------------
// [cx, cy, hole_pitch_x, hole_pitch_y, screw, post_od, part_w, part_d, part_h, n_holes]  in CASE coords
// screw = metric size of the MACHINE screw (3 = M3, 2.5 = M2.5, 2 = M2).
pcb_fix = "machine";   // ["machine", "nut", "selftap"]
//   machine (chosen 2026-09-22): ordinary machine screw driven straight into the PLA post - it forms its
//           own thread on first insertion. M3 hole 3.0 (screw test 2026-09-26: 2.9 and 3.0 both
//           grip on the A1; 3.0 chosen as less likely to split the post);
//           posts grow to screw + 4 mm OD so the forming pressure can't split them.
//   nut:    clearance hole through post + cover, hex pocket for a nut underneath.
//   selftap: the original 2.5 / 2.0 / 1.6 pilots for self-tapping screws.
// part_w/d/h = outline and total height above the posts (for the clearance check below).
// Hole pitches marked ?? are placeholders — replace with measured values when the parts arrive.
// Last field: number of holes — 4 (corners) or 2 (diagonal: -x-y and +x+y corners)
cover_pcbs = [
    [127, 166, 61, 85,  3,   6, 68, 92, 20, 4],   // XH-M543 TPA3116D2 stereo amp 92 x 68 x ~20, long axis along Y. holes MEASURED 85 x 61 (2026-09-11)
    [52,  27,  55, 32,  3,   6, 62, 38, 17, 4],   // XY-J02 #1 (left flipper), front-left of cover. holes MEASURED 55 x 32
    [202, 31,  55, 32,  3,   6, 62, 38, 17, 4],   // XY-J02 #2 (right flipper), front-right. holes MEASURED 55 x 32
    [190, 110, 11.4, 47, 2,   4.5, 21, 51, 10, 4, 7, 4.5, 8.4],  // Pico H, PINS UP (Dupont jumpers), USB toward the front: 7 mm tall, 4.5 OD
                                                  //   posts. Holes 11.4 x 47, M2. Field 12 = 8.4 mm slot between the two FRONT posts:
                                                  //   the flipped board's micro-USB SOCKET (8 wide) hangs between them and the round posts
                                                  //   left only 6.9 (the first cover v2 had to be shaved, 2026-10-02). Leaves ~0.55 mm of wall
                                                  //   on the inner side of those two holes - drive their screws gently.
    [225, 120, 0, 23,   2.5, 6, 20, 30, 5,  2],   // LIS3DH breakout: 2 holes IN LINE, 23 apart along the long side (MEASURED 2026-09-11;
                                                  //   pitch_x 0 turns the 2-hole pattern into a straight pair along Y). Outline 20 x 30 is a
                                                  //   conservative envelope - clears the wall and the Pico either side. Rigid, axes square to the box.
    [45.2, 95.2, 38.5, 78.4, 3, 7, 44, 84, 16, 4], // 7-port hub FE2.1 (cover v2): 84 x 44, holes 78.4 x 38.5 MEASURED. Ports face +X into the open
                                                  //   centre (use the 5 front ones); 5 V jack (wires soldered) + micro-USB face the left wall
    // PCM2704 DAC: plugs into the hub, no mount. 3.5 mm cable to the amp.
];
cover_post_h = 5;
function post_h(b) = len(b) > 10 ? b[10] : cover_post_h;   // optional per-board post height (field 10) and OD (field 11)

// Clearance check: how far the deepest button + microswitch reaches below the panel underside.
btn_depth = 40;   // 35 mm for the button + microswitch, plus 5 mm for the spade connectors and wire bend (measured)
joy_depth = 37;   // joystick body below the panel underside: 35 below the 1.6 plate (maker drawing 2026-09-30)
free_under_btn = H - top_t - btn_depth - cover_t;      // height available above the cover under a button
free_under_joy = H - top_t - joy_depth - cover_t;
function under_circle(b, c, r) = let(hw = b[6]/2, hd = b[7]/2)
    (abs(b[0] - c[0]) < hw + r) && (abs(b[1] - c[1]) < hd + r);   // conservative box-vs-circle overlap
function under_rect(b, c, w, d) = (abs(b[0] - c[0]) < (b[6] + w)/2) && (abs(b[1] - c[1]) < (b[7] + d)/2);
for (b = cover_pcbs) {
    ph = post_h(b) + b[8];
    for (p = six_btns_b)   if (under_circle(b, fb(p), btn_d/2 + 3) && ph > free_under_btn)
        echo(str("WARNING: cover part at ", [b[0], b[1]], " (", ph, " mm tall) is under an arcade button; only ", free_under_btn, " mm free."));
    for (p = start_btns_b) if (under_circle(b, fb(p), start_d/2 + 3) && ph > free_under_btn)
        echo(str("WARNING: cover part at ", [b[0], b[1]], " (", ph, " mm tall) is under coin/start; only ", free_under_btn, " mm free."));
    if (under_rect(b, joy_c, joy_plate[0], joy_plate[1]) && ph > free_under_joy)
        echo(str("WARNING: cover part at ", [b[0], b[1]], " (", ph, " mm tall) is under the joystick; only ", free_under_joy, " mm free."));
}

// GX16 socket body clearance: ring nut + solder cups reach ~22 mm behind the back wall at the jack line.
if (gx_d > 0) for (gxx = [gx_x, mq_gx_x]) if (gxx > 0) for (b = cover_pcbs) {
    gz0 = 22 - 10; gz1 = 22 + 10;                       // socket body z window (centre 22, nut r ~10)
    bz0 = cover_t + clr + post_h(b); bz1 = bz0 + b[8];
    if (abs(b[0] - gxx) < b[6]/2 + 10 && (D - wall) - (b[1] + b[7]/2) < 22 && gz0 < bz1 && gz1 > bz0)
        echo(str("WARNING: GX16 socket body at x=", gxx, " overlaps the cover part at ", [b[0], b[1]]));
}

// ---------------- Panel-mount USB (PC cable in, feeds the hub) ----------------
usb_panel      = (mq_gx_x == 0);   // retired by the marquee GX16 link
usb_panel_x    = 197;                // beside the 12 V jack; 197 (not 200) keeps the flange pocket ~2.5 mm clear of the GX16 ring nut
usb_panel_drop = H - 22;             // centre 22 mm above the cover, level with the DC jack (18-below-top contradicted the side-by-side decision)
usb_panel_cut  = [11, 6];            // through-cutout w x h: passes the raised socket (9 x 3.3, MEASURED 2026-09-26) with 1 mm margin.
                                     //   Was 13 x 7 - with 3.4 clearance holes that left a 0.3 mm web to the screw holes.
usb_panel_screw_pitch = 17;          // flange screw spacing, MEASURED 17 mm centre-to-centre (2026-09-26)
usb_panel_screw_d     = 3.4;         // CLEARANCE: the flange mounts INSIDE the wall with threaded holes (confirmed 2026-09-26);
                                     //   the supplied M3 screws go in from outside through the wall into the flange
usb_panel_flange = [25.3, 10.5];     // flange w x h, MEASURED 2026-09-26 (5.2 thick)
usb_panel_skin   = 2;                // wall left in front of the flange - the supplied screws are sized for a thin panel,
                                     //   and a plug must reach the socket through it. Pocket = flange + 0.35 each side.

// RULE (2026-10-01): every joint between PRINTED parts = M3 heat-set insert + M3 machine screw. No pins / glue.
m3_ins_d = 4.0;       // hole for the M3 heat-set inserts (melt in with the iron; standard M3 x 5 x ~4.6 OD)
m3_ins_l = 5.5;       // hole depth = insert length 5 + 0.5

// ---------------- Cover fixings ----------------
post_size   = 14;     // corner post square (orig 14)
post_inset  = 12;     // insert hole centre from outer edges (orig 12)
post_h      = 15;
insert_d    = m3_ins_d;   // M3 heat-set insert (was M4 until 2026-10-01 - rule: M3 inserts everywhere)
insert_deep = 8;
cover_csk_d = 6.4;    // countersink for an M3 flat head
cover_hole_d = 3.4;
mid_tabs    = true;   // extra screw tab at mid front / mid back
feet_d      = 13.0; feet_recess = 1.2; // 3M Bumpon SJ5312 (12.7 x 3.5) recesses: 0.3 clearance, foot ~2.3 proud,
                                       // recess wall takes nudge shear. Shared standard with the trackball controller.

// ---------------- Slide-on marquee module (optional) ----------------
// A DMD marquee that slides onto dovetail rails on the OUTSIDE of the front and
// back walls (same rail pair on both, symmetric about W/2, so the module moves to
// whichever end faces away from the player: back for arcade, front for pinball).
// Sized for a P2 128x32 HUB75 LED panel (256 x 64 mm) driven by an ESP32 (ZeDMD)
// with a 12 V -> 5 V buck on the module. Panel outline is nominal — MEASURE the
// actual panel before printing the head.
marquee_rails = true;      // print the rails on the case walls
mq_rail_x  = [54, 200];    // rail centres — clear of the corner rounding and the port zone
mq_z0 = 40; mq_z1 = 79;    // rail span: above the jack/USB plugs, ending at the top chamfer
mq_root = 10; mq_crest = 14; mq_deep = 5;   // male dovetail cross-section
mq_slide_clr = 0.3;
mq_rail_screw_z = 52;     // plate -> rail screw height (case z): low on the rail, where it is thickest        // per-face sliding clearance — tune on a test print
mq_gap     = 0.2;          // plate stand-off from the wall
mq_plate_t = 8;            // module back-plate thickness (5.3 groove + web)
mq_plate_w = 230;
mq_panel = [320, 80, 15];  // 2 x P2.5 64x32 HUB75 panels chained, each MEASURED 160 x 80 x 15 (2026-09-28)
mq_panel_m3  = [[-62.5, -32.5], [62.5, -32.5], [-62.5, 32.5], [62.5, 32.5],   // M3 brass inserts per 160 x 80 panel,
                [-12.5, 32.5], [12.5, -32.5]];                                // from the panel centre, in FRONT-VIEW coords:
                                                                             // corners on 125 x 65, plus two mid ones
mq_panel_pins = [[-72.5, 15.5], [72.5, -15.5]];   /* maker's drawing is the BACK view: x mirrored here (v1 had it unmirrored - pins landed at the wrong diagonal, fit test 2026-09-29) */                               // moulded locating PINS on the panel back (maker's drawing; fit test 2026-09-29) - the flange has 4.5 mm holes for them
mq_tilt  = 30;             // head lean-back, degrees — face meets the sightline of a seated player looking down at a table
mq_wall  = "back";         // the marquee lives on the BACK wall (coin/start edge) — classic arcade-marquee
                           // position: screen, rails and ports all on the wall away from the player. The front
                           // (palm-rest) wall stays bare. "front" kept for experiments only (no rails there).

// ---------------- Anti-curl mouse ears (print aid, case only) ----------------
print_ears = false;   // OFF (2026-09-26: no anti-curl tabs on any part). When on: breakaway 0.6 mm discs on the print's bed face (the top panel). Front/back
                      // edges only: at 254 mm wide there is no bed room for ears or brim in X on the A1.
                      // Snap off and trim flush after the print. The top-face outline is inset 6 mm by
                      // the chamfer, so the discs sit on that contact edge, half on the part, half on the bed.

$fn = 64;
eps = 0.01;

// =====================================================================
//  Helpers
// =====================================================================
// ---------------- Zip-tie mounts (placed by docs/cable_router.py -> model/tie_points.scad) ----------------
include <tie_points.scad>
tie_mount = [10, 7, 5];        // across the cable, along it, height
module tie_mount_block() {     // origin: centre of the base; cable runs along +X; the tunnel runs ACROSS (Y)
    difference() {
        translate([-tie_mount[1]/2, -tie_mount[0]/2, 0]) cube([tie_mount[1], tie_mount[0], tie_mount[2]]);
        translate([-2.25, -tie_mount[0]/2 - 1, 1.2]) cube([4.5, tie_mount[0] + 2, 2]);    // 4.5 x 2 tunnel for 4 mm ties
    }
}
module rrect(w, d, h, r) {
    hull() for (x = [r, w - r], y = [r, d - r]) translate([x, y, 0]) cylinder(r = r, h = h);
}

// Outer shell: rounded vertical corners + 45° chamfered top edge, flat bottom
module shell_outer() {
    hull() for (x = [corner_r, W - corner_r], y = [corner_r, D - corner_r]) {
        translate([x, y, 0]) cylinder(r = corner_r, h = H - edge_c);
        translate([x, y, H - edge_c]) cylinder(r1 = corner_r, r2 = corner_r - edge_c, h = edge_c);
    }
}

module cavity() {
    translate([wall, wall, -1]) rrect(W - 2*wall, D - 2*wall, H - top_t + 1, corner_r - wall);
}

module rebate() {
    translate([wall - ledge, wall - ledge, -1])
        rrect(W - 2*(wall - ledge), D - 2*(wall - ledge), cover_t + clr + 1, corner_r - wall + ledge);
}

ledge_z = cover_t + clr;   // top of the ledge = bottom of everything inside

// Right-angle gusset in the YZ plane, extruded along X. polygon x -> Y, y -> Z
module gusset(g, t) {
    rotate([90, 0, 90]) linear_extrude(t) polygon([[0, 0], [g, 0], [0, -g]]);
}

// =====================================================================
//  Internal features (all unioned into the shell, then holes cut)
// =====================================================================
module corner_posts() {
    for (x = [wall, W - wall - post_size], y = [wall, D - wall - post_size]) {
        translate([x, y, ledge_z - eps]) cube([post_size, post_size, post_h]);
        // 45° wedge rising into the wall corner: the case prints top-face-down, where the bare post top was a
        // 14 mm floating cantilever (Bambu Studio flagged it 2026-09-26). Faces are exactly 45°.
        cx = x < W/2 ? wall : W - wall - eps;  cy = y < D/2 ? wall : D - wall - eps;
        hull() {
            translate([x, y, ledge_z + post_h - 2*eps]) cube([post_size, post_size, eps]);
            translate([cx, cy, ledge_z + post_h + post_size - eps]) cube([eps, eps, eps]);
        }
    }
}
module corner_post_holes() {
    for (x = [post_inset, W - post_inset], y = [post_inset, D - post_inset])
        translate([x, y, ledge_z - 1]) cylinder(d = insert_d, h = insert_deep + 1);
}

tab_w = 12; tab_d = 12; tab_h = 15;
module mid_tabs_body() {
    if (mid_tabs) for (m = [0, 1]) mirror([0, m, 0]) translate([0, m ? -D : 0, 0]) {
        translate([W/2 - tab_w/2, wall - eps, ledge_z - eps]) cube([tab_w, tab_d, tab_h]);
        // 45° gusset from the tab top up the wall (orig had the same)
        translate([W/2 - tab_w/2, wall - eps, ledge_z + tab_h - eps])
            rotate([90, 0, 90]) linear_extrude(tab_w) polygon([[0, 0], [tab_d, 0], [0, tab_d]]);
    }
}
module mid_tab_holes() {
    if (mid_tabs) for (y = [wall + tab_d/2, D - wall - tab_d/2])
        translate([W/2, y, ledge_z - 1]) cylinder(d = insert_d, h = insert_deep + 1);
}

module pcb_standoffs(list, od, hole, h) {
    for (p = list) translate([p[0], p[1], H - top_t - h + eps]) cylinder(d = od, h = h);
}
module pcb_standoff_holes(list, hole, h) {
    for (p = list) translate([p[0], p[1], H - top_t - h - 1]) cylinder(d = hole, h = h + 1 + pcb_hole_into_panel);
}
drv_posts = (drv_size[0] > 0) ?
    [for (sx = [-1, 1], sy = [-1, 1])
        [drv_centre[0] + sx*(drv_size[0]/2 - drv_inset), drv_centre[1] + sy*(drv_size[1]/2 - drv_inset)]]
    : [];

// Clamp bosses: 4 corners + 2 mid long sides, just outside the plate outline
bx = joy_plate[0]/2 + joy_boss_gap + joy_boss_d/2;
by = joy_plate[1]/2 + joy_boss_gap + joy_boss_d/2;
joy_bosses = concat([for (sx = [-1, 1], sy = [-1, 1]) [sx*bx, sy*by]],
                    joy_mid_bosses ? [[-bx, 0], [bx, 0]] : []);
joy_boss_h = joy_plate_t + 2;             // boss pokes 2 mm into a counterbore in the frame
joy_boss_deep = joy_boss_h + top_t - 1.5; // blind hole, leaves 1.5 mm of top surface

module joystick_bosses() {
    if (joy_mount == "clamp")
        for (b = joy_bosses)
            translate([joy_c[0] + b[0], joy_c[1] + b[1], H - top_t - joy_boss_h + eps])
                cylinder(d = joy_boss_d, h = joy_boss_h);
}
module joystick_boss_holes() {
    if (joy_mount == "clamp")
        for (b = joy_bosses)
            translate([joy_c[0] + b[0], joy_c[1] + b[1], H - top_t - joy_boss_h - 1])
                cylinder(d = joy_boss_hole, h = joy_boss_deep + 1);
}

// Printed frame that clamps the joystick plate. Print flat (plate side up as modelled).
module joy_clamp() {
    fw = 2*bx + joy_boss_d + 2;  fd = 2*by + joy_boss_d + 2;     // outer size
    ow = joy_plate[0] - 2*joy_overlap;  od = joy_plate[1] - 2*joy_overlap; // opening
    difference() {
        translate([-fw/2, -fd/2, 0]) rrect(fw, fd, joy_frame_t, 5);
        translate([-ow/2, -od/2, -1]) rrect(ow, od, joy_frame_t + 2, 3);
        for (b = joy_bosses) translate([b[0], b[1], 0]) {
            translate([0, 0, -1]) cylinder(d = joy_screw_d, h = joy_frame_t + 2);
            translate([0, 0, joy_frame_t - 2]) cylinder(d = joy_boss_d + 0.4, h = 3);  // boss counterbore (plate side)
        }
    }
}

sol_rib_len = max(sol_hole_pitch + sol_slot_len + 20, sol_body[0] + 20);

module solenoid_rib() {   // origin: front-left-bottom of the rib, rib runs along +X
    difference() {
        union() {
            cube([sol_rib_len, sol_rib_t, sol_rib_h]);
            for (x = [0, sol_rib_len - 4])
                translate([x, sol_rib_t, sol_rib_h]) gusset(12, 4);      // back-side gussets
            for (x = [0, sol_rib_len - 4])
                translate([x, 0, sol_rib_h]) mirror([0, 1, 0]) gusset(6, 4); // small front gussets
        }
        for (s = [-1, 1])
            translate([sol_rib_len/2 + s*sol_hole_pitch/2, -1, sol_rib_h/2])
                hull() for (x = [-sol_slot_len/2, sol_slot_len/2])
                    translate([x, 0, 0]) rotate([-90, 0, 0]) cylinder(d = sol_slot_w, h = sol_rib_t + 2);
    }
}
sol_y = D - flipper_yb - sol_offset;                          // just in front of the flipper housing
housing_gap = (nudge_off > 0) ? nudge_off - (btn_d + 6) : 40;  // clear wall length available for the striker
if (sol_mount == "cover" && housing_gap < sol_body[1] + 2)
    echo(str("WARNING: only ", housing_gap, " mm between button housings; solenoid body is ", sol_body[1], " mm."));
if (sol_mount == "cover" && sol_offset < (btn_d + 6)/2 + sol_body[1]/2 + 1)
    echo("WARNING: sol_offset too small — solenoid body overlaps the flipper button housing.");

module solenoid_strikers() {   // on the case, both sides, from cover level up
    sh = sol_body[2] + sol_pad_h + 10;
    if (sol_mount == "cover") for (m = [0, 1]) mirror([m, 0, 0]) translate([m ? -W : 0, 0, 0])
        translate([wall - eps, sol_y + min(12, housing_gap/2 - 1), ledge_z - eps])
            rotate([90, 0, 0]) linear_extrude(2*min(12, housing_gap/2 - 1))
                polygon([[0, 0], [striker_t, 0], [striker_t, sh - striker_t], [0, sh]]);  // 45-deg top chamfer: no support top-face-down
}

module xyj_card_guides() {     // vertical slots hanging from the top panel (unused when xyj_n = 0)
    ph = xyj_board[1] + 2;    // post height: board height + 2
    if (xyj_n > 0) for (i = [0 : xyj_n - 1]) {
        bx = xyj_pos[i][0]; by = xyj_pos[i][1];
        // left post at bx; right post placed so the two groove floors are exactly board length + clearance apart
        for (side = [0, 1]) translate([bx + side*(xyj_board[0] + xyj_clr + xyj_post - 2*xyj_groove), by - xyj_post/2, H - top_t - ph + eps])
            difference() {
                cube([xyj_post, xyj_post, ph]);
                translate([side ? -1 : xyj_post - xyj_groove, xyj_post/2 - (xyj_board[2] + xyj_clr)/2, -1])
                    cube([xyj_groove + 1, xyj_board[2] + xyj_clr, ph + 2]);     // open at the bottom
            }
    }
}

exc_pad_d = 33.5;   // adhesive pad (the aluminium drive face) - MEASURED 2026-09-30
exc_h     = 30;     // pad face -> back plate - MEASURED; body Ø50 (exc_d) hangs below the pad
exc_gap   = 2;      // body bottom -> catch bridge
exc_px    = exc_d/2 + 2.5 + 4.5;   // pillar centres (+-x): 2.5 mm off the body
exc_bridge = [2*exc_px + 9, 26, 4];   // catch bridge: x, y (wide, so a dropped exciter can't tip off), thickness
exc_wire_hole = [-10, -4, 9];       // leads pass through here to the D3 drop (case coords 100, 30)
module exc_bridge() {   // prints flat. 2 x M3x8 up into the pillar inserts
    difference() {
        translate([-exc_bridge[0]/2, -exc_bridge[1]/2, 0]) linear_extrude(exc_bridge[2])
            offset(r = 3) offset(delta = -3) square([exc_bridge[0], exc_bridge[1]]);
        for (sx = [-1, 1]) translate([sx*exc_px, 0, -1]) cylinder(d = 3.4, h = 10, $fn = 24);
        translate([exc_wire_hole[0], exc_wire_hole[1], -1]) cylinder(d = exc_wire_hole[2], h = 10);
    }
}
module exciter_ring() {
    // Mounted PAD-UP: the pad sticks to the panel, the Ø50 magnet body hangs free below (fixed 2026-09-30 - the
    // first design assumed the body against the panel). A 1.5 mm ring centres the pad. Fall-safe: two pillars
    // either side with a 2.2 mm hole each, pointing at each other, 3.5 mm below the back plate - slide a length of
    // 1.75 mm filament through both as a catch bar (the old tangential zip-tie slots could not form a sling).
    if (exc_d > 0) translate([exc_pos[0], exc_pos[1], H - top_t + eps]) {
        translate([0, 0, -1.5]) difference() {
            cylinder(d = exc_pad_d + 5, h = 1.5);
            translate([0, 0, -1]) cylinder(d = exc_pad_d + 1, h = 4);
        }
        // Catch bridge (2026-10-01 - screwed, no filament bar): two 9 x 9 pillars end exc_gap below the body; a printed
        // bridge (part "exc_bridge") screws across their ends with M3x8 into M3 inserts. It never touches the body in
        // normal use (a touching bridge would deaden the sound) - it only catches the exciter if the tape ever lets go.
        for (sx = [-1, 1]) translate([sx*exc_px, 0, -(exc_h + exc_gap)]) difference() {
            translate([-4.5, -4.5, 0]) cube([9, 9, exc_h + exc_gap]);
            translate([0, 0, -0.01]) cylinder(d = m3_ins_d, h = m3_ins_l, $fn = 24);
        }
    }
}
module misc_pcb_posts() {
    for (b = misc_pcbs) for (sx = [-1, 1], sy = [-1, 1])
        translate([b[0] + sx*b[2]/2, b[1] + sy*b[3]/2, H - top_t - misc_post_h + eps]) cylinder(d = b[5], h = misc_post_h);
}
module misc_pcb_holes() {
    for (b = misc_pcbs) for (sx = [-1, 1], sy = [-1, 1])
        translate([b[0] + sx*b[2]/2, b[1] + sy*b[3]/2, H - top_t - misc_post_h - 1]) cylinder(d = b[4], h = misc_post_h);
}

module cable_anchor() {        // zip-tie loop on the inside wall between the two ports
    if (usb_panel || mq_gx_x > 0) {
        if (port_wall == "back")    // with the DMD GX16 at 197 the block sits 3 mm higher: the ring nut (r 9.5) needs turning room
            translate([(dc_x + usb_panel_x)/2 + 4, D - wall - 8 + eps, H - dc_drop + (mq_gx_x > 0 ? 17 : 14)]) {   // +4: clears the start button body (audit 2026-09-30)
                difference() {
                    translate([-3.5, 0, -4]) cube([7, 8, 8]);       // 7 wide -> 2 mm cheeks beside the tie slot
                    translate([-1.5, -1, -1.1]) cube([3, 10, 2.2]);
                }
                // 45-deg gusset above the block (below it in print orientation) - was a bare 8 mm cantilever
                translate([-3.5, 8 - eps, 4 - eps]) rotate([90, 0, 90]) linear_extrude(7) polygon([[0, 0], [-8, 0], [0, 8]]);
            }
        else
            translate([wall - eps, (dc_y + usb_panel_y)/2, port_z + 14]) difference() {
                translate([0, -3.5, -4]) cube([8, 7, 8]);           // 2 mm cheeks (dormant left-wall variant)
                translate([-1, -1.5, -1.1]) cube([10, 3, 2.2]);
            }
    }
}

module solenoid_mounts() {     // rib style (legacy)
    if (use_solenoids && sol_mount == "rib") for (m = [0, 1]) mirror([m, 0, 0]) translate([m ? -W : 0, 0, 0]) {
        // rib hangs from the top panel
        translate([wall + sol_rib_gap, sol_rib_y, H - top_t - sol_rib_h + eps]) solenoid_rib();
        // striker block on the inside of the side wall, in line with the plunger
        translate([wall - eps, sol_rib_y - 20, H - top_t - sol_rib_h])
            cube([striker_t, 40 + sol_rib_t, sol_rib_h]);
    }
}

// =====================================================================
//  Holes
// =====================================================================
module top_cutouts() {
    // six arcade buttons + coin/start
    for (p = six_btns_b)   translate([fb(p)[0], fb(p)[1], H - top_t - 1]) cylinder(d = btn_d,   h = top_t + 2);
    for (p = start_btns_b) translate([fb(p)[0], fb(p)[1], H - top_t - 1]) cylinder(d = start_d, h = top_t + 2);
    // joystick shaft
    translate([joy_c[0], joy_c[1], H - top_t - 1]) cylinder(d = joy_shaft, h = top_t + 2);
    csk_h = (joy_csk - joy_screw) / 2;
    if (joy_mount == "countersunk")
        for (sx = [-1, 1], sy = [-1, 1])
            translate([joy_c[0] + sx*joy_pitch[0]/2, joy_c[1] + sy*joy_pitch[1]/2, 0]) {
                translate([0, 0, H - top_t - 1]) cylinder(d = joy_screw, h = top_t + 2);
                translate([0, 0, H - csk_h]) cylinder(d1 = joy_screw, d2 = joy_csk + 0.2, h = csk_h + eps);
            }
}

module side_button_holes() {
    for (m = [0, 1]) mirror([m, 0, 0]) translate([m ? -W : 0, 0, 0]) {
        translate([-1, D - flipper_yb, H - btn_drop]) rotate([0, 90, 0]) cylinder(d = btn_d, h = wall + 2);
        if (nudge_off > 0)
            translate([-1, D - flipper_yb - nudge_off, H - btn_drop]) rotate([0, 90, 0]) cylinder(d = nudge_d, h = wall + 2);
    }
}

module back_wall_cutouts() {
    // encoder USB cutout + flange pocket (legacy, off by default)
    if (enc_usb_cutout) {
        translate([usb_x - usb_w/2, D - wall - 1, H - usb_top_drop - usb_h]) cube([usb_w, wall + 2, usb_h]);
        translate([usb_x - usb_flange_w/2, D - wall - eps, H - top_t - usb_flange_h])
            cube([usb_flange_w, usb_flange_deep, usb_flange_h]);
    }
    if (port_wall == "back") {
        if (mq_gx_x == 0) translate([dc_x, D - wall - 1, H - dc_drop]) rotate([-90, 0, 0]) cylinder(d = dc_jack_d, h = wall + 2);
        if (gx_d > 0) for (gxx = [gx_x, mq_gx_x]) if (gxx > 0)
            translate([gxx, D - wall - 1, H - dc_drop]) rotate([-90, 0, 0]) cylinder(d = gx_d, h = wall + 2);
        if (gx_d > 0 && mq_gx_x > 0 && gx_label)      // 0.6 deep, under each socket (outside face)
            for (l = [[gx_x, "IN"], [mq_gx_x, "DMD"]]) translate([l[0], D - 0.6, H - dc_drop - 16]) rotate([90, 0, 180])
                linear_extrude(1) text(l[1], size = 4.5, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
        if (usb_panel) {
            translate([usb_panel_x - usb_panel_cut[0]/2, D - wall - 1, H - usb_panel_drop - usb_panel_cut[1]/2])
                cube([usb_panel_cut[0], wall + 2, usb_panel_cut[1]]);
            if (usb_panel_screw_pitch > 0) for (sx = [-1, 1])
                translate([usb_panel_x + sx*usb_panel_screw_pitch/2, D - wall - 1, H - usb_panel_drop])
                    rotate([-90, 0, 0]) cylinder(d = usb_panel_screw_d, h = wall + 2);
            // flange pocket from inside, leaving usb_panel_skin of wall
            pw = usb_panel_flange[0] + 0.7; ph = usb_panel_flange[1] + 0.7;
            translate([usb_panel_x - pw/2, D - wall - 1, H - usb_panel_drop - ph/2])
                cube([pw, wall - usb_panel_skin + 1, ph]);
            // 45° chamfer under the pocket: printed top-face-down, its lower edge is otherwise a 3 mm cantilever
            pk = wall - usb_panel_skin;
            translate([usb_panel_x - pw/2, 0, H - usb_panel_drop - ph/2]) rotate([90, 0, 90]) linear_extrude(pw)
                polygon([[D - wall - 1, eps], [D - wall + pk, eps], [D - wall, -pk], [D - wall - 1, -pk - 1]]);
        }
    } else {   // left side wall, low
        translate([-1, dc_y, port_z]) rotate([0, 90, 0]) cylinder(d = dc_jack_d, h = wall + 2);
        if (usb_panel) {
            translate([-1, usb_panel_y - usb_panel_cut[0]/2, port_z - usb_panel_cut[1]/2])
                cube([wall + 2, usb_panel_cut[0], usb_panel_cut[1]]);
            if (usb_panel_screw_pitch > 0) for (sy = [-1, 1])
                translate([-1, usb_panel_y + sy*usb_panel_screw_pitch/2, port_z])
                    rotate([0, 90, 0]) cylinder(d = usb_panel_screw_d, h = wall + 2);
        }
    }
}

// =====================================================================
//  Parts
// =====================================================================
module td_posts() {
    if (td_on) for (sx = [-1, 1], sy = [-1, 1])
        translate([td_cc[0] + sx*td_post_xy[0], td_cc[1] + sy*td_post_xy[1], H - top_t - td_post_h])
            cylinder(d = td_post_od, h = td_post_h + eps);
}
module td_cutouts() {
    if (td_on) {
        z0 = H - top_t;                                   // panel underside
        skin = top_t - td_pocket_d;
        pw = td_board + [2, 2] * td_pocket_clr;
        translate([td_bc[0] - pw[0]/2, td_bc[1] - pw[1]/2, z0 - 1]) cube([pw[0], pw[1], td_pocket_d + 1]);
        ww = td_active + [2, 2] * td_win_m;
        translate([td_win_c[0], td_win_c[1], 0]) hull() {                                  // window, 45° out to the top
            translate([-ww[0]/2, -ww[1]/2, z0 + td_pocket_d - eps]) cube([ww[0], ww[1], eps]);
            translate([-ww[0]/2 - skin, -ww[1]/2 - skin, H]) cube([ww[0] + 2*skin, ww[1] + 2*skin, 1]);
        }
        for (sx = [-1, 1], sy = [-1, 1])                                                    // M3 machine-screw holes
            translate([td_cc[0] + sx*td_post_xy[0], td_cc[1] + sy*td_post_xy[1], H - top_t - td_post_h - 1])
                cylinder(d = m3_ins_d, h = min(m3_ins_l, td_post_h - 0.6));   // M3 insert
    }
}
module td_clamp() {   // print flat, groove up. td_clamp_raise thickens it toward the board. 4 x M3x8 pan head from below into M3 inserts; 1.5 mm foam tape on the two lands
    difference() {
        union() {
            translate([-td_clamp[0]/2, -td_clamp[1]/2, 0]) cube(td_clamp);
            // lands under the header strips (|y| 9.5-14) stand proud of the post-contact face by td_clamp_raise:
            // the posts set where the plate stops, so only the lands can take up slack
            if (td_clamp_raise > 0) for (m = [0, 1]) mirror([0, m, 0])
                translate([-td_clamp[0]/2, td_relief[0]/2, td_clamp[2] - eps]) cube([td_clamp[0], 14 - td_relief[0]/2, td_clamp_raise + eps]);
        }
        translate([-td_clamp[0]/2 - 1, -td_relief[0]/2, td_clamp[2] - td_relief[1]]) cube([td_clamp[0] + 2, td_relief[0], 5]);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx*td_post_xy[0], sy*td_post_xy[1], -1]) cylinder(d = 3.4, h = 10);
    }
}

module case() {
    difference() {
        union() {
            difference() { shell_outer(); cavity(); rebate(); }
            corner_posts();
            mid_tabs_body();
            joystick_bosses();
            pcb_standoffs(pcb_posts, pcb_post_od, pcb_post_hole, pcb_post_h);
            pcb_standoffs(drv_posts, pcb_post_od, pcb_post_hole, pcb_post_h);
            solenoid_mounts();
            solenoid_strikers();
            mq_rails();
            xyj_card_guides();
            exciter_ring();
            misc_pcb_posts();
            cable_anchor();
            td_posts();
            for (t = tie_case) translate([t[0], t[1], H - top_t + eps]) rotate([180, 0, t[2]]) tie_mount_block();   // hang from the panel (x-flip first, then z: cable stays along t[2])
        }
        td_cutouts();
        top_cutouts();
        side_button_holes();
        back_wall_cutouts();
        corner_post_holes();
        mid_tab_holes();
        joystick_boss_holes();
        misc_pcb_holes();
        pcb_standoff_holes(pcb_posts, pcb_post_hole, pcb_post_h);
        pcb_standoff_holes(drv_posts, pcb_post_hole, pcb_post_h);
    }
}

cov_off = wall - ledge + clr;                 // cover origin offset from case origin
cw = W - 2*cov_off;  cd = D - 2*cov_off;

// Solenoid cradle on the cover (cover coords). Origin = case origin shifted by cov_off.
sol_pad_len = sol_body[0] + 24;        // body + 12 margin each end
sol_pad_w   = sol_body[1] + 2*2;
sol_x0      = wall + striker_t + sol_gap + sol_rod_out - 12;   // pad start (case coords), left side — keeps 6 mm to the striker
module sol_cradle_body(m) {      // m = 0 left, 1 right
    x0 = m ? W - sol_x0 - sol_pad_len : sol_x0;
    translate([x0 - cov_off, sol_y - sol_pad_w/2 - cov_off, cover_t - eps]) {
        cube([sol_pad_len, sol_pad_w, sol_pad_h]);                                  // pad
        for (side = [0, 1]) translate([0, side*(sol_pad_w - 2), 0]) cube([sol_pad_len, 2, sol_pad_h + sol_rail_h]); // rails
    }
}
module sol_cradle_holes(m) {   // two full-length slots at +/-7 lateral: the diagonal M4 pair lands in them
    x0 = m ? W - sol_x0 - sol_pad_len : sol_x0;                       // whichever way the diagonal runs,
    scx = m ? x0 + sol_pad_len - 12 - sol_hole_face : x0 + 12 + sol_hole_face;   // on both sides (180-deg turn)
    for (sgn = [-1, 1]) translate([scx - cov_off, sol_y + sgn*sol_hole_lat/2 - cov_off, 0]) {
        hull() for (dx = [-sol_slot_len/2, sol_slot_len/2])
            translate([dx, 0, -1]) cylinder(d = sol_slot_w, h = cover_t + sol_pad_h + 2);
        hull() for (dx = [-sol_slot_len/2, sol_slot_len/2])                          // 90-deg countersink from below
            translate([dx, 0, -eps]) cylinder(d1 = sol_slot_w + 5, d2 = sol_slot_w, h = 2.5);
    }
}

function pcb_hole_pts(b) = (len(b) > 9 && b[9] == 2) ? [[-1, -1], [1, 1]] : [[-1, -1], [1, -1], [-1, 1], [1, 1]];
function post_od(b) = len(b) > 11 ? b[11] : pcb_fix == "machine" ? max(b[5], b[4] + 4) : b[5];
module cover_pcb_posts() {
    for (b = cover_pcbs) for (h = pcb_hole_pts(b))
        translate([b[0] + h[0]*b[2]/2 - cov_off, b[1] + h[1]*b[3]/2 - cov_off, cover_t - eps]) cylinder(d = post_od(b), h = post_h(b));
}
// ISO nuts: across-flats and thickness per size; pocket is +0.2 AF (snug press fit) and +0.2 deep.
function nut_af(sz) = sz >= 3 ? 5.5 : sz >= 2.5 ? 5.0 : 4.0;
function nut_t(sz)  = sz >= 3 ? 2.4 : sz >= 2.5 ? 2.0 : 1.6;
function pilot(sz)  = sz >= 3 ? 2.5 : sz >= 2.5 ? 2.0 : 1.6;
function form_hole(sz) = sz >= 3 ? 3.0 : sz >= 2.5 ? 2.35 : 1.85;   // machine screw forms its own thread in PLA
module cover_pcb_holes() {
    for (b = cover_pcbs) if (len(b) > 12)          // connector slot between the two low-y posts (field 12 = clear width)
        translate([b[0] - b[12]/2 - cov_off, b[1] - b[3]/2 - post_od(b)/2 - 1 - cov_off, cover_t])
            cube([b[12], post_od(b) + 2, post_h(b) + 1]);
    for (b = cover_pcbs) for (h = pcb_hole_pts(b))
        translate([b[0] + h[0]*b[2]/2 - cov_off, b[1] + h[1]*b[3]/2 - cov_off, 0]) {
            if (pcb_fix == "machine")                                                                       // blind: 5 mm post + 3 mm
                translate([0, 0, cover_t - 3]) cylinder(d = form_hole(b[4]), h = post_h(b) + 4);     // into the cover, 1 mm floor
            else if (pcb_fix == "nut") {
                translate([0, 0, -1]) cylinder(d = b[4] + 0.4, h = cover_t + cover_post_h + 2);        // clearance, through
                translate([0, 0, -eps]) cylinder(d = (nut_af(b[4]) + 0.2) / cos(30), h = nut_t(b[4]) + 0.2, $fn = 6);  // nut pocket
            } else
                translate([0, 0, cover_t - 1]) cylinder(d = pilot(b[4]), h = cover_post_h + 2);        // self-tap pilot
        }
}

module cover(ears = false) {   // ears: anti-curl discs, print exports only - never in the views
    difference() {
        union() {
            rrect(cw, cd, cover_t, corner_r - wall + ledge - clr);
            if (ears) cover_ear_set();
            if (use_solenoids && sol_mount == "cover") for (m = [0, 1]) sol_cradle_body(m);
            cover_pcb_posts();
            for (t = tie_cover) translate([t[0] - cov_off, t[1] - cov_off, cover_t - eps]) rotate([0, 0, t[2]]) tie_mount_block();
        }
        if (use_solenoids && sol_mount == "cover") for (m = [0, 1]) sol_cradle_holes(m);
        cover_pcb_holes();
        // corner screws, countersunk from below (outside)
        holes = concat(
            [for (x = [post_inset, W - post_inset], y = [post_inset, D - post_inset]) [x, y]],
            mid_tabs ? [[W/2, wall + tab_d/2], [W/2, D - wall - tab_d/2]] : []);
        for (p = holes) translate([p[0] - cov_off, p[1] - cov_off, 0]) {
            translate([0, 0, -1]) cylinder(d = cover_hole_d, h = cover_t + 2);
            csk = (cover_csk_d - cover_hole_d) / 2;
            translate([0, 0, -eps]) cylinder(d1 = cover_csk_d, d2 = cover_hole_d, h = csk);
        }
        // rubber-foot recesses: 4 corners + 2 mid front/back (heavy box + nudge forces)
        feet = concat([for (x = [25, cw - 25], y = [25, cd - 25]) [x, y]],
                      [[cw/2, 25], [cw/2, cd - 25]]);
        for (f = feet) translate([f[0], f[1], -1]) cylinder(d = feet_d, h = feet_recess + 1);
    }
}

// Corner anti-warp ears for the case print (2026-09-30, after the corners lifted): four 16 mm discs, 0.8 mm
// thick, on the bed face under the four top corners. They stay inside the 254 mm width (the bed has ~1 mm spare
// there) and reach 6 mm out along the 230 mm depth, where the turned print has ~10 mm of room each side.
corner_ears = true;
module print_corner_ears() {
    for (x = [9, W - 9], y = [edge_c, D - edge_c])
        translate([x, y, H - 0.8]) cylinder(d = 16, h = 0.8);
}
module print_ear_set() {
    for (x = [14, W/2, W - 14], y = [6, D - 6])
        translate([x, y, H - 0.6]) cylinder(d = 16, h = 0.6);
}

if (part == "case") { case(); if (print_ears) print_ear_set(); }   // exporting "case" alone: flip 180 in the slicer
// case ready to slice: top face down, turned 90° so the 254 mm width runs along the A1's bed (Y) axis.
// Printed with the 254 side along X it failed twice at layer ~22 ("extruder is not extruding normally",
// 2026-09-26/27): with the top chamfer each layer widens, and by layer 22 the toolhead came within ~2.5 mm
// of both X travel ends. Along X it now spans only 235 mm.
if (part == "case_print")
    rotate([0, 0, 90]) translate([0, -D/2, 0]) translate([0, D, H]) rotate([180, 0, 0]) {
        case(); if (print_ears) print_ear_set(); if (corner_ears) print_corner_ears(); }
if (part == "print_all") {
    // everything in print orientation, side by side. Export as one STL, then in the slicer:
    // Split -> To Objects, Arrange. Case = plate 1, cover = plate 2, test coupon = plate 3.
    translate([0, D, H]) rotate([180, 0, 0]) { case(); if (print_ears) print_ear_set(); }   // top face down, mouse ears on the bed
    translate([W + 15, 0, 0]) cover();                          // feet down, cradles up; 4 mm brim in the slicer
    translate([W + 15 + cw + 15, 10, 0]) test_fit();
    if (joy_mount == "clamp") translate([W + 15 + cw + 15, sol_pad_w + 80, 0]) joy_clamp();
}
// Cover anti-curl ears: full 16 mm discs, 0.8 mm (4 layers) so the rim is stiff enough not to curl
// on its own - the thin 0.6 mm version lifted at a corner and the nozzle scarred the part (2026-09-12).
// Unioned INSIDE cover() before the holes are cut, so a screw hole or foot recess is cut through an
// ear rather than bridged. In X the cover leaves ~4 mm of bed each side, so the discs sit 5 mm in from
// the side edges and reach ~3 mm past them; in Y they reach much further out, where there is room.
// A 4 mm outer brim in the slicer is the better fix and fits - these are the belt-and-braces option.
module cover_ear_set() {
    for (p = [[5, -3], [cw - 5, -3], [5, cd + 3], [cw - 5, cd + 3], [cw/2, -4], [cw/2, cd + 4]])
        translate([p[0], p[1], 0]) cylinder(d = 16, h = 0.8);
}

if (part == "cover") cover();   // no ears on the cover: print with a 4 mm brim (2026-09-26)
if (part == "joy_clamp") joy_clamp();
if (part == "td_clamp") td_clamp();
if (part == "exc_bridge") exc_bridge();
// Fit test for the status display: the top-panel corner with window, pocket and posts, printed top-face-down
// like the case (~25 min). Check: the clear plate drops into the pocket, pixels centred in the window,
// clamp screws bite and the clamp holds the board without rocking.
td_test_box = [[td_bc[0] - 33, td_bc[1] - 24, H - top_t - td_post_h - 1], [66, 48, top_t + td_post_h + 2]];
if (part == "td_test")
    translate([0, 0, H]) rotate([180, 0, 0]) translate([-td_bc[0], -td_bc[1], 0])
        intersection() { case(); translate(td_test_box[0]) cube(td_test_box[1]); }
if (part == "test_fit") test_fit();
// Screw-hole test: real cover posts (4 mm plate + 5 mm post) at three M3 hole sizes plus the M2.5 and
// M2 holes, each labelled with its diameter. Drive a machine screw into each; keep the size that bites
// firmly without splitting and set form_hole() to it before printing the cover. ~5 min.
// ---------------- 7-port hub carrier (Eujgoov FE2.1 board, ordered 2026-09-27) ----------------
// MOVED 2026-09-28: left-middle of the cover, over the old 4-port hub's two posts, which now serve as
// locating pins through two holes in the plate. Board long axis front-back; USB-A ports face +X into the open
// centre; the 5 V jack (wires soldered to its pins - no plug) and the micro-USB input face the left wall
// (~18 mm, right-angle micro plug). The two rearmost ports are spare: their plugs would reach the amp.
// Board and hole pattern MEASURED 2026-09-28 (84 x 44, holes 78.4 x 38.5). Hole size assumed M3.
hub7_board    = [44, 84];        // board as mounted: X across, Y front-back
hub7_c        = [45.2, 95.2];    // board centre, case coords
hub7_hole     = [2.75, 2.8];     // hole centre inset from the edges (x, y)
hub7_screw    = 3;               // M3 assumed (form_hole -> 3.0)
hub7_post     = [7, 5];          // post OD, height (clears the through-hole solder joints under the board)
hub7_plate_t  = 2.5;
hub7_old_posts = [[40, 90], [84, 114]];   // the printed cover's old hub posts (case coords, OD 7, 5 tall)
function hub7_rel(p) = [p[0] - hub7_c[0], p[1] - hub7_c[1]];
module hub_carrier() {           // origin: board centre on the bed; print flat, posts up; M3x8 screws
    hx = hub7_board[0]/2 - hub7_hole[0];  hy = hub7_board[1]/2 - hub7_hole[1];
    x0 = -hub7_board[0]/2 - 2;  x1 = hub7_rel(hub7_old_posts[1])[0] + 6;  y0 = -hub7_board[1]/2 - 2;
    difference() {
        union() {
            translate([x0, y0, 0]) cube([x1 - x0, hub7_board[1] + 4, hub7_plate_t]);
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx*hx, sy*hy, hub7_plate_t - eps])
                cylinder(d = hub7_post[0], h = hub7_post[1]);
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx*hx, sy*hy, 0.8])        // blind: 0.8 mm floor
            cylinder(d = form_hole(hub7_screw), h = hub7_plate_t + hub7_post[1]);
        for (p = hub7_old_posts) translate([hub7_rel(p)[0], hub7_rel(p)[1], -1])  // drop over the old posts
            cylinder(d = 7.8, h = hub7_plate_t + 2);
        // "PORTS" arrow engraved 0.6 mm, pointing +X (the side the USB-A sockets face)
        translate([22, -28, hub7_plate_t - 0.6]) linear_extrude(1) {
            polygon([[16, 0], [8, 6], [8, 2.5], [-10, 2.5], [-10, -2.5], [8, -2.5], [8, -6]]);
            translate([2, 11]) text("PORTS", size = 5, halign = "center", valign = "center");
        }
    }
}
if (part == "hub_carrier") hub_carrier();

if (part == "screw_test") {
    tests = [[3, 2.8], [3, 2.9], [3, 3.0], [2.5, 2.35], [2, 1.85]];
    difference() {
        union() {
            cube([len(tests)*14 + 2, 22, cover_t]);
            for (i = [0 : len(tests) - 1]) translate([8 + i*14, 8, cover_t - eps]) cylinder(d = tests[i][0] + 4, h = cover_post_h);
        }
        for (i = [0 : len(tests) - 1]) {
            translate([8 + i*14, 8, cover_t - 3]) cylinder(d = tests[i][1], h = cover_post_h + 4);
            translate([8 + i*14, 18, cover_t - 0.6]) linear_extrude(1)
                text(str(tests[i][1]), size = 3.2, halign = "center", valign = "center");
        }
    }
}
module test_fit() {
    // 1) solenoid cradle coupon: pad + rails + slots on a 4 mm base
    difference() {
        union() {
            translate([-5, -5, 0]) cube([sol_pad_len + 10, sol_pad_w + 10, cover_t]);
            translate([0, 0, cover_t - eps]) {
                cube([sol_pad_len, sol_pad_w, sol_pad_h]);
                for (side = [0, 1]) translate([0, side*(sol_pad_w - 2), 0]) cube([sol_pad_len, 2, sol_pad_h + sol_rail_h]);
            }
        }
        for (sgn = [-1, 1]) hull() for (dx = [-sol_slot_len/2, sol_slot_len/2])
            translate([12 + sol_hole_face + dx, sol_pad_w/2 + sgn*sol_hole_lat/2, -1]) cylinder(d = sol_slot_w, h = 20);
    }
    // 2) XY-J02 slot coupon (only when the panel slots are in use)
    if (xyj_n > 0) translate([sol_pad_len + 20, 0, 0]) {
        span = xyj_board[0] + xyj_clr;
        cube([span + 2*xyj_post, 14, 2]);
        for (side = [0, 1]) translate([side*(span + xyj_post - 2*xyj_groove), 4, 2 - eps])
            difference() {
                cube([xyj_post, xyj_post, 25]);
                translate([side ? -1 : xyj_post - xyj_groove, xyj_post/2 - (xyj_board[2] + xyj_clr)/2, 3])
                    cube([xyj_groove + 1, xyj_board[2] + xyj_clr, 30]);
            }
    }
    // 3) side-button, DC jack and GX16 tether holes in a 5 mm wall coupon
    translate([0, sol_pad_w + 25, 0]) difference() {
        cube([btn_d + 12 + dc_jack_d + 12 + (gx_d > 0 ? gx_d + 12 : 0), wall, 40]);
        translate([btn_d/2 + 6, -1, 20]) rotate([-90, 0, 0]) cylinder(d = btn_d, h = wall + 2);
        translate([btn_d + 12 + dc_jack_d/2 + 6, -1, 20]) rotate([-90, 0, 0]) cylinder(d = dc_jack_d, h = wall + 2);
        if (gx_d > 0) translate([btn_d + 12 + dc_jack_d + 12 + gx_d/2 + 6, -1, 20])
            rotate([-90, 0, 0]) cylinder(d = gx_d, h = wall + 2);
    }
}
// =====================================================================
//  Marquee rails (on the case) and the slide-on module
// =====================================================================
module mq_rail_profile(g = 0)   // dovetail cross-section: x across the wall, y = out of the wall
    polygon([[-mq_root/2 - g, 0], [mq_root/2 + g, 0],
             [mq_crest/2 + g, mq_deep + g], [-mq_crest/2 - g, mq_deep + g]]);

module mq_rail() {   // male rail on the wall face, runs mq_z0..mq_z1, top end tapers to nothing at 45°
    // FIXED 2026-10-03: the old single hull() also spread the ROOT from 10 to 14 mm up the rail, so the top half
    // was a plain rectangle and the plate's dovetail grooves could not go on (the first printed case has those rails).
    translate([0, 0, mq_z0]) linear_extrude(mq_z1 - mq_deep - mq_z0 + 0.01) mq_rail_profile();
    hull() {        // only the top end tapers (slide lead-in, support-free print)
        translate([0, 0, mq_z1 - mq_deep]) linear_extrude(0.01) mq_rail_profile();
        translate([0, 0, mq_z1 - 0.01]) linear_extrude(0.01) scale([1, 0.02]) mq_rail_profile();
    }
}

module mq_rails() {   // back wall only — screen, rails and ports all live on the wall away from the player
    if (marquee_rails) for (x = mq_rail_x)
        translate([x, D - eps, 0]) mq_rail();
}

module mq_at_wall() {   // place children on the selected wall (geometry is authored for the back wall)
    if (mq_wall == "back") children();
    else translate([0, D, 0]) mirror([0, 1, 0]) children();
}

mq_plate_z0 = mq_z0 - 4;
mq_plate_z1 = H + 13;      // neck continues past the box top to the head

// ---- Marquee v2 (2026-09-28): frame halves + rear-cover halves + mounting plate, all support-free, all on the A1 bed.
// Head-local coords: origin = bottom-front-centre of the frame, x across (panel 1 = -x = LEFT from the player),
// y = depth from the LED face (+y = backward), z = up. Panels: 160 x 80 x 15 each (33 deep with plugs, MEASURED).
mq_bez    = 6;      // frame wall around the panels (thin surround, 2026-09-28)
mq_proud  = 1;      // frame front stands this far proud of the LED face (45° inner chamfer)
mq_fl_t   = 6;      // rear flange the panels screw to (M3x10 into the panels' brass inserts)
mq_fl_w   = [13, 22];   // flange band width: along the long edges, at the short ends (clears the J1/J2 plugs at 25+ mm)
mq_cav    = 33;     // cover cavity behind the flange: plug tips at y 33, buck (18 thick) sits 3 mm clear above them
mq_cov_t  = 2.4;    // cover wall / back thickness
mq_pz     = mq_bez;                              // panel bottom edge (local z)
mq_fh     = mq_panel[1] + 2*mq_bez;              // frame height 92
mq_hw     = mq_panel[0]/2 + mq_bez;              // half width 166
mq_fl_y   = mq_panel[2];                         // flange front face = panel back (y 15)
mq_cov_y0 = mq_fl_y + mq_fl_t;                   // cover rim (y 21)
mq_cov_y1 = mq_cov_y0 + mq_cav + mq_cov_t;       // cover outer back (y 56.4)
mq_r      = 8;                                   // outer corner radius
function mq_pc(m) = [m ? mq_panel[0]/4 : -mq_panel[0]/4, mq_pz + mq_panel[1]/2];   // panel centre (x, z) per half
mq_post_xz = [[-152, 12], [-152, 80], [-9, 12], [-9, 80]];      // cover posts on the flange (left half; mirrored)
mq_saddle_x = [-95, -35, 35, 95];                                // plate -> frame screws, up into the bottom wall

module mq_outline2d(m) {        // frame/cover outline in (x, z): rounded outer corners, square at the seam
    sx = m ? 1 : -1;
    hull() for (z = [mq_r, mq_fh - mq_r]) {
        translate([sx*(mq_hw - mq_r), z]) circle(mq_r);
        translate([sx*0.01, z - mq_r]) square([0.01, 2*mq_r]);
    }
}
module mq_xz(y0, y1) {          // extrude a 2D (x, z) shape along +y from y0 to y1
    translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
}
module mq_frame_half(m) {       // prints flange-down (part = marquee_frame_left/right); M3x10 x4 per panel
    pc = mq_pc(m);
    difference() {
        union() {
            hull() {                                                   // walls, with a 2 mm 45° chamfer at the face -
                mq_xz(-mq_proud + 2, mq_cov_y0) mq_outline2d(m);        // on the OUTER edges only: the seam edge stays
                mq_xz(-mq_proud, -mq_proud + 0.01) hull() {              // square so the halves butt with no V-groove
                    offset(delta = -2) mq_outline2d(m);                   // (2026-09-30)
                    translate([m ? 0 : -0.01, 2]) square([0.01, mq_fh - 4]);
                }
            }
        }
        // panel pocket (0.3 clearance), open at the front, down to the flange
        translate([pc[0] - mq_panel[0]/4 - 0.3 - (m ? 0 : 1), -mq_proud - 1, mq_pz - 0.3])
            cube([mq_panel[0]/2 + 0.6 + 1, mq_fl_y + mq_proud + 1, mq_panel[1] + 0.6]);
        // 45° chamfer on the inner front edge
        hull() {
            translate([pc[0], -mq_proud - 0.01, pc[1]]) rotate([-90, 0, 0])
                linear_extrude(0.01) square([mq_panel[0]/2 + 0.6 + 2*mq_proud + 2, mq_panel[1] + 0.6 + 2*mq_proud], center = true);
            translate([pc[0], 0, pc[1]]) rotate([-90, 0, 0])
                linear_extrude(0.01) square([mq_panel[0]/2 + 0.6, mq_panel[1] + 0.6], center = true);
        }
        // flange window: open behind the panel except the perimeter bands
        translate([pc[0] - mq_panel[0]/4 + mq_fl_w[1], mq_fl_y - 1, mq_pz + mq_fl_w[0]])
            cube([mq_panel[0]/2 - 2*mq_fl_w[1], mq_fl_t + 2, mq_panel[1] - 2*mq_fl_w[0]]);
        // panel screws: M3 clearance + counterbore from the back, on the maker's insert pattern
        for (h = mq_panel_m3) translate([pc[0] + h[0], mq_fl_y - 1, pc[1] + h[1]]) rotate([-90, 0, 0]) {
            cylinder(d = 3.4, h = mq_fl_t + 2);
            translate([0, 0, mq_fl_t - 1.5 + 1]) cylinder(d = 6.5, h = 3);
        }
        // clearance for the panel's two moulded locating pins (found on the fit test 2026-09-29)
        for (h = mq_panel_pins) translate([pc[0] + h[0], mq_fl_y - 1, pc[1] + h[1]]) rotate([-90, 0, 0])
            cylinder(d = 4.5, h = mq_fl_t + 2);
        // cover screws land here: 3.0 self-forming holes (M3x40 from the cover back)
        for (p = mq_post_xz) translate([m ? -p[0] : p[0], mq_cov_y0 + 0.01, p[1]]) rotate([90, 0, 0])
            cylinder(d = form_hole(3), h = mq_fl_t - 0.8);
        // plate screws: 3.0 holes up into the bottom wall
        for (x = mq_saddle_x) if ((x > 0) == (m == 1))
            translate([x, (mq_cov_y0 - mq_proud)/2, -0.01]) cylinder(d = form_hole(3), h = mq_bez - 1);
        // seam alignment pins: 3 mm filament through the top and bottom walls (glue the seam too)
        for (z = [mq_bez/2, mq_fh - mq_bez/2]) translate([0, (mq_cov_y0 - mq_proud)/2, z])
            rotate([0, 90, 0]) cylinder(d = 3.2, h = 24, center = true);
    }
}
module mq_cover_half(m) {       // prints back-down (part = marquee_cover_left/right)
    sx = m ? 1 : -1;
    difference() {
        union() {
            difference() {
                mq_xz(mq_cov_y0, mq_cov_y1) mq_outline2d(m);
                mq_xz(mq_cov_y0 - 1, mq_cov_y1 - mq_cov_t) offset(delta = -mq_cov_t) mq_outline2d(m);
                translate([m ? -1 : -0.02, mq_cov_y0 - 1, mq_cov_t])            // open at the seam (ribbon crosses)
                    cube([1.02, mq_cav + 1, mq_fh - 2*mq_cov_t]);
            }
            for (p = mq_post_xz)
                translate([m ? -p[0] : p[0], mq_cov_y0, p[1]]) rotate([-90, 0, 0]) cylinder(d = 10, h = mq_cav + 0.1);   // 10 OD: solid wall round the 6.5 head recess
            if (m) {                                                           // buck cradle (right half): 3 mm rim
                bx = 95; bz = mq_fh/2;
                translate([bx, mq_cov_y1 - mq_cov_t - 1.5 + 0.01, bz]) rotate([-90, 0, 0]) difference() {   // sits ON the back (v1 floated 1.5 mm)
                    translate([0, 0, 0]) cube([46 + 2*1.6 + 0.6, 32.5 + 2*1.6 + 0.6, 3.01], center = true);
                    cube([46.6, 33.1, 4], center = true);
                    cube([60, 20, 4], center = true);                          // gaps for the side tabs
                }
            }
        }
        for (p = mq_post_xz) translate([m ? -p[0] : p[0], mq_cov_y0 - 1, p[1]]) rotate([-90, 0, 0]) {
            cylinder(d = 3.4, h = mq_cav + mq_cov_t + 2);
            translate([0, 0, mq_cav + mq_cov_t + 1 - 2]) cylinder(d = 6.5, h = 10);   // 2 mm head recess in the back (v1 was 4.4 deep in a 7 mm post: 0.25 mm wall -> floating ring)
        }
        if (m) for (i = [-3 : 3])                                             // vents over the buck
            translate([95 + i*6, mq_cov_y1 - mq_cov_t - 1, mq_fh/2]) rotate([-90, 0, 0])
                hull() for (dz = [-14, 14]) translate([0, dz, 0]) cylinder(d = 3, h = mq_cov_t + 2);
        // cable exit, bottom at the seam: 12 V lead + USB-C cable (half-slot in each half)
        translate([m ? 0 : -14, mq_cov_y0 + 8, -1]) cube([14, 16, mq_cov_t + 2]);
    }
}
// ---- Marquee v3 TRAYS (2026-10-01): frame + cover in ONE piece per half -> 3 parts (2 trays + plate).
// The panel drops in from the FRONT and is screwed from OUTSIDE the back: M3x10 down a tube into its brass insert
// (the counterbore runs to 4 mm from the panel, so an M3x10 gets 6 mm of thread; driver goes down the 6.5 mm bore). Electronics go in through the front opening first.
// The seam side is OPEN (ribbon + power harness cross inside). Each panel uses its 2 SEAM-END corner inserts + the 2
// middle inserts, leaving the outer ~45 mm free: the ESP32 stands on the LEFT tray's outer end wall (VHB on a pad,
// connectors inward, USB-C down through a floor hole) and the 10 A buck on the RIGHT tray's (vents in the back).
mq_back_t   = 2.4;
mq_tray_y1  = mq_cov_y1;                     // outer back (y 56.4)
mq_screw_floor = 4;                          // plastic left under the screw head, next to the panel (2026-10-01: no long M3s)
mq_tube     = [10, mq_cov_y1 - mq_fl_y - mq_screw_floor];   // screw tube OD, counterbore depth (6.5 dia) from the outside
                                             //   -> M3x10: 4 mm through the floor + 6 mm into the panel's insert
esp_env     = [35, 31, 56];                  // ESP32 envelope: inward x across the board, y (board width + 2), z (52 + USB)
esp_pad     = 7;                             // (now the standoff height)
esp_holes   = [[2.2, 2.9], [26.8, 2.9], [2.2, 51.74 - 2.2], [26.8, 51.74 - 2.2]];   // [across, from the USB end], scaled from
                                             //   ELEGOO's drawing (Ø3 holes)
esp_screw   = 2;                             // M2x10. M3 does NOT fit (checked 2026-10-01): a Ø5.5 post hits the EN button 2.5 mm
                                             //   from the hole, and an M3 head hits the D23 jumper housing on the pin side
esp_post_d  = esp_screw >= 3 ? 5.5 : 4.5;
                                             // posts keep the shield can (3.3) and the right-angle USB-C plug off the wall.
                                             // Board orientation: VIN/GND/EN-button edge toward the BACK - each post's teardrop
                                             //   cap points back, and this keeps it off the EN/BOOT buttons (tip 4.85 vs button 5.0)
mq_gx       = [55, 18];                      // ONE cable in (2026-10-01): GX16-8 socket in the RIGHT tray's back skin, x/z
                                             //   (head coords). Clear of the tubes (x 17.5, 92.5), vents (x 68+), J1 of panel 2
                                             //   (x 37-47, mid-height) and the floor; body reaches y 32 (panel plugs end y 33, higher up).
mq_end_relief = 3.5;                         // cavity behind the panel extends this far into the outer end wall (2.2 mm left)
                                             //   - J1 sits 37-47 mm from the panel's outer end (photo 2026-10-01)
esp_y0      = mq_fl_y + 4;                   // board's front edge (y) ; board 29 along y
esp_z0      = 26;                            // board's USB end (z); board 52 tall, USB-C points DOWN - 20 mm under it for the angled plug
buck_env    = [32, 18, 63];                  // J2D50K2405 63 (incl. ears) x 32 x 18: flat on the right tray's back skin at the
                                             //   end wall (x 32, y 18, z 63), standing on its bottom ear; 4 leads from a long side -> seam
function mq_use_inserts(m) = [for (h = mq_panel_m3) if ((m == 0 && (h[0] > -50 || h[1] < 0)) || (m == 1 && (h[0] < 50 || h[1] > 0))) h];
    // 5 of each panel's 6 inserts (2026-10-01): seam end + mids + ONE outer corner - left panel's outer-BOTTOM
    // (below the ESP32, z 8.5-18.5 vs board z 26+), right panel's outer-TOP (above the buck, z 73.5+ vs buck top 69).
    // The other outer corner is where the ESP32 / buck stand.
module esp_post() {     // 7 mm standoff along +x. Wall half: full teardrop toward +y (= down when the tray prints back-down);
                        // board half (3.6 mm, where the can/buttons are): plain round, so nothing pokes into the components
    linear_extrude(3.4) hull() { circle(d = esp_post_d, $fn = 32); translate([0, esp_post_d/2 * 1.414]) rotate(45) square(0.01, center = true); }
    cylinder(d = esp_post_d, h = esp_pad + 0.01, $fn = 32);
}
module mq_tray_half(m) {
    sx = m ? 1 : -1; pc = mq_pc(m);
    xo = sx * (mq_panel[0]/2 + 0.3 + mq_end_relief);                   // inner face of the (relieved) outer end wall
    difference() {
        union() {
            difference() {
                hull() {                                               // shell with the 2 mm front chamfer on the OUTER edges
                    mq_xz(-mq_proud + 2, mq_tray_y1) mq_outline2d(m);
                    mq_xz(-mq_proud, -mq_proud + 0.01) hull() {
                        offset(delta = -2) mq_outline2d(m);
                        translate([m ? 0 : -0.01, 2]) square([0.01, mq_fh - 4]);
                    }
                }
                // panel pocket + cavity: panel-sized, from the front to the back skin; open at the seam
                translate([m ? -1 : -mq_panel[0]/2 - 0.3, -mq_proud - 1, mq_pz - 0.3])
                    cube([mq_panel[0]/2 + 0.3 + 1, mq_tray_y1 - mq_back_t + mq_proud + 1, mq_panel[1] + 0.6]);
                // end relief: behind the panel the cavity reaches 3.5 mm into the outer end wall; 45° lead-in (prints back-down)
                hull() {
                    translate([m ? mq_panel[0]/2 : -mq_panel[0]/2 - 0.3 - mq_end_relief, mq_fl_y + mq_end_relief, mq_pz - 0.3])
                        cube([0.3 + mq_end_relief + 0.01, mq_tray_y1 - mq_back_t - mq_fl_y - mq_end_relief, mq_panel[1] + 0.6]);
                    translate([m ? mq_panel[0]/2 : -mq_panel[0]/2 - 0.3, mq_fl_y, mq_pz - 0.3]) cube([0.31, 0.01, mq_panel[1] + 0.6]);
                }
                // 45° chamfer on the inner front edge
                hull() {
                    translate([pc[0], -mq_proud - 0.01, pc[1]]) rotate([-90, 0, 0])
                        linear_extrude(0.01) square([mq_panel[0]/2 + 0.6 + 2*mq_proud + 2, mq_panel[1] + 0.6 + 2*mq_proud], center = true);
                    translate([pc[0], 0, pc[1]]) rotate([-90, 0, 0])
                        linear_extrude(0.01) square([mq_panel[0]/2 + 0.6, mq_panel[1] + 0.6], center = true);
                }
            }
            for (h = mq_use_inserts(m))                                // screw tubes: back skin -> panel back (the panel stop)
                translate([pc[0] + h[0], mq_fl_y, pc[1] + h[1]]) rotate([-90, 0, 0]) cylinder(d = mq_tube[0], h = mq_tray_y1 - mq_fl_y - 0.01);
            translate([m ? 0 : -mq_seam_rib[0], mq_seam_rib[2], mq_pz - 0.31])  // seam bulkhead: floor to top wall
                cube([m ? mq_seam_rib[1] : mq_seam_rib[0] + 0.01, mq_tray_y1 - mq_back_t - mq_seam_rib[2] + 0.01, mq_panel[1] + 0.62]);
            if (m == 0) for (h = esp_holes)                            // ESP32 standoffs (2026-10-01: use its screw holes; M2);
                translate([xo - 0.01, esp_y0 + h[0], esp_z0 + h[1]]) rotate([0, 90, 0]) esp_post();   // component side faces the wall
            if (m == 0) for (h = esp_holes)                            // print support: 3 mm rib (wall side, clear of the can/buttons
                translate([xo - 0.01, esp_y0 + h[0], esp_z0 + h[1] - esp_post_d/2])   //   which start 3.6 off the wall) back to the skin
                    cube([3.01, mq_tray_y1 - mq_back_t - esp_y0 - h[0] + 0.01, esp_post_d]);
            // (no buck shelf since 2026-10-01: the J2D50K2405 has screw ears on both short ends that the lip would hit;
            //  the buck stands on the floor at the right end, VHB on its flat face - free zone x 125-164, y 33-54, z 6-86)
        }
        if (m == 0) for (h = esp_holes)                                // pilots: 8.7 deep (0.5 mm skin left) - M2x10 through the board
            translate([xo + esp_pad + 0.01, esp_y0 + h[0], esp_z0 + h[1]]) rotate([0, -90, 0]) cylinder(d = form_hole(esp_screw), h = esp_pad + 1.7, $fn = 16);
        for (h = mq_use_inserts(m)) translate([pc[0] + h[0], mq_fl_y - 1, pc[1] + h[1]]) rotate([-90, 0, 0]) {
            cylinder(d = 3.4, h = mq_tray_y1 + 2);
            translate([0, 0, mq_tray_y1 - mq_fl_y + 1 - mq_tube[1]]) cylinder(d = 6.5, h = mq_tube[1] + 2);   // head recess from the back
        }
        // ONE cable for power + data (2026-10-01): GX16-8 socket in the right tray's back (prints in the first layers,
        // no overhang). Inside: pins 1-4 -> buck (right end), pins 5-8 -> USB pigtail along the floor to the ESP32 (left end).
        if (m == 1) translate([mq_gx[0], mq_tray_y1 - mq_back_t - 1, mq_gx[1]]) rotate([-90, 0, 0]) cylinder(d = gx_d, h = mq_back_t + 2);
        if (m == 1 && gx_label) translate([mq_gx[0], mq_tray_y1 - 0.6, mq_gx[1] + 15]) rotate([90, 0, 180])
            linear_extrude(1) text("DMD", size = 4.5, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
        // (no back vents since 2026-10-01: the buck lies flat on the back skin there; ~1.5 W at a typical 3 A load)
        for (x = mq_saddle_x) if ((x > 0) == (m == 1))                 // plate screws up into the bottom wall
            translate([x, (mq_cov_y0 - mq_proud)/2, -0.01]) cylinder(d = m3_ins_d, h = mq_pz - 0.3 - 0.5);   // M3 insert from below, 0.5 skin
        // seam joint, INSIDE (2026-10-01): screws run along x from the left rib into M3 inserts in the right rib
        for (z = mq_seam_z) translate([0, mq_seam_rib[3], z]) rotate([0, 90, 0])
            if (m == 0) translate([0, 0, -mq_seam_rib[0] - 1]) cylinder(d = 3.4, h = mq_seam_rib[0] + 1.01, $fn = 24);   // clearance
            else { translate([0, 0, -0.01]) cylinder(d = m3_ins_d, h = m3_ins_l, $fn = 24);                              // insert
                   cylinder(d = 3.2, h = 8, $fn = 16); }                                                                // screw tip room
    }
}
// seam BULKHEADS, one per tray, butting at x = 0: [left thickness, right thickness, y0, screw y]. Full cavity height and
// fused to the floor, back skin AND top wall (2026-10-02: "vulnerable to breaking in half?" - the first ribs
// hung off the 2.4 mm back skin only and nothing tied the top of the seam). Start at y 35: behind the panel plugs
// (end y 33); ribbon, harness and the USB pigtail cross the seam in front of them (y 15-35).
// left 5 thick (screw head side, M3x10 socket head -> 5 mm into the insert), right 9 (insert 5.5 + tip room).
// 3 screws between the panel-screw tubes (x +-17.5 at z 8.5-18.5 / 73.5-83.5): a 2.5 mm hex key reaches them along x.
mq_seam_rib = [5, 9, 35, 45];
mq_seam_z   = [24, 46, 68];
module mq_place() {             // head-local -> case coords, as mounted on the back wall
    translate([W/2, D + mq_gap + 1, mq_plate_z1 + 6]) rotate([-mq_tilt, 0, 0]) children();
}
module marquee_plate() {        // slides on the rails; the saddle carries the head at mq_tilt
    difference() {
        union() {
            translate([(W - mq_plate_w)/2, D + mq_gap + mq_plate_t, mq_plate_z0])
                rotate([90, 0, 0]) linear_extrude(mq_plate_t) hull() {
                    square([mq_plate_w, mq_plate_z1 - mq_plate_z0 - corner_r]);
                    for (x = [corner_r, mq_plate_w - corner_r])
                        translate([x, mq_plate_z1 - mq_plate_z0 - corner_r]) circle(corner_r);
                }
            intersection() {                                           // saddle: plate top -> 6 mm slab under the frame,
                hull() {                                               // trimmed flush with the plate's front face
                    translate([(W - 200)/2, D + mq_gap, mq_plate_z1 - 12]) cube([200, mq_plate_t, 1]);
                    mq_place() translate([-110, -mq_proud, -6]) cube([220, mq_cov_y0 + mq_proud, 6]);
                }
                translate([-10, D + mq_gap, 0]) cube([W + 20, 200, 300]);
            }
        }
        // 2026-10-03: straight-sided slots, not dovetails - they clear the rails of the first printed case (which widen to a
        // 14 mm rectangle near the top) as well as fixed rails. Tipping back is stopped by one M3x8 per rail instead:
        // through the plate into an M3 insert melted into the rail face (drill the rail through this 4 mm hole).
        for (x = mq_rail_x) {
            translate([x - mq_crest/2 - mq_slide_clr, D + mq_gap - eps, mq_plate_z0 - 1])
                cube([mq_crest + 2*mq_slide_clr, mq_deep + mq_slide_clr + eps, mq_z1 + 0.4 - (mq_plate_z0 - 1)]);
            // stops 0.4 mm short of the slot (keeps the printed bridge over the slot whole); the drill opens it
            translate([x, D + mq_gap + mq_deep + mq_slide_clr + 0.4, mq_rail_screw_z]) rotate([-90, 0, 0]) cylinder(d = 4.0, h = mq_plate_t, $fn = 32);
        }
        mq_place() for (x = mq_saddle_x) translate([x, (mq_cov_y0 - mq_proud)/2, -7]) {
            cylinder(d = 3.4, h = 8);
            // head/driver channel. The screw axis leans 30 deg, so "from below" runs THROUGH the plate and out of its
            // case-facing face - the first plate had only a 3 mm counterbore here and the screws could not be fitted
            // (2026-10-02). Screw the trays on BEFORE sliding the plate onto the case.
            translate([0, 0, -70]) cylinder(d = 6.5, h = 73);
        }
    }
}
module marquee() {              // the whole module as mounted
    marquee_plate();
    mq_place() for (m = [0, 1]) mq_tray_half(m);
}
module marquee_components() {   // visualisation only
    mq_place() {
        color([0.12, 0.12, 0.12]) translate([-mq_panel[0]/2, 0, mq_pz]) cube([mq_panel[0], mq_panel[2], mq_panel[1]]);
        color("Orange") translate([-130, -0.5, mq_pz + 44]) cube([260, 1, 14]);
        color("Cyan")   translate([-90,  -0.5, mq_pz + 22]) cube([180, 1, 8]);
        color("RoyalBlue") translate([mq_panel[0]/2 + 0.3 + mq_end_relief - buck_env[0], mq_tray_y1 - mq_back_t - buck_env[1], mq_pz - 0.3]) cube(buck_env);   // 10 A buck on the right end wall
        color("DarkSlateGray") translate([-mq_panel[0]/2 - 0.3 - mq_end_relief + esp_pad, esp_y0, esp_z0]) cube([1.6, 29, 52]);        // ESP32 board on its pad (7 mm)
        color("SlateGray", 0.5) translate([-mq_panel[0]/2 - 0.3 - mq_end_relief + esp_pad, esp_y0, esp_z0]) cube([35, 29, 52]);       // ESP32 + jumper envelope
        color("Silver") translate([-mq_panel[0]/2 - 0.3 - mq_end_relief + esp_pad - 1.6 - 3.25, esp_y0 + 14.5 - 6, esp_z0 - 25]) cube([6.5, 12, 25]);  // USB-C plug
    }
}
module mock_button(d, cap) {          // origin on the panel surface, body hangs down
    color(cap) {
        cylinder(d = d + 5, h = 2.5);                                    // bezel ring
        translate([0, 0, 2.5 - eps]) cylinder(d = d - 6, h = 4);         // plunger
    }
    color("DimGray") translate([0, 0, -36]) cylinder(d = d - 1, h = 36); // body + microswitch
}

module case_components() {            // everything that mounts on the case / top panel
    for (p = six_btns_b)   translate([fb(p)[0], fb(p)[1], H]) mock_button(btn_d, "WhiteSmoke");
    for (p = start_btns_b) translate([fb(p)[0], fb(p)[1], H]) mock_button(start_d, "Red");
    // flipper buttons in the side walls
    for (m = [0, 1]) mirror([m, 0, 0]) translate([m ? -W : 0, 0, 0]) {
        color("Yellow") {
            translate([-2, D - flipper_yb, H - btn_drop]) rotate([0, 90, 0]) cylinder(d = btn_d + 5, h = 2 + eps);
            translate([-6, D - flipper_yb, H - btn_drop]) rotate([0, 90, 0]) cylinder(d = btn_d - 6, h = 4 + eps);
        }
        color("DimGray") translate([eps, D - flipper_yb, H - btn_drop]) rotate([0, 90, 0]) cylinder(d = btn_d - 1, h = 36);
    }
    // joystick: plate under the panel, shaft + ball above
    color("Silver") translate([joy_c[0] - joy_plate[0]/2, joy_c[1] - joy_plate[1]/2, H - top_t - joy_plate_t]) cube([joy_plate[0], joy_plate[1], joy_plate_t]);
    color("Black")  translate([joy_c[0], joy_c[1], H - eps]) cylinder(d = 40, h = 1.2);   // dust washer
    color("Black")  translate([joy_c[0], joy_c[1], H - top_t]) cylinder(d = 9.5, h = top_t + 28);
    color("Red")    translate([joy_c[0], joy_c[1], H + 28 + 14]) sphere(d = 34);
    // encoder PCB on its standoffs
    ec = [(pcb_posts[0][0] + pcb_posts[3][0])/2, (pcb_posts[0][1] + pcb_posts[3][1])/2];
    color("Green") translate([ec[0] - 18, ec[1] - 46, H - top_t - pcb_post_h - 1.6]) cube([36, 92, 1.6]);
    // exciter inside its locating ring
    color("Silver")   translate([exc_pos[0], exc_pos[1], H - top_t - 3]) cylinder(d = exc_pad_d, h = 3);
    color("DimGray") translate([exc_pos[0], exc_pos[1], H - top_t - exc_h]) cylinder(d = exc_d, h = exc_h - 8);
    color("Orange") translate([exc_pos[0], exc_pos[1], H - top_t - exc_h - exc_gap - exc_bridge[2]]) exc_bridge();
    // status display: clear plate + board + strips, and its clamp
    if (td_on) {
        zf = H - top_t + td_pocket_d;
        color("LightCyan", 0.6) translate([td_bc[0] - td_board[0]/2, td_bc[1] - td_board[1]/2, zf - 5.4]) cube([td_board[0], td_board[1], 5.4]);
        color("Black") translate([td_bc[0] - td_board[0]/2, td_bc[1] - td_board[1]/2, zf - 6.7]) cube([td_board[0], td_board[1], 1.3]);
        for (sy = [-1, 1]) color("DimGray") translate([td_bc[0] - 16, td_bc[1] + sy*11.6 - 1.25, zf - td_A]) cube([32, 2.5, td_A - 6.7]);
        color("Orange") translate([td_cc[0], td_cc[1], zf - td_A - td_foam - td_clamp[2]]) td_clamp();
    }
    // rear panel connectors
    if (mq_gx_x == 0) {
        color("Black") translate([dc_x, D - wall - 6, H - dc_drop]) rotate([-90, 0, 0]) cylinder(d = 13.5, h = 13);
        color("Black") translate([usb_panel_x - 8, D - wall - 10, H - usb_panel_drop - 4]) cube([16, 12, 8]);
    }
    for (gxx = [gx_x, mq_gx_x]) if (gxx > 0)
        color("Silver") translate([gxx, D - wall - 22, H - dc_drop]) rotate([-90, 0, 0]) cylinder(d = 19, h = 22);
}

cover_pcb_colors = ["DarkSeaGreen", "RoyalBlue", "RoyalBlue", "Green", "MediumPurple", "DarkSlateGray"];
module cover_components() {           // cover-local coords, matching cover()
    for (i = [0 : len(cover_pcbs) - 1]) {
        b = cover_pcbs[i];
        color(cover_pcb_colors[i])
            translate([b[0] - b[6]/2 - cov_off, b[1] - b[7]/2 - cov_off, cover_t + post_h(b)]) cube([b[6], b[7], b[8]]);
    }
    // solenoids on their cradles, rods aimed at the strikers
    sol_zc = cover_t + sol_pad_h + sol_body[2]/2;
    for (m = [0, 1]) {
        bx = m ? W - (wall + striker_t + sol_gap + sol_rod_out) - sol_body[0] : wall + striker_t + sol_gap + sol_rod_out;
        color("Gray") translate([bx - cov_off, sol_y - sol_body[1]/2 - cov_off, cover_t + sol_pad_h]) cube(sol_body);
        color("Silver") translate([m ? bx + sol_body[0] - cov_off : bx - cov_off, sol_y - cov_off, sol_zc])
            rotate([0, m ? 90 : -90, 0]) cylinder(d = 5, h = sol_rod_out);
    }
}

if (part == "assembly") {
    case();
    if (show_components) case_components();
    if (show_components && marquee_rails) mq_at_wall() { marquee(); marquee_components(); }
    translate([cov_off, cov_off, 0]) {
        color("orange") cover();
        if (show_components) cover_components();
    }
    if (joy_mount == "clamp")
        color("teal") translate([joy_c[0], joy_c[1], H - top_t - joy_plate_t - joy_frame_t]) joy_clamp();
}
if (part == "cover_loaded") {         // the electronics bay on its own
    cover();
    if (show_components) cover_components();
}
if (part == "case_loaded") {          // case interior with its components, no cover
    case();
    if (show_components) case_components();
}
if (part == "marquee") mq_at_wall() marquee();
// printable parts, each in print orientation and all support-free:
if (part == "marquee_plate")        translate([0, 110, -(D + mq_gap)]) rotate([90, 0, 0]) marquee_plate();   /* y +110: lands on the plate area */   // front face (grooves) down, saddle up
if (part == "marquee_tray_left")    translate([0, 0, mq_tray_y1]) rotate([-90, 0, 0]) mq_tray_half(0);   // back down
if (part == "marquee_tray_right")   translate([0, 0, mq_tray_y1]) rotate([-90, 0, 0]) mq_tray_half(1);
if (part == "marquee_frame_left")   translate([0, 0, mq_cov_y0]) rotate([-90, 0, 0]) mq_frame_half(0);   // flange down
// 10-minute check of the flange hole pattern (screws + locating pins): just the 6 mm flange of the left frame
if (part == "marquee_flange_test")  translate([0, 0, mq_cov_y0]) rotate([-90, 0, 0])
    intersection() { mq_frame_half(0); translate([-300, mq_fl_y, -10]) cube([600, mq_fl_t + 0.01, 200]); }
// seam alignment pins for the frame halves (the 3.2 mm holes, 12 deep each side): 4 printed pins, lying flat
// with a small flat on the underside so they print cleanly. Use 2, keep 2 spare. (Or: M3 screw shanks, heads cut off.)
if (part == "marquee_seam_pins") for (i = [0 : 3]) translate([0, i*6, 0])
    intersection() { translate([0, 0, 1.3]) rotate([0, 90, 0]) cylinder(d = 3.0, h = 22, $fn = 32);
                     translate([-1, -2, 0]) cube([24, 4, 4]); }
if (part == "marquee_frame_right")  translate([0, 0, mq_cov_y0]) rotate([-90, 0, 0]) mq_frame_half(1);
if (part == "marquee_cover_left")   translate([0, 0, mq_cov_y1]) rotate([-90, 0, 0]) mq_cover_half(0);   // back down
if (part == "marquee_cover_right")  translate([0, 0, mq_cov_y1]) rotate([-90, 0, 0]) mq_cover_half(1);
if (part == "marquee_loaded") {       // module + panel mock
    mq_at_wall() {
        marquee();
        if (show_components) marquee_components();
    }
}

// ---------------- render exports (renders/export_stls.py) ----------------
// The printed parts in assembled case coordinates, for the Blender product renders (not for printing).
if (part == "r_case")    case();
if (part == "r_cover")   translate([cov_off, cov_off, 0]) cover();
if (part == "r_marquee") mq_at_wall() marquee();
// every position the render scripts need, as one JSON echo:  openscad -o x.echo -D 'part="r_echo"' ...
if (part == "r_echo") {
    ec = [(pcb_posts[0][0] + pcb_posts[3][0])/2, (pcb_posts[0][1] + pcb_posts[3][1])/2];
    sols = [for (m = [0, 1]) let(bx = m ? W - (wall + striker_t + sol_gap + sol_rod_out) - sol_body[0]
                                        : wall + striker_t + sol_gap + sol_rod_out) [bx, sol_y - sol_body[1]/2, cover_t + sol_pad_h, m]];
    echo(str("RJSON{\"W\":", W, ",\"D\":", D, ",\"H\":", H, ",\"top_t\":", top_t, ",\"cover_t\":", cover_t,
        ",\"cov_off\":", cov_off, ",\"btn_d\":", btn_d, ",\"start_d\":", start_d,
        ",\"six\":", [for (p = six_btns_b) fb(p)], ",\"start\":", [for (p = start_btns_b) fb(p)],
        ",\"flip_y\":", D - flipper_yb, ",\"flip_z\":", H - btn_drop,
        ",\"joy\":", joy_c, ",\"joy_plate\":", joy_plate, ",\"enc\":", ec, ",\"enc_z\":", H - top_t - pcb_post_h - 1.6,
        ",\"exc\":", exc_pos, ",\"exc_d\":", exc_d, ",\"exc_h\":", exc_h, ",\"exc_pad\":", exc_pad_d,
        ",\"td\":", td_bc, ",\"td_board\":", td_board, ",\"td_z\":", H - top_t + td_pocket_d,
        ",\"gx\":", [gx_x, mq_gx_x], ",\"gx_z\":", H - dc_drop,
        ",\"pcbs\":", [for (b = cover_pcbs) [b[0], b[1], cover_t + post_h(b), b[6], b[7], b[8]]],
        ",\"sol_body\":", sol_body, ",\"sols\":", sols, ",\"sol_rod\":", sol_rod_out,
        ",\"mq_origin\":", [W/2, D + mq_gap + 1, mq_plate_z1 + 6], ",\"mq_tilt\":", mq_tilt,
        ",\"mq_panel\":", mq_panel, ",\"mq_pz\":", mq_pz, "}"));
}
