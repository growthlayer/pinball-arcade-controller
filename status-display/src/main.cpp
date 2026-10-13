// Pinball controller status display - LilyGO T-Display-S3 (1.9" 170x320 LCD), USB CDC serial.
//
// The host sends one command per line (115200 8N1, any line ending):
//   HELLO            -> replies "STATUS-DISPLAY 1" (lets the host find the right port)
//   TABLE <text>     table name in the top bar
//   NUDGE <x> <y>    nudge vector, -100..100 each axis
//   TILT <0-3>       0 = none, 1-2 = warnings, 3 = TILT
//   HEAT <l> <r>     flipper coil heat estimate, 0-100 each (host models it from flipper presses)
//   MSG <text>       one-line message at the bottom
//   CLEAR            reset every field
//   FRAME            measuring aid: 1-px white frame on the outermost pixels + centre cross (any other command exits)
// Anything else replies "ERR <line>". The screen dims to "waiting for PC" 5 s after the last command.
// The DMD shows the game; this screen shows the controller (nudge, tilt, coil heat) - see README.

#include <Arduino.h>
#include <Arduino_GFX_Library.h>

static const int PIN_POWER_ON = 15;   // must be HIGH for the LCD to run from USB/battery
static const int PIN_LCD_BL   = 38;

Arduino_DataBus *bus = new Arduino_ESP32PAR8Q(7 /*DC*/, 6 /*CS*/, 8 /*WR*/, 9 /*RD*/,
                                              39, 40, 41, 42, 45, 46, 47, 48 /*D0-D7*/);
Arduino_GFX *lcd = new Arduino_ST7789(bus, 5 /*RST*/, 1 /*landscape*/, true /*IPS*/,
                                      170, 320, 35, 0, 35, 0);
Arduino_Canvas *gfx = new Arduino_Canvas(320, 170, lcd);   // draw off-screen, flush once: no flicker

static const uint16_t C_BG = 0x0000, C_DIM = 0x4208, C_TXT = 0xFFFF, C_ACC = 0x04FF,
                      C_OK = 0x07E0, C_WARN = 0xFD20, C_BAD = 0xF800;

struct State {
    String table = "", msg = "";
    int nx = 0, ny = 0, peak = 0, tilt = 0, heatL = 0, heatR = 0;
    uint32_t lastRx = 0, peakAt = 0;
} st;

String line;
bool dirty = true;
bool frameMode = false;

static void handle(const String &l) {
    int sp = l.indexOf(' ');
    String cmd = (sp < 0 ? l : l.substring(0, sp)), arg = (sp < 0 ? "" : l.substring(sp + 1));
    cmd.toUpperCase();
    frameMode = (cmd == "FRAME");
    if (frameMode) { dirty = true; return; }
    if (cmd == "HELLO") Serial.println("STATUS-DISPLAY 1");
    else if (cmd == "TABLE") st.table = arg;
    else if (cmd == "MSG")   st.msg = arg;
    else if (cmd == "HEAT") {
        int sp2 = arg.indexOf(' ');
        st.heatL = constrain(arg.substring(0, sp2).toInt(), 0, 100);
        st.heatR = constrain(sp2 < 0 ? 0 : arg.substring(sp2 + 1).toInt(), 0, 100);
    }
    else if (cmd == "TILT")  st.tilt = constrain(arg.toInt(), 0, 3);
    else if (cmd == "NUDGE") {
        int sp2 = arg.indexOf(' ');
        st.nx = constrain(arg.substring(0, sp2).toInt(), -100, 100);
        st.ny = constrain(sp2 < 0 ? 0 : arg.substring(sp2 + 1).toInt(), -100, 100);
        int m = max(abs(st.nx), abs(st.ny));
        if (m > st.peak || millis() - st.peakAt > 10000) { st.peak = m; st.peakAt = millis(); }   // peak holds 10 s
    } else if (cmd == "CLEAR") st = State();
    else { Serial.print("ERR "); Serial.println(l); return; }
    st.lastRx = millis();
    dirty = true;
}

static void drawNudge(int x0, int y0, int s) {   // square s x s, centre crosshair, dot at the vector
    int cx = x0 + s / 2, cy = y0 + s / 2, r = s / 2 - 4;
    gfx->drawRect(x0, y0, s, s, C_DIM);
    gfx->drawFastHLine(x0 + 4, cy, s - 8, C_DIM);
    gfx->drawFastVLine(cx, y0 + 4, s - 8, C_DIM);
    gfx->drawCircle(cx, cy, r / 2, C_DIM);
    int px = cx + st.nx * r / 100, py = cy - st.ny * r / 100;
    int m = max(abs(st.nx), abs(st.ny));
    uint16_t c = m > 80 ? C_BAD : m > 50 ? C_WARN : C_OK;
    gfx->drawLine(cx, cy, px, py, c);
    gfx->fillCircle(px, py, 6, c);
    gfx->setTextSize(1); gfx->setTextColor(C_DIM);
    gfx->setCursor(x0, y0 + s + 4); gfx->print("NUDGE  peak "); gfx->print(st.peak);
}

static void renderFrame() {   // outermost pixel ring + corner ticks + centre cross, for measuring the active area
    gfx->fillScreen(C_BG);
    gfx->drawRect(0, 0, 320, 170, C_TXT);
    gfx->drawRect(1, 1, 318, 168, C_BAD);
    gfx->drawFastHLine(150, 85, 20, C_TXT); gfx->drawFastVLine(160, 75, 20, C_TXT);
    gfx->setTextSize(1); gfx->setTextColor(C_DIM);
    gfx->setCursor(110, 110); gfx->print("320 x 170 px  FRAME");
    gfx->setCursor(8, 8); gfx->print("USB end?");
    gfx->flush();
}

static void render() {
    if (frameMode) { renderFrame(); return; }
    bool live = st.lastRx && millis() - st.lastRx < 5000;
    gfx->fillScreen(C_BG);

    // top bar: table name + link dot
    gfx->fillRect(0, 0, 320, 24, 0x10A2);
    gfx->setTextSize(2); gfx->setTextColor(C_TXT);
    gfx->setCursor(6, 5);
    gfx->print(st.table.length() ? st.table.substring(0, 24) : String("Pinball controller"));
    gfx->fillCircle(310, 12, 5, live ? C_OK : C_DIM);

    drawNudge(8, 32, 116);

    // right column: coil heat bars
    int x = 138;
    gfx->setTextSize(1); gfx->setTextColor(C_DIM);
    gfx->setCursor(x, 34); gfx->print("FLIPPER COIL HEAT");
    const int heat[2] = {st.heatL, st.heatR};
    for (int i = 0; i < 2; i++) {
        int y = 46 + i * 26, w = 150, h = 18, bx = x + 18;
        gfx->setTextSize(2); gfx->setTextColor(C_TXT);
        gfx->setCursor(x, y + 2); gfx->print(i ? "R" : "L");
        gfx->drawRect(bx, y, w, h, C_DIM);
        uint16_t c = heat[i] >= 85 ? C_BAD : heat[i] >= 60 ? C_WARN : C_OK;
        gfx->fillRect(bx + 2, y + 2, (w - 4) * heat[i] / 100, h - 4, c);
        if (heat[i] >= 85) { gfx->setTextSize(1); gfx->setTextColor(C_TXT); gfx->setCursor(bx + w - 44, y + 6); gfx->print("REST IT"); }
    }
    if (st.tilt) {   // warnings as pips, TILT as a full red banner
        if (st.tilt >= 3) {
            gfx->fillRoundRect(x, 104, 174, 34, 6, C_BAD);
            gfx->setTextSize(3); gfx->setTextColor(C_TXT);
            gfx->setCursor(x + 50, 110); gfx->print("TILT");
        } else {
            gfx->setTextSize(2); gfx->setTextColor(C_WARN);
            gfx->setCursor(x, 112); gfx->print("DANGER");
            for (int i = 0; i < st.tilt; i++) gfx->fillCircle(x + 90 + i * 18, 119, 6, C_WARN);
        }
    }

    // bottom line
    gfx->setTextSize(1); gfx->setTextColor(live ? C_TXT : C_DIM);
    gfx->setCursor(x, 156);
    gfx->print(live ? st.msg.substring(0, 29) : String("waiting for PC..."));
    gfx->flush();
}

void setup() {
    pinMode(PIN_POWER_ON, OUTPUT); digitalWrite(PIN_POWER_ON, HIGH);
    pinMode(PIN_LCD_BL, OUTPUT);   digitalWrite(PIN_LCD_BL, HIGH);
    Serial.begin(115200);
    gfx->begin();
    render();
}

void loop() {
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') { line.trim(); if (line.length()) handle(line); line = ""; }
        else if (line.length() < 120) line += c;
    }
    static uint32_t lastDraw = 0;
    static bool wasLive = false;
    bool live = st.lastRx && millis() - st.lastRx < 5000;
    if (live != wasLive) { dirty = true; wasLive = live; }
    if (dirty && millis() - lastDraw > 33) { render(); dirty = false; lastDraw = millis(); }   // <= 30 fps
}
