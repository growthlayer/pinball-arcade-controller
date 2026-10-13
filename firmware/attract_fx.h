// Colour attract show for the marquee (128x32), rendered live - pinball-controller, 2026-10-03.
// Plain C++ (no Arduino dependencies): the ZeDMD firmware calls FxRender() 30 times a second while the PC is silent,
// and tools/attract_sim.cpp compiles the same file on the Mac to preview / test it on the panels.
// Scenes: plasma + PINBALL, fire + FREE PLAY, pinball table, warp + JACKPOT fireworks, rainbow wave scroller,
// matrix rain revealing PINBALL, chase lights + high score.
#pragma once
#include <math.h>
#include <stdint.h>
#include <string.h>

#include "attract_text.h"

namespace fx {

static const int W = 128, H = 32;
static uint8_t* fb;  // W*H*3 RGB, set by FxRender

static uint32_t rng = 0x12345678;
static inline uint32_t rnd() { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static inline float frnd() { return (rnd() & 0xFFFF) / 65535.0f; }
static inline uint8_t clamp8(int v) { return v < 0 ? 0 : (v > 255 ? 255 : v); }

static void hsv(uint8_t h, uint8_t s, uint8_t v, uint8_t* r, uint8_t* g, uint8_t* b) {
  uint8_t reg = h / 43, rem = (h - reg * 43) * 6;
  uint8_t p = (v * (255 - s)) >> 8, q = (v * (255 - ((s * rem) >> 8))) >> 8, t = (v * (255 - ((s * (255 - rem)) >> 8))) >> 8;
  switch (reg) {
    case 0: *r = v; *g = t; *b = p; break;
    case 1: *r = q; *g = v; *b = p; break;
    case 2: *r = p; *g = v; *b = t; break;
    case 3: *r = p; *g = q; *b = v; break;
    case 4: *r = t; *g = p; *b = v; break;
    default: *r = v; *g = p; *b = q; break;
  }
}
static inline void put(int x, int y, uint8_t r, uint8_t g, uint8_t b) {
  if (x < 0 || y < 0 || x >= W || y >= H) return;
  uint8_t* p = fb + (y * W + x) * 3; p[0] = r; p[1] = g; p[2] = b;
}
static inline void add(int x, int y, int r, int g, int b) {
  if (x < 0 || y < 0 || x >= W || y >= H) return;
  uint8_t* p = fb + (y * W + x) * 3; p[0] = clamp8(p[0] + r); p[1] = clamp8(p[1] + g); p[2] = clamp8(p[2] + b);
}
static inline void blend(int x, int y, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
  if (x < 0 || y < 0 || x >= W || y >= H || !a) return;
  uint8_t* p = fb + (y * W + x) * 3;
  p[0] = (p[0] * (255 - a) + r * a) / 255; p[1] = (p[1] * (255 - a) + g * a) / 255; p[2] = (p[2] * (255 - a) + b * a) / 255;
}
static inline uint8_t maskAt(const FxMask& m, int x, int y) {
  return (x < 0 || y < 0 || x >= m.w || y >= m.h) ? 0 : m.a[y * m.w + x];
}
// Draw a mask centred at (cx, cy), scaled by s, with a black outline; colour from hue (or white if sat == 0).
static void text(const FxMask& m, float cx, float cy, float s, uint8_t hue0, uint8_t hueStep, uint8_t sat, uint8_t val,
                 bool outline = true) {
  const float hw = m.w * s / 2, hh = m.h * s / 2;
  const int x0 = (int)(cx - hw) - 1, x1 = (int)(cx + hw) + 1, y0 = (int)(cy - hh) - 1, y1 = (int)(cy + hh) + 1;
  for (int y = y0; y <= y1; y++)
    for (int x = x0; x <= x1; x++) {
      const int mx = (int)((x - cx) / s + m.w / 2.0f), my = (int)((y - cy) / s + m.h / 2.0f);
      const uint8_t a = maskAt(m, mx, my);
      if (outline && a < 100) {
        bool near = false;
        for (int dy = -1; dy <= 1 && !near; dy++)
          for (int dx = -1; dx <= 1; dx++)
            if (maskAt(m, (int)((x + dx - cx) / s + m.w / 2.0f), (int)((y + dy - cy) / s + m.h / 2.0f)) > 120) { near = true; break; }
        if (near) { put(x, y, 0, 0, 0); continue; }
      }
      if (a) {
        uint8_t r, g, b; hsv(hue0 + (x - x0) * hueStep, sat, val, &r, &g, &b); blend(x, y, r, g, b, a);
      }
    }
}

// ---------------------------------------------------------------- scenes (t = frame inside the scene)
static void plasma(int t) {
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++) {
      const float dx = x - 64, dy = (y - 16) * 2;
      const float v = sinf(x * 0.06f + t * 0.05f) + sinf(y * 0.15f + t * 0.07f) + sinf((x + y) * 0.05f + t * 0.03f) +
                      sinf(sqrtf(dx * dx + dy * dy) * 0.09f - t * 0.08f);
      uint8_t r, g, b; hsv((uint8_t)((v + 4) * 32 + t * 2), 255, 150, &r, &g, &b); put(x, y, r, g, b);
    }
  const float s = t < 24 ? 1.0f + (24 - t) * 0.12f : 1.0f + 0.04f * sinf(t * 0.15f);
  text(M_PINBALL, 64, 12, s, 0, 0, 0, 255);
  if (t > 30) text(M_CONTROLLER, 64, 27, 1, t * 3, 4, 200, 255);
}

static uint8_t heat[H + 2][W];
static void fire(int t) {
  if (t == 0) memset(heat, 0, sizeof heat);
  for (int x = 0; x < W; x++) heat[H + 1][x] = heat[H][x] = (rnd() & 3) ? 120 + (rnd() % 136) : 0;
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++) {
      const int l = heat[y + 1][(x + W - 1) % W], c = heat[y + 1][x], r = heat[y + 1][(x + 1) % W], d = heat[y + 2][x];
      const int v = (l + c + r + d) * 63 / 256 - (int)(rnd() % 3);
      heat[y][x] = v < 0 ? 0 : v;
    }
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++) {
      const int h = heat[y][x];   // black -> red -> orange -> yellow -> white
      put(x, y, clamp8(h * 3), clamp8(h * 3 - 255), clamp8(h * 3 - 510));
    }
  text(M_FREEPLAY, 64, 10, 1.0f + 0.03f * sinf(t * 0.2f), 30, 0, 80, 255);
  if ((t / 10) % 2) text(M_PRESSSTART, 64, 25, 1, 0, 0, 0, 255);
}

struct Spark { float x, y, vx, vy; uint8_t hue, life; };
static Spark sp[96];
static void sparkBurst(float x, float y, uint8_t hue, int n, float speed) {
  for (int i = 0; i < 96 && n > 0; i++)
    if (!sp[i].life) {
      const float a = frnd() * 6.283f, v = speed * (0.4f + frnd());
      sp[i] = {x, y, cosf(a) * v, sinf(a) * v * 0.6f, (uint8_t)(hue + rnd() % 30), (uint8_t)(18 + rnd() % 18)}; n--;
    }
}
static void sparks(float grav) {
  for (int i = 0; i < 96; i++)
    if (sp[i].life) {
      Spark& s = sp[i]; s.x += s.vx; s.y += s.vy; s.vy += grav; s.life--;
      uint8_t r, g, b; hsv(s.hue, s.life > 10 ? 200 : 120, (uint8_t)(s.life * 7 + 60), &r, &g, &b); add((int)s.x, (int)s.y, r, g, b);
    }
}

static float bx, by, bvx, bvy, trail[12][2];
static uint8_t bumpFlash[3];
static const float BUMP[3][2] = {{34, 11}, {64, 7}, {94, 11}};
static void table(int t) {
  if (t == 0) { bx = 20; by = 2; bvx = 1.3f; bvy = 0; memset(bumpFlash, 0, 3); memset(sp, 0, sizeof sp); for (auto& p : trail) { p[0] = bx; p[1] = by; } }
  for (int y = 0; y < H; y++)  // dark blue playfield with a faint grid
    for (int x = 0; x < W; x++) put(x, y, 0, 0, ((x + y) % 8 == 0) ? 40 : 18);
  for (int x = 0; x < W; x++) { put(x, 0, 60, 60, 120); }
  for (int y = 0; y < H; y++) { put(0, y, 60, 60, 120); put(W - 1, y, 60, 60, 120); }
  // physics (2 sub-steps)
  for (int k = 0; k < 2; k++) {
    bvy += 0.045f; bx += bvx * 0.5f; by += bvy * 0.5f;
    if (bx < 2) { bx = 2; bvx = fabsf(bvx); }
    if (bx > W - 3) { bx = W - 3; bvx = -fabsf(bvx); }
    if (by < 2) { by = 2; bvy = fabsf(bvy); }
    for (int i = 0; i < 3; i++) {
      const float dx = bx - BUMP[i][0], dy = (by - BUMP[i][1]) * 1.6f, d = sqrtf(dx * dx + dy * dy);
      if (d < 6 && d > 0.01f) {
        const float nx = dx / d, ny = dy / d, dot = bvx * nx + bvy * ny;
        if (dot < 0) { bvx -= 2.2f * dot * nx; bvy -= 2.2f * dot * ny; bumpFlash[i] = 12; sparkBurst(bx, by, i * 85, 14, 1.4f); }
      }
    }
    // flippers: kick the ball back up when it reaches them
    if (by > 26 && bvy > 0 && ((bx > 34 && bx < 60) || (bx > 68 && bx < 94))) {
      bvy = -2.6f - frnd() * 0.8f; bvx = (bx < 64 ? 1 : -1) * (0.6f + frnd() * 1.2f);
    }
    if (by > H + 2) { bx = 6 + frnd() * 110; by = 1; bvx = (frnd() - 0.5f) * 2.5f; bvy = 0; }
  }
  for (int i = 11; i > 0; i--) { trail[i][0] = trail[i - 1][0]; trail[i][1] = trail[i - 1][1]; }
  trail[0][0] = bx; trail[0][1] = by;
  // bumpers
  for (int i = 0; i < 3; i++) {
    uint8_t r, g, b; hsv(i * 85 + t * 2, bumpFlash[i] ? 60 : 255, bumpFlash[i] ? 255 : 150, &r, &g, &b);
    for (int dy = -3; dy <= 3; dy++)
      for (int dx = -5; dx <= 5; dx++)
        if (dx * dx + dy * dy * 3 <= 27) put((int)BUMP[i][0] + dx, (int)BUMP[i][1] + dy, r, g, b);
    if (bumpFlash[i]) bumpFlash[i]--;
  }
  // flippers (up when the ball is close)
  const bool up = by > 20 && bvy > 0;
  for (int i = 0; i <= 22; i++) {
    const float f = i / 22.0f, lift = up ? 5 : 0;
    put(36 + i, (int)(29 - f * (2 + lift)), 255, 200, 0); put(92 - i, (int)(29 - f * (2 + lift)), 255, 200, 0);
  }
  for (int i = 11; i >= 0; i--) {  // rainbow trail + ball
    uint8_t r, g, b; hsv(t * 6 + i * 18, 255, 255 - i * 20, &r, &g, &b); add((int)trail[i][0], (int)trail[i][1], r / 2, g / 2, b / 2);
  }
  for (int dy = -1; dy <= 1; dy++)
    for (int dx = -1; dx <= 1; dx++) if (dx * dx + dy * dy < 2) put((int)bx + dx, (int)by + dy, 230, 230, 255);
  sparks(0.05f);
}

struct Star { float x, y, z; uint8_t hue; };
static Star st[90];
static void warp(int t) {
  if (t == 0) { for (auto& s : st) { s = {frnd() * 2 - 1, frnd() * 2 - 1, frnd(), (uint8_t)(rnd() & 255)}; } memset(sp, 0, sizeof sp); }
  memset(fb, 0, W * H * 3);
  for (auto& s : st) {
    const float px = 64 + s.x / s.z * 40, py = 16 + s.y / s.z * 12;
    s.z -= 0.018f;
    if (s.z < 0.05f || px < 0 || px >= W || py < 0 || py >= H) { s = {frnd() * 2 - 1, frnd() * 2 - 1, 1, (uint8_t)(rnd() & 255)}; continue; }
    const float nx = 64 + s.x / s.z * 40, ny = 16 + s.y / s.z * 12;
    uint8_t r, g, b; hsv(s.hue, 120, (uint8_t)(255 * (1 - s.z * 0.7f)), &r, &g, &b);
    for (int k = 0; k <= 3; k++) add((int)(px + (nx - px) * k / 3), (int)(py + (ny - py) * k / 3), r, g, b);
  }
  if (t > 30 && t % 14 == 0) sparkBurst(10 + frnd() * 108, 4 + frnd() * 20, rnd() & 255, 40, 1.6f);
  sparks(0.04f);
  const float s = t < 30 ? 0.1f + t * 0.03f : 1.0f + 0.05f * sinf(t * 0.25f);
  text(M_JACKPOT, 64, 16, s, t * 5, 3, 255, 255);
}

static void scroller(int t) {
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++) put(x, y, 0, 0, 0);
  for (int i = 0; i < 40; i++) {  // twinkling stars
    const uint32_t h = i * 2654435761u; const int x = (h >> 8) % W, y = (h >> 20) % H;
    const uint8_t v = (uint8_t)(40 + 40 * sinf(t * 0.2f + i));
    put(x, y, v, v, v + 20);
  }
  const float off = t * 2.0f - W;
  for (int x = 0; x < W; x++) {
    const int mx = (int)(x + off);
    const int dy = (int)(6 * sinf(x * 0.08f + t * 0.15f));
    uint8_t r, g, b; hsv(x * 3 + t * 5, 255, 255, &r, &g, &b);
    for (int my = 0; my < M_SCROLL.h; my++) {
      const uint8_t a = maskAt(M_SCROLL, mx, my);
      if (a) blend(x, 9 + my + dy, r, g, b, a);
    }
  }
}

static uint8_t rainY[W], rainSpd[W], reveal[H][W];
static void matrix(int t) {
  if (t == 0) { for (int x = 0; x < W; x++) { rainY[x] = rnd() % 64; rainSpd[x] = 1 + rnd() % 3; } memset(reveal, 0, sizeof reveal); }
  for (int i = 0; i < W * H * 3; i += 3) { fb[i] = fb[i] * 7 / 10; fb[i + 1] = fb[i + 1] * 85 / 100; fb[i + 2] = fb[i + 2] * 7 / 10; }
  const int ox = 64 - M_PINBALL.w / 2, oy = 16 - M_PINBALL.h / 2;
  for (int x = 0; x < W; x++) {
    if (t % rainSpd[x] == 0) rainY[x]++;
    if (rainY[x] > 60) { rainY[x] = 0; rainSpd[x] = 1 + rnd() % 3; }
    const int y = rainY[x] - 10;
    put(x, y, 180, 255, 180);
    if (y >= 0 && y < H && maskAt(M_PINBALL, x - ox, y - oy) > 100) reveal[y][x] = 255;
  }
  for (int y = 0; y < H; y++)
    for (int x = 0; x < W; x++)
      if (reveal[y][x]) { add(x, y, 0, reveal[y][x] / 2, 0); if (reveal[y][x] < 250 && t > 60) reveal[y][x]++; }
  if (t > 120) text(M_PINBALL, 64, 16, 1, 80, 0, 160, (uint8_t)((t - 120) * 4 > 255 ? 255 : (t - 120) * 4), false);
}

static void chase(int t) {
  memset(fb, 0, W * H * 3);
  const int perim = 2 * (W + H) - 4;
  for (int i = 0; i < perim; i++) {  // marquee bulbs running round the edge
    int x, y;
    if (i < W) { x = i; y = 0; } else if (i < W + H - 1) { x = W - 1; y = i - W + 1; }
    else if (i < 2 * W + H - 2) { x = W - 1 - (i - (W + H - 1)) - 1; y = H - 1; } else { x = 0; y = H - 1 - (i - (2 * W + H - 2)) - 1; }
    if ((i + t / 2) % 4 == 0) { uint8_t r, g, b; hsv(i * 2 + t * 3, 200, 255, &r, &g, &b); put(x, y, r, g, b); }
  }
  text(M_HIGHSCORE, 64, 7, 1, 30, 0, 200, 255, false);
  text(M_SCORE, 64, 21, 1.0f + 0.04f * sinf(t * 0.2f), t * 4, 4, 255, 255);
  if ((t / 12) % 2) text(M_MRK, 115, 7, 1, 0, 0, 0, 230, false);
  if ((t / 12) % 2 == 0) text(M_MRK, 13, 7, 1, 0, 0, 0, 230, false);
}

// ---------------------------------------------------------------- sequencer
struct Scene { void (*fn)(int); int len; };
static const Scene SCENES[] = {{plasma, 210}, {fire, 200}, {table, 300}, {warp, 210},
                               {scroller, (int)((W + 1012) / 2.0f) + 10}, {matrix, 220}, {chase, 180}};
static const int NSCENES = sizeof(SCENES) / sizeof(SCENES[0]);
static int scene = 0, st_t = 0;

}  // namespace fx

// Render the next frame of the show into rgb (128*32*3). Call 30 times a second.
static void FxRender(uint8_t* rgb) {
  using namespace fx;
  fb = rgb;
  if (st_t >= SCENES[scene].len) { scene = (scene + 1) % NSCENES; st_t = 0; }
  SCENES[scene].fn(st_t);
  const int len = SCENES[scene].len, fade = 10;  // short fade in/out between scenes
  const int k = st_t < fade ? st_t : (len - 1 - st_t < fade ? len - 1 - st_t : fade);
  if (k < fade)
    for (int i = 0; i < W * H * 3; i++) rgb[i] = rgb[i] * k / fade;
  st_t++;
}
static void FxRestart() { fx::scene = 0; fx::st_t = 0; }
