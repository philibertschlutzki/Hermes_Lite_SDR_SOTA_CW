#include "outputs.h"

#include "pico/stdlib.h"
#include "hardware/gpio.h"

#ifndef PTT_GPIO
#define PTT_GPIO 2
#endif

#ifndef KEY_GPIO
#define KEY_GPIO 3
#endif

void outputs_init(void) {
  gpio_init(PTT_GPIO);
  gpio_set_dir(PTT_GPIO, GPIO_OUT);
  gpio_put(PTT_GPIO, 0);

  gpio_init(KEY_GPIO);
  gpio_set_dir(KEY_GPIO, GPIO_OUT);
  gpio_put(KEY_GPIO, 0);
}

void outputs_set_ptt(bool on) {
  gpio_put(PTT_GPIO, on ? 1 : 0);
}

void outputs_set_key(bool on) {
  gpio_put(KEY_GPIO, on ? 1 : 0);
}
