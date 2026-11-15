// SOTA-CW-Firmware für das HL2-IO-Board (N2ADR, Raspberry Pi Pico).
//
// - I2C-Slave an i2c1 (GPIO14 SDA, GPIO15 SCL), Adresse 0x1D: der HL2 leitet
//   C&C-Befehle 0x3D (I2C2) des Hosts hierher weiter. Damit braucht der Pi
//   nur das Netzwerkkabel zum HL2.
// - Standardregister 0..12 (Frequenz, Eingänge, Lüfter, RF-Eingänge, HPF).
// - CW-Keyer ab Register 200: Text-FIFO, Morse-Timing im Pico, Ausgabe auf
//   die Low-Side-Schalter Out7 (KEY) und Out8 (PTT) am ACC-Anschluss (D-Sub).
//   Ein externes Keying-Kabel führt sie auf die 3,5-mm-Key-Buchse CN4 des HL2:
//   Out7 -> Tip, Out8 -> Ring, GND -> Sleeve.
//
// Pinbelegung nach hl2ioboard.h (jimahlstrom/HL2IOBoard).
#include <stdbool.h>
#include <stdint.h>

#include "hardware/gpio.h"
#include "hardware/i2c.h"
#include "hardware/pwm.h"
#include "hardware/watchdog.h"
#include "pico/i2c_slave.h"
#include "pico/stdlib.h"

#include "ioboard_regs.h"
#include "keyer.h"

// --- IO-Board-Pins (GPIO-Nummern) ---
#define GPIO_HPF      0
#define GPIO_SW12     1
#define GPIO_RF3      2
#define GPIO_INTTR    3
#define GPIO_FAN      4
#define GPIO_IN5      6
#define GPIO_IN4      7
#define GPIO_OUT8     8
#define GPIO_OUT7     9
#define GPIO_OUT5     10
#define GPIO_OUT4     11
#define GPIO_SW5      12
#define GPIO_EXTTR    13
#define GPIO_I2C_SDA  14
#define GPIO_I2C_SCL  15
#define GPIO_OUT1     16
#define GPIO_IN1      17
#define GPIO_IN2      18
#define GPIO_OUT2     19
#define GPIO_OUT3     20
#define GPIO_IN3      21
#define GPIO_OUT6     22
#define GPIO_LED      25

// Keying-Ausgänge: Low-Side-Schalter (High am GPIO = Ausgang nach GND).
// Per CMake überschreibbar, z. B. -DKEY_GPIO=22 für Out6.
#ifndef KEY_GPIO
#define KEY_GPIO GPIO_OUT7   // Out7 (J6 Pin 7) -> Keying-Kabel -> CN4 Tip (Key)
#endif
#ifndef PTT_GPIO
#define PTT_GPIO GPIO_OUT8   // Out8 (J6 Pin 8) -> Keying-Kabel -> CN4 Ring (PTT)
#endif

#define I2C_BAUD   (400 * 1000)
#define FAN_WRAP   1020
#define HPF_MIN_HZ 2550000u  // wie CheckHPF der Standardfirmware (fcode 76)

static keyer_t g_keyer;

static void set_key(bool on) {
  gpio_put(KEY_GPIO, on);
  gpio_put(GPIO_LED, on);
}

static void set_ptt(bool on) { gpio_put(PTT_GPIO, on); }

static void i2c_handler(i2c_inst_t* i2c, i2c_slave_event_t event) {
  switch (event) {
    case I2C_SLAVE_RECEIVE:
      keyer_i2c_receive(&g_keyer, i2c_read_byte_raw(i2c), time_us_64());
      break;
    case I2C_SLAVE_REQUEST:
      i2c_write_byte_raw(i2c, keyer_i2c_request(&g_keyer));
      break;
    case I2C_SLAVE_FINISH:
      keyer_i2c_finish(&g_keyer);
      break;
    default:
      break;
  }
}

static void out_init(uint pin, bool level) {
  gpio_init(pin);
  gpio_put(pin, level);
  gpio_set_dir(pin, GPIO_OUT);
}

static void in_init(uint pin) {
  gpio_init(pin);
  gpio_set_dir(pin, GPIO_IN);
}

static void configure_pins(void) {
  // Ausgänge zuerst sicher auf Low (Taste los, PTT aus)
  const uint outs[] = {GPIO_HPF, GPIO_SW12, GPIO_RF3, GPIO_INTTR, GPIO_OUT1, GPIO_OUT2, GPIO_OUT3, GPIO_OUT4,
                       GPIO_OUT5, GPIO_OUT6, GPIO_OUT7, GPIO_OUT8, GPIO_SW5, GPIO_LED};
  for (unsigned i = 0; i < sizeof outs / sizeof outs[0]; i++) out_init(outs[i], false);

  const uint ins[] = {GPIO_EXTTR, GPIO_IN1, GPIO_IN2, GPIO_IN3, GPIO_IN4, GPIO_IN5};
  for (unsigned i = 0; i < sizeof ins / sizeof ins[0]; i++) in_init(ins[i]);

  gpio_set_function(GPIO_FAN, GPIO_FUNC_PWM);
  uint slice = pwm_gpio_to_slice_num(GPIO_FAN);
  pwm_set_wrap(slice, FAN_WRAP);
  pwm_set_gpio_level(GPIO_FAN, 0);
  pwm_set_enabled(slice, true);

  gpio_set_function(GPIO_I2C_SDA, GPIO_FUNC_I2C);
  gpio_set_function(GPIO_I2C_SCL, GPIO_FUNC_I2C);
  i2c_init(i2c1, I2C_BAUD);
  i2c_slave_init(i2c1, IOBOARD_I2C_ADDR, &i2c_handler);
}

static uint8_t read_inputs(void) {
  uint8_t v = 0;
  if (gpio_get(GPIO_EXTTR)) v |= 0x01;  // 1 = RX
  if (gpio_get(GPIO_IN1)) v |= 0x02;
  if (gpio_get(GPIO_IN2)) v |= 0x04;
  if (gpio_get(GPIO_IN3)) v |= 0x08;
  if (gpio_get(GPIO_IN4)) v |= 0x10;
  if (gpio_get(GPIO_IN5)) v |= 0x20;
  return v;
}

static void update_standard_outputs(void) {
  static uint8_t last_fan = 0xFF;
  uint8_t fan = g_keyer.regs[REG_FAN_SPEED];
  if (fan != last_fan) {
    pwm_set_gpio_level(GPIO_FAN, (uint16_t)fan * 4u);
    last_fan = fan;
  }

  uint8_t inputs = read_inputs();
  g_keyer.regs[REG_INPUT_PINS] = inputs;
  bool rx = inputs & 0x01;

  switch (g_keyer.regs[REG_RF_INPUTS]) {
    case 1:
      gpio_put(GPIO_INTTR, 1);
      gpio_put(GPIO_RF3, 1);
      break;
    case 2:
      gpio_put(GPIO_INTTR, 1);
      gpio_put(GPIO_RF3, rx);  // RX über J9, TX-Rückkopplung über J10
      break;
    default:
      gpio_put(GPIO_INTTR, 0);
      gpio_put(GPIO_RF3, 0);
      break;
  }

  if (g_keyer.freq_changed) {
    g_keyer.freq_changed = false;
    gpio_put(GPIO_HPF, keyer_tx_freq_hz(&g_keyer) > HPF_MIN_HZ);
  }
}

int main(void) {
  keyer_init(&g_keyer, set_key, set_ptt);
  configure_pins();
  stdio_init_all();

  // Hängt die Hauptschleife, startet der Pico neu; beim Start sind alle Ausgänge aus.
  watchdog_enable(200, true);

  while (true) {
    keyer_poll(&g_keyer, time_us_64());
    update_standard_outputs();
    watchdog_update();
    busy_wait_us_32(20);
  }
}
