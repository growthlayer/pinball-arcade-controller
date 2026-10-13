// Read / set ZeDMD's RGB order (0-5) and save it on the device. Usage: zedmd_rgb [newOrder]
#include "ZeDMD.h"
#include <cstdio>
#include <cstdlib>
#include <chrono>
#include <thread>
int main(int argc, char** argv) {
  ZeDMD* z = new ZeDMD();
  bool ok = false;   // opening the port resets the ESP32 - retry while it boots
  for (int i = 0; i < 6 && !(ok = z->Open()); i++) std::this_thread::sleep_for(std::chrono::seconds(2));
  if (!ok) { printf("ZeDMD not found\n"); return 1; }
  printf("current RGB order: %d\n", z->GetRGBOrder());
  if (argc > 1) { z->SetRGBOrder((uint8_t)atoi(argv[1])); z->SaveSettings(); printf("set + saved: %d\n", atoi(argv[1])); }
  z->Close(); delete z; return 0;
}
