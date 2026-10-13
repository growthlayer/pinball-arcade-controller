// Plays raw RGB888 128x32 frames on the marquee (ZeDMD). Usage: zedmd_play file.raw [fps=30] [loops=1]
#include "ZeDMD.h"
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <thread>
#include <vector>
int main(int argc, char** argv) {
  if (argc < 2) { printf("usage: zedmd_play file.raw [fps] [loops]\n"); return 1; }
  int fps = argc > 2 ? atoi(argv[2]) : 30, loops = argc > 3 ? atoi(argv[3]) : 1;
  FILE* f = fopen(argv[1], "rb"); if (!f) { printf("cannot open %s\n", argv[1]); return 1; }
  std::vector<uint8_t> data; uint8_t buf[65536]; size_t n;
  while ((n = fread(buf, 1, sizeof buf, f)) > 0) data.insert(data.end(), buf, buf + n);
  fclose(f);
  const size_t fs = 128 * 32 * 3, count = data.size() / fs;
  ZeDMD* z = new ZeDMD(); bool ok = false;   // opening the port resets the ESP32 - retry while it boots
  for (int i = 0; i < 6 && !(ok = z->Open()); i++) std::this_thread::sleep_for(std::chrono::seconds(2));
  if (!ok) { printf("ZeDMD not found\n"); return 1; }
  z->SetFrameSize(128, 32);
  printf("%zu frames at %d fps, %d loop(s)\n", count, fps, loops);
  auto t = std::chrono::steady_clock::now(); const auto step = std::chrono::microseconds(1000000 / fps);
  for (int l = 0; l < loops; l++)
    for (size_t i = 0; i < count; i++) { z->RenderRgb888(&data[i * fs]); t += step; std::this_thread::sleep_until(t); }
  z->ClearScreen(); z->Close(); delete z; return 0;
}
