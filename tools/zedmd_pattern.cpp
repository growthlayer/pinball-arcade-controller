// Orientation / colour test for the marquee (ZeDMD 128x32) - pinball-controller, 2026-10-03.
// Build (Mac): see tools/README.md.  Run: ./zedmd_pattern [seconds]
// Shows: RED square top-left, GREEN top-right, BLUE bottom-left, WHITE bottom-right, a white arrow pointing UP
// in the middle, colour bars (R G B Y C M W) along the bottom, and a 1-pixel border round the whole screen.
#include "ZeDMD.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>

static uint8_t img[128 * 32 * 3];
static void px(int x, int y, uint8_t r, uint8_t g, uint8_t b) {
  if (x < 0 || y < 0 || x >= 128 || y >= 32) return;
  uint8_t* p = img + (y * 128 + x) * 3; p[0] = r; p[1] = g; p[2] = b;
}
static void box(int x0, int y0, int w, int h, uint8_t r, uint8_t g, uint8_t b) {
  for (int y = y0; y < y0 + h; y++) for (int x = x0; x < x0 + w; x++) px(x, y, r, g, b);
}
int main(int argc, char** argv) {
  int secs = argc > 1 ? atoi(argv[1]) : 30;
  memset(img, 0, sizeof(img));
  for (int x = 0; x < 128; x++) { px(x, 0, 60, 60, 60); px(x, 31, 60, 60, 60); }
  for (int y = 0; y < 32; y++) { px(0, y, 60, 60, 60); px(127, y, 60, 60, 60); }
  box(1, 1, 8, 8, 255, 0, 0);       // top-left red
  box(119, 1, 8, 8, 0, 255, 0);     // top-right green
  box(1, 23, 8, 8, 0, 0, 255);      // bottom-left blue
  box(119, 23, 8, 8, 255, 255, 255);// bottom-right white
  for (int i = 0; i < 9; i++) box(64 - i, 3 + i, 2 * i + 1, 1, 255, 255, 255);   // arrow head pointing UP
  box(61, 12, 7, 8, 255, 255, 255);                                              // arrow shaft
  const uint8_t bars[7][3] = {{255,0,0},{0,255,0},{0,0,255},{255,255,0},{0,255,255},{255,0,255},{255,255,255}};
  for (int i = 0; i < 7; i++) box(14 + i * 14, 24, 12, 5, bars[i][0], bars[i][1], bars[i][2]);
  ZeDMD* z = new ZeDMD();
  bool ok = false;   // opening the port resets the ESP32 - retry while it boots
  for (int i = 0; i < 6 && !(ok = z->Open()); i++) std::this_thread::sleep_for(std::chrono::seconds(2));
  if (!ok) { printf("ZeDMD not found\n"); return 1; }
  z->SetFrameSize(128, 32);
  printf("Showing the test pattern for %d s\n", secs);
  for (int t = 0; t < secs; t++) { z->RenderRgb888(img); std::this_thread::sleep_for(std::chrono::seconds(1)); }
  z->ClearScreen(); z->Close(); delete z;
  return 0;
}
