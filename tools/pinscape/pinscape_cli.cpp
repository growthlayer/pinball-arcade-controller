// Mac/Linux helper for the Pinscape Pico over its vendor interface (uses PinscapePico/LinuxAPI + libusb).
// pinscape_cli log | getconfig | putconfig <file.json> | reboot
#include "PinscapeVendorInterface.h"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <thread>
#include <chrono>
using PinscapePico::Linux::PinscapeVendorInterface;
int main(int argc, char** argv) {
  if (argc < 2) { fprintf(stderr, "usage: %s log|getconfig|putconfig <file>|reboot\n", argv[0]); return 2; }
  PinscapeVendorInterface p;
  if (!p.Open()) { fprintf(stderr, "Pinscape Pico not found / could not open vendor interface\n"); return 1; }
  std::string c = argv[1];
  if (c == "log") {
    for (int i = 0; i < 50; i++) {
      std::vector<uint8_t> b; uint32_t avail = 0;
      if (!p.QueryLog(b, avail) || b.empty()) break;
      fwrite(b.data(), 1, b.size(), stdout);
      if (avail == 0) break;
    }
  } else if (c == "getconfig") {
    std::vector<uint8_t> b;
    if (!p.GetConfig(b)) { fprintf(stderr, "no config stored (or read failed)\n"); return 1; }
    fwrite(b.data(), 1, b.size(), stdout);
  } else if (c == "putconfig" && argc > 2) {
    std::ifstream f(argv[2], std::ios::binary);
    std::vector<uint8_t> b((std::istreambuf_iterator<char>(f)), {});
    if (b.empty()) { fprintf(stderr, "empty file\n"); return 1; }
    if (!p.PutConfig(b)) { fprintf(stderr, "PutConfig failed\n"); return 1; }
    printf("config stored (%zu bytes); rebooting\n", b.size());
    p.Reboot();
  } else if (c == "reboot") {
    p.Reboot();
  } else { fprintf(stderr, "unknown command\n"); return 2; }
  return 0;
}
