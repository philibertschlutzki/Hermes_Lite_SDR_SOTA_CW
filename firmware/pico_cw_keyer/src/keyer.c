#include "keyer.h"

#include <string.h>

#include "cw_morse.h"

// -----------------------------------------------------------------------------
// Hilfen
// -----------------------------------------------------------------------------

static uint8_t clamp_u8(uint8_t v, uint8_t lo, uint8_t hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

uint16_t keyer_fifo_level(const keyer_t* k) {
  return (uint16_t)((k->fifo_head - k->fifo_tail) & (CW_FIFO_SIZE - 1));
}

static void fifo_clear(keyer_t* k) { k->fifo_tail = k->fifo_head; }

static bool fifo_pop(keyer_t* k, char* c) {
  if (k->fifo_tail == k->fifo_head) return false;
  *c = (char)k->fifo[k->fifo_tail];
  k->fifo_tail = (uint16_t)((k->fifo_tail + 1) & (CW_FIFO_SIZE - 1));
  return true;
}

static void fifo_push(keyer_t* k, uint8_t c) {
  uint16_t next = (uint16_t)((k->fifo_head + 1) & (CW_FIFO_SIZE - 1));
  if (next == k->fifo_tail) {
    k->regs[REG_CW_ERROR] = CW_ERR_FIFO_OVERFLOW;
    return;
  }
  k->fifo[k->fifo_head] = c;
  k->fifo_head = next;
}

static void outputs_off(keyer_t* k) {
  if (k->set_key) k->set_key(false);
  if (k->set_ptt) k->set_ptt(false);
}

uint64_t keyer_tx_freq_hz(const keyer_t* k) {
  uint64_t f = 0;
  for (int r = REG_TX_FREQ_BYTE4; r <= REG_TX_FREQ_BYTE0; r++) f = (f << 8) | k->regs[r];
  return f;
}

// PARIS: Dit = 1200 / WPM ms. Farnsworth dehnt nur Zeichen-/Wortabstände,
// Gewichtung verlängert Key-down und verkürzt die folgende Pause gleich viel,
// so dass das Tempo erhalten bleibt.
keyer_timing_t keyer_compute_timing(uint8_t wpm, uint8_t farnsworth_wpm, uint8_t weight_pct) {
  wpm = clamp_u8(wpm, 5, 60);
  if (farnsworth_wpm == 0 || farnsworth_wpm > wpm) farnsworth_wpm = wpm;
  if (farnsworth_wpm < 5) farnsworth_wpm = 5;
  if (weight_pct == 0) weight_pct = 50;
  weight_pct = clamp_u8(weight_pct, 25, 75);

  uint32_t dit = 1200000u / wpm;
  keyer_timing_t t;
  uint32_t delta = (weight_pct >= 50) ? dit * (uint32_t)(weight_pct - 50) / 50u : 0;
  uint32_t shrink = (weight_pct < 50) ? dit * (uint32_t)(50 - weight_pct) / 50u : 0;
  t.weight_delta_us = delta;
  t.dit_on_us = dit + delta - shrink;
  t.dah_on_us = 3u * dit + delta - shrink;
  t.intra_us = dit - delta + shrink;

  // Farnsworth (ARRL): zusätzliche Pause so verteilen, dass das Wort PARIS
  // (31 Dits Elemente/Intra, 19 Dits Abstände) farnsworth_wpm ergibt.
  uint32_t space_unit = dit;
  if (farnsworth_wpm < wpm) {
    uint64_t total_us = 60000000ull / farnsworth_wpm;   // ein Wort
    uint64_t elem_us = 31ull * dit;
    space_unit = (uint32_t)((total_us - elem_us) / 19ull);
  }
  t.inter_char_us = 3u * space_unit - delta + shrink;
  t.inter_word_us = 7u * space_unit - delta + shrink;
  return t;
}

// -----------------------------------------------------------------------------
// Init / Register
// -----------------------------------------------------------------------------

static void reset_standard_regs(keyer_t* k) {
  for (int r = 0; r < CW_REG_BASE; r++) k->regs[r] = 0;
  k->regs[REG_FIRMWARE_MAJOR] = FW_VERSION_MAJOR;
  k->regs[REG_FIRMWARE_MINOR] = FW_VERSION_MINOR;
  k->regs[REG_INPUT_PINS] = 0x01;  // EXTTR high = RX
}

void keyer_init(keyer_t* k, keyer_output_fn set_key, keyer_output_fn set_ptt) {
  memset((void*)k, 0, sizeof(*k));
  k->set_key = set_key;
  k->set_ptt = set_ptt;
  reset_standard_regs(k);
  k->regs[REG_CW_CMD] = CW_CMD_IDLE;
  k->regs[REG_CW_STATUS] = CW_STATUS_IDLE;
  k->regs[REG_CW_WPM] = 20;
  k->regs[REG_PTT_LEAD_MS] = 80;
  k->regs[REG_PTT_TAIL_MS] = 120;
  k->regs[REG_FARNSWORTH_WPM] = 0;
  k->regs[REG_WEIGHT_PCT] = 50;
  k->regs[REG_CW_WATCHDOG_S] = 3;
  k->regs[REG_CW_API_VERSION] = CW_KEYER_API;
  k->regs[REG_CW_MAGIC] = CW_KEYER_MAGIC;
  k->state = KS_IDLE;
  outputs_off(k);
}

static bool reg_is_readonly(uint8_t reg) {
  switch (reg) {
    case REG_INPUT_PINS:
    case REG_FIRMWARE_MAJOR:
    case REG_FIRMWARE_MINOR:
    case REG_CW_STATUS:
    case REG_CW_ERROR:
    case REG_CW_PROGRESS:
    case REG_CW_FIFO_LEVEL:
    case REG_CW_API_VERSION:
    case REG_CW_MAGIC:
      return true;
    default:
      return false;
  }
}

static void reg_write(keyer_t* k, uint8_t reg, uint8_t val, uint64_t now_us) {
  k->last_host_us = now_us;  // jeder Write zählt als Lebenszeichen des Hosts
  if (reg_is_readonly(reg)) return;

  switch (reg) {
    case REG_TX_FREQ_BYTE0:
      k->regs[reg] = val;
      k->freq_changed = true;
      return;
    case REG_CONTROL:
      if (val == 1) reset_standard_regs(k);
      return;
    case REG_CW_CMD:
      k->regs[reg] = val;
      if (val == CW_CMD_START) {
        k->start_req = true;
      } else if (val == CW_CMD_ABORT) {
        // Sofort loslassen, nicht erst in der Hauptschleife
        if (k->set_key) k->set_key(false);
        fifo_clear(k);
        k->abort_req = true;
      } else if (val == CW_CMD_CLEAR) {
        fifo_clear(k);
        k->regs[REG_CW_ERROR] = CW_ERR_NONE;
      }
      return;
    case REG_CW_FIFO_DATA:
      fifo_push(k, val);
      return;
    case REG_CW_KEY_DIRECT:
      k->regs[reg] = val ? 1 : 0;
      if (!val && k->set_key) k->set_key(false);
      return;
    case REG_CW_HEARTBEAT:
      k->regs[reg] = val;
      return;
    default:
      k->regs[reg] = val;
      return;
  }
}

static uint8_t reg_read(keyer_t* k, uint8_t reg) {
  switch (reg) {
    case REG_CW_FIFO_LEVEL: {
      uint16_t lvl = keyer_fifo_level(k);
      return (uint8_t)(lvl > 255 ? 255 : lvl);
    }
    case REG_CW_FIFO_DATA:
      return 0;
    default:
      return k->regs[reg];
  }
}

// -----------------------------------------------------------------------------
// I2C-Slave
// -----------------------------------------------------------------------------

void keyer_i2c_receive(keyer_t* k, uint8_t byte, uint64_t now_us) {
  if (!k->i2c_have_reg) {
    k->i2c_reg = byte;
    k->i2c_have_reg = true;
    return;
  }
  reg_write(k, k->i2c_reg, byte, now_us);
  if (k->i2c_reg != REG_CW_FIFO_DATA) k->i2c_reg++;  // FIFO-Register zählt nicht weiter
}

uint8_t keyer_i2c_request(keyer_t* k) {
  uint8_t v = reg_read(k, k->i2c_reg);
  k->i2c_reg++;
  return v;
}

void keyer_i2c_finish(keyer_t* k) { k->i2c_have_reg = false; }

// -----------------------------------------------------------------------------
// Zustandsautomat
// -----------------------------------------------------------------------------

static void finish(keyer_t* k, uint8_t status, uint8_t err) {
  outputs_off(k);
  k->state = KS_IDLE;
  k->pattern = 0;
  k->regs[REG_CW_STATUS] = status;
  if (err) k->regs[REG_CW_ERROR] = err;
  k->regs[REG_CW_CMD] = CW_CMD_IDLE;
}

// Nächstes Element starten oder nächstes Zeichen holen. `t` = Startzeitpunkt.
static void advance(keyer_t* k, uint64_t t) {
  for (;;) {
    if (k->pattern && *k->pattern) {
      char e = *k->pattern++;
      uint32_t on = (e == '-') ? k->timing.dah_on_us : k->timing.dit_on_us;
      if (k->set_key) k->set_key(true);
      k->state = KS_ELEMENT_ON;
      k->t_next = t + on;
      return;
    }
    char c;
    if (!fifo_pop(k, &c)) {
      k->state = KS_TAIL;
      k->t_next = t + (uint64_t)k->regs[REG_PTT_TAIL_MS] * 1000u;
      return;
    }
    k->regs[REG_CW_PROGRESS]++;
    if (cw_is_word_gap(c)) {
      // inter_char wurde nach dem letzten Zeichen schon gewartet
      uint32_t extra = k->timing.inter_word_us > k->timing.inter_char_us
                           ? k->timing.inter_word_us - k->timing.inter_char_us : 0;
      k->state = KS_ELEMENT_OFF;
      k->pattern = 0;
      k->t_next = t + extra;
      return;
    }
    k->pattern = cw_morse_pattern(c);  // unbekannte Zeichen: NULL -> überspringen
  }
}

void keyer_poll(keyer_t* k, uint64_t now) {
  if (k->abort_req) {
    k->abort_req = false;
    k->start_req = false;
    k->regs[REG_CW_KEY_DIRECT] = 0;
    finish(k, CW_STATUS_ABORTED, CW_ERR_NONE);
    return;
  }

  // Host-Watchdog: Pi/Netz weg -> Taste und PTT los
  if (k->state != KS_IDLE) {
    uint64_t wd = (uint64_t)clamp_u8(k->regs[REG_CW_WATCHDOG_S], 1, 30) * 1000000u;
    if (now - k->last_host_us > wd) {
      k->regs[REG_CW_KEY_DIRECT] = 0;
      fifo_clear(k);
      finish(k, CW_STATUS_ERROR, CW_ERR_HOST_WATCHDOG);
      return;
    }
  }

  // Tune (Dauerträger) hat Vorrang vor Text, aber nur aus IDLE heraus
  if (k->state == KS_IDLE && k->regs[REG_CW_KEY_DIRECT]) {
    k->state = KS_TUNE;
    k->tune_start = now;
    k->regs[REG_CW_STATUS] = CW_STATUS_TUNE;
    k->regs[REG_CW_ERROR] = CW_ERR_NONE;
    if (k->set_ptt) k->set_ptt(true);
    if (k->set_key) k->set_key(true);
    return;
  }
  if (k->state == KS_TUNE) {
    if (!k->regs[REG_CW_KEY_DIRECT]) {
      finish(k, CW_STATUS_IDLE, CW_ERR_NONE);
    } else if (now - k->tune_start > CW_TUNE_MAX_US) {
      k->regs[REG_CW_KEY_DIRECT] = 0;
      finish(k, CW_STATUS_ERROR, CW_ERR_TUNE_TIMEOUT);
    }
    return;
  }

  if (k->start_req) {
    k->start_req = false;
    if (k->state == KS_IDLE) {
      k->timing = keyer_compute_timing(k->regs[REG_CW_WPM], k->regs[REG_FARNSWORTH_WPM], k->regs[REG_WEIGHT_PCT]);
      k->regs[REG_CW_PROGRESS] = 0;
      k->regs[REG_CW_STATUS] = CW_STATUS_RUNNING;
      k->pattern = 0;
      if (k->set_ptt) k->set_ptt(true);
      k->state = KS_LEAD;
      k->t_next = now + (uint64_t)k->regs[REG_PTT_LEAD_MS] * 1000u;
    }
    // START während eines laufenden Auftrags: Text wird einfach weiter gesendet
  }

  if (k->state == KS_IDLE || now < k->t_next) return;

  // Fällige Übergänge mit dem geplanten Zeitpunkt (nicht `now`), damit sich
  // Abfrage-Jitter nicht aufsummiert.
  uint64_t t = k->t_next;
  switch (k->state) {
    case KS_LEAD:
      advance(k, t);
      break;
    case KS_ELEMENT_ON: {
      if (k->set_key) k->set_key(false);
      bool last = !(k->pattern && *k->pattern);
      k->state = KS_ELEMENT_OFF;
      k->t_next = t + (last ? k->timing.inter_char_us : k->timing.intra_us);
      break;
    }
    case KS_ELEMENT_OFF:
      advance(k, t);
      break;
    case KS_TAIL:
      if (keyer_fifo_level(k) > 0) {  // Type-ahead während des Nachlaufs
        advance(k, now);
      } else {
        finish(k, CW_STATUS_DONE, CW_ERR_NONE);
      }
      break;
    default:
      break;
  }
}
