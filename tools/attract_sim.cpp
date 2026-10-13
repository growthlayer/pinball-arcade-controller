// Renders the firmware's colour attract show on the Mac -> attract_sim.raw (128x32 RGB888, 30 fps).
#include <cstdio>
#include <vector>
#include "../firmware/attract_fx.h"
int main() {
  int total = 0; for (int i = 0; i < fx::NSCENES; i++) total += fx::SCENES[i].len;
  std::vector<uint8_t> f(128 * 32 * 3, 0);
  FILE* o = fopen("attract_sim.raw", "wb");
  for (int i = 0; i < total; i++) { FxRender(f.data()); fwrite(f.data(), 1, f.size(), o); }
  fclose(o); printf("%d frames, %.1f s\n", total, total / 30.0);
}
