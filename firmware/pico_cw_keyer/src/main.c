#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#include "pico/stdlib.h"

#include "ioboard_regs.h"
#include "cw_morse.h"
#include "outputs.h"

// -----------------------------------------------------------------------------
// Register access abstraction
//
// This repo ships with a mock register bank so the logic compiles and can be
// exercised on a Pico directly. For a real HL2 IO-Board integration, replace
// reg_read/reg_write with the board-specific register interface.
// -----------------------------------------------------------------------------

static volatile uint16_t g_regs[512];

static inline uint16_t reg_read(uint16_t addr) {
  if (addr < (uint16_t)(sizeof(g_regs) / sizeof(g_regs[0]))) return g_regs[addr];
  return 0;
}

static inline void reg_write(uint16_t addr, uint16_t value) {
  if (addr < (uint16_t)(sizeof(g_regs) / sizeof(g_regs[0]))) g_regs[addr] = value;
}

// -----------------------------------------------------------------------------

static void set_status(uint16_t st, uint16_t err) {
  reg_write(REG_CW_STATUS, st);
  reg_write(REG_ERROR_CODE, err);
}

static char text_get_char(uint16_t idx) {
  uint16_t reg = REG_TEXT_BUF + (idx / 2);
  uint16_t word = reg_read(reg);
  if ((idx % 2) == 0) return (char)((word >> 8) & 0xFF);
  return (char)(word & 0xFF);
}

static void key_down(uint32_t ms) {
  outputs_set_key(true);
  sleep_ms(ms);
  outputs_set_key(false);
}

static bool check_abort(void) {
  return reg_read(REG_CW_CMD) == CW_CMD_ABORT;
}

static void send_char(char c, cw_timing_t t) {
  const char* pat = cw_morse_pattern(c);
  if (!pat) return;

  for (const char* p = pat; *p; ++p) {
    if (check_abort()) return;
    if (*p == '.') key_down(t.dit_ms);
    else if (*p == '-') key_down(t.dah_ms);
    if (check_abort()) return;
    sleep_ms(t.intra_symbol_ms);
  }
}

int main(void) {
  stdio_init_all();
  outputs_init();

  // Init register defaults
  reg_write(REG_CW_CMD, CW_CMD_IDLE);
  set_status(CW_STATUS_IDLE, 0);
  reg_write(REG_CW_WPM, 20);
  reg_write(REG_PTT_LEAD_MS, 80);
  reg_write(REG_PTT_TAIL_MS, 120);
  reg_write(REG_TEXT_LEN, 0);
  reg_write(REG_PROGRESS, 0);

  while (true) {
    uint16_t cmd = reg_read(REG_CW_CMD);

    if (cmd != CW_CMD_START) {
      sleep_ms(10);
      continue;
    }

    // Latch parameters
    uint16_t wpm = reg_read(REG_CW_WPM);
    uint16_t lead = reg_read(REG_PTT_LEAD_MS);
    uint16_t tail = reg_read(REG_PTT_TAIL_MS);
    uint16_t len  = reg_read(REG_TEXT_LEN);

    if (len > TEXT_MAX_CHARS) {
      set_status(CW_STATUS_ERROR, 1);
      reg_write(REG_CW_CMD, CW_CMD_IDLE);
      continue;
    }

    cw_timing_t timing = cw_timing_from_wpm(wpm);

    reg_write(REG_PROGRESS, 0);
    set_status(CW_STATUS_RUNNING, 0);

    outputs_set_ptt(true);
    sleep_ms(lead);

    bool aborted = false;

    for (uint16_t i = 0; i < len; i++) {
      if (check_abort()) { aborted = true; break; }

      char c = text_get_char(i);
      if (c == 0) break;

      if (cw_is_word_gap(c)) {
        sleep_ms(timing.inter_word_ms);
      } else {
        send_char(c, timing);
        sleep_ms(timing.inter_char_ms);
      }

      reg_write(REG_PROGRESS, i + 1);
    }

    sleep_ms(tail);
    outputs_set_ptt(false);
    outputs_set_key(false);

    if (aborted) set_status(CW_STATUS_ABORTED, 0);
    else set_status(CW_STATUS_DONE, 0);

    // Return to idle
    reg_write(REG_CW_CMD, CW_CMD_IDLE);

    sleep_ms(10);
  }
}
