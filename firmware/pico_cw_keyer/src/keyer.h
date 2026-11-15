#pragma once
// Plattformunabhängige Keyer-Logik (I2C-Registerbank + Morse-Zustandsautomat).
// Wird auf dem Pico von main.c und auf dem Host von test/test_keyer.c genutzt.
#include <stdbool.h>
#include <stdint.h>

#include "ioboard_regs.h"

typedef void (*keyer_output_fn)(bool on);

typedef enum {
  KS_IDLE = 0,
  KS_LEAD,
  KS_ELEMENT_ON,
  KS_ELEMENT_OFF,
  KS_TAIL,
  KS_TUNE,
} keyer_state_t;

typedef struct {
  uint32_t dit_on_us;   // Dit mit Gewichtung
  uint32_t dah_on_us;
  uint32_t intra_us;    // Pause nach Element (vor Gewichtungsausgleich)
  uint32_t weight_delta_us;  // +Verlängerung Key-down, -Verkürzung der Pause
  uint32_t inter_char_us;    // Pause nach letztem Element eines Zeichens
  uint32_t inter_word_us;    // Pause bei Leerzeichen (gesamt)
} keyer_timing_t;

typedef struct {
  volatile uint8_t regs[256];

  // FIFO (Produzent: I2C-IRQ, Konsument: Hauptschleife)
  volatile uint8_t fifo[CW_FIFO_SIZE];
  volatile uint16_t fifo_head;
  volatile uint16_t fifo_tail;

  // I2C-Slave-Zustand (nur IRQ)
  uint8_t i2c_reg;
  bool i2c_have_reg;

  // Anforderungen IRQ -> Hauptschleife
  volatile bool start_req;
  volatile bool abort_req;
  volatile bool freq_changed;
  volatile uint64_t last_host_us;

  // Automat (nur Hauptschleife)
  keyer_state_t state;
  uint64_t t_next;
  uint64_t tune_start;
  keyer_timing_t timing;
  const char* pattern;
  bool last_element_long;

  keyer_output_fn set_key;
  keyer_output_fn set_ptt;
} keyer_t;

void keyer_init(keyer_t* k, keyer_output_fn set_key, keyer_output_fn set_ptt);

// I2C-Slave-Ereignisse (aus der IRQ-Routine aufrufen)
void keyer_i2c_receive(keyer_t* k, uint8_t byte, uint64_t now_us);
uint8_t keyer_i2c_request(keyer_t* k);
void keyer_i2c_finish(keyer_t* k);

// Hauptschleife: so oft wie möglich aufrufen (Auflösung = Aufrufintervall)
void keyer_poll(keyer_t* k, uint64_t now_us);

uint64_t keyer_tx_freq_hz(const keyer_t* k);
uint16_t keyer_fifo_level(const keyer_t* k);
keyer_timing_t keyer_compute_timing(uint8_t wpm, uint8_t farnsworth_wpm, uint8_t weight_pct);
