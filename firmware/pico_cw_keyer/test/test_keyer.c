// Host-Test der Keyer-Logik: gcc -I../src test_keyer.c ../src/keyer.c ../src/cw_morse.c
#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "keyer.h"

static keyer_t K;
static bool key_on, ptt_on;
static uint64_t now;

// Protokoll der Tastenwechsel
#define MAXEV 4096
static uint64_t ev_t[MAXEV];
static bool ev_v[MAXEV];
static int nev;

static void set_key(bool on) {
  if (on != key_on && nev < MAXEV) { ev_t[nev] = now; ev_v[nev] = on; nev++; }
  key_on = on;
}
static void set_ptt(bool on) { ptt_on = on; }

// HL2-I2C-Write: Registernummer + ein Datenbyte, dann Stop
static void hl2_write(uint8_t reg, uint8_t val) {
  keyer_i2c_receive(&K, reg, now);
  keyer_i2c_receive(&K, val, now);
  keyer_i2c_finish(&K);
}

// HL2-I2C-Read: Registernummer, dann 4 Bytes
static void hl2_read4(uint8_t reg, uint8_t out[4]) {
  keyer_i2c_receive(&K, reg, now);
  for (int i = 0; i < 4; i++) out[i] = keyer_i2c_request(&K);
  keyer_i2c_finish(&K);
}

static void run_until(uint64_t t_end, bool heartbeat) {
  uint64_t last_hb = now;
  while (now < t_end) {
    now += 50;  // 50 µs Abfrageintervall
    if (heartbeat && now - last_hb >= 500000) { hl2_write(REG_CW_HEARTBEAT, 1); last_hb = now; }
    keyer_poll(&K, now);
  }
}

static void reset(void) {
  memset(&K, 0, sizeof K);
  key_on = ptt_on = false;
  now = 1000000;
  nev = 0;
  keyer_init(&K, set_key, set_ptt);
}

static void send(const char* s, uint8_t wpm) {
  hl2_write(REG_CW_CMD, CW_CMD_CLEAR);
  hl2_write(REG_CW_WPM, wpm);
  hl2_write(REG_PTT_LEAD_MS, 50);
  hl2_write(REG_PTT_TAIL_MS, 100);
  for (const char* p = s; *p; p++) hl2_write(REG_CW_FIFO_DATA, (uint8_t)*p);
  hl2_write(REG_CW_CMD, CW_CMD_START);
}

static void test_identity(void) {
  reset();
  uint8_t b[4];
  hl2_read4(REG_CW_WATCHDOG_S, b);
  assert(b[0] == 3 && b[2] == CW_KEYER_API && b[3] == CW_KEYER_MAGIC);
  hl2_read4(REG_FIRMWARE_MAJOR, b);
  assert(b[0] == FW_VERSION_MAJOR && b[1] == FW_VERSION_MINOR);
}

static void test_freq_regs(void) {
  reset();
  uint64_t f = 14074000;
  for (int r = 0; r < 5; r++) hl2_write((uint8_t)r, (uint8_t)(f >> (8 * (4 - r))));
  assert(K.freq_changed);
  assert(keyer_tx_freq_hz(&K) == f);
}

static void test_paris_timing(void) {
  reset();
  send("PARIS", 20);  // Dit = 60 ms
  run_until(now + 5000000, true);
  assert(K.regs[REG_CW_STATUS] == CW_STATUS_DONE);
  assert(!key_on && !ptt_on);
  // PARIS: 14 Elemente -> 28 Wechsel
  assert(nev == 28);
  // Erstes Element 'P' = Dit 60 ms nach 50 ms Vorlauf
  assert(ev_v[0] && ev_t[1] - ev_t[0] == 60000);
  // Dah des 'P': 180 ms
  assert(ev_t[3] - ev_t[2] == 180000);
  // Intra 60 ms
  assert(ev_t[2] - ev_t[1] == 60000);
  // Ende 'P' bis Beginn 'A': 3 Dits
  assert(ev_t[8] - ev_t[7] == 180000);
  // Gesamt erstes Key-down bis letztes Key-up = 50 - 7 (ohne Wortpause) - 3 + ... = 43 Dits
  assert(ev_t[27] - ev_t[0] == 43u * 60000u);
  assert(K.regs[REG_CW_PROGRESS] == 5);
}

static void test_word_gap(void) {
  reset();
  send("E E", 20);
  run_until(now + 3000000, true);
  assert(nev == 4);
  // Key-up des ersten E bis Key-down des zweiten = 7 Dits
  assert(ev_t[2] - ev_t[1] == 7u * 60000u);
}

static void test_abort_is_immediate(void) {
  reset();
  send("TTTTTTTT", 10);
  run_until(now + 200000, true);  // im ersten Dah
  assert(key_on);
  hl2_write(REG_CW_CMD, CW_CMD_ABORT);
  assert(!key_on);  // schon im IRQ-Pfad losgelassen
  keyer_poll(&K, now + 50);
  assert(K.regs[REG_CW_STATUS] == CW_STATUS_ABORTED && !ptt_on);
  assert(keyer_fifo_level(&K) == 0);
}

static void test_host_watchdog(void) {
  reset();
  send("TTTTTTTTTTTTTTTTTTTT", 10);
  run_until(now + 4000000, false);  // kein Heartbeat, Watchdog 3 s
  assert(!key_on && !ptt_on);
  assert(K.regs[REG_CW_STATUS] == CW_STATUS_ERROR);
  assert(K.regs[REG_CW_ERROR] == CW_ERR_HOST_WATCHDOG);
}

static void test_tune_limit(void) {
  reset();
  hl2_write(REG_CW_KEY_DIRECT, 1);
  run_until(now + 1000, true);
  assert(key_on && ptt_on && K.regs[REG_CW_STATUS] == CW_STATUS_TUNE);
  run_until(now + 16000000, true);
  assert(!key_on && K.regs[REG_CW_ERROR] == CW_ERR_TUNE_TIMEOUT);
}

static void test_tune_off(void) {
  reset();
  hl2_write(REG_CW_KEY_DIRECT, 1);
  run_until(now + 1000, true);
  hl2_write(REG_CW_KEY_DIRECT, 0);
  assert(!key_on);
  run_until(now + 1000, true);
  assert(K.regs[REG_CW_STATUS] == CW_STATUS_IDLE && !ptt_on);
}

static void test_fifo_overflow_and_level(void) {
  reset();
  for (int i = 0; i < 300; i++) hl2_write(REG_CW_FIFO_DATA, 'E');
  uint8_t b[4];
  hl2_read4(REG_CW_PROGRESS, b);
  assert(b[1] == 255);  // FIFO-Level
  assert(K.regs[REG_CW_ERROR] == CW_ERR_FIFO_OVERFLOW);
}

static void test_readonly(void) {
  reset();
  hl2_write(REG_CW_MAGIC, 0);
  hl2_write(REG_CW_STATUS, 7);
  assert(K.regs[REG_CW_MAGIC] == CW_KEYER_MAGIC && K.regs[REG_CW_STATUS] == CW_STATUS_IDLE);
}

static void test_farnsworth(void) {
  keyer_timing_t t = keyer_compute_timing(25, 15, 50);
  // Elemente mit 25 WPM (48 ms), Zeichenabstand länger als 3 Dits
  assert(t.dit_on_us == 48000);
  assert(t.inter_char_us > 3u * 48000u);
  // PARIS bei 15 WPM = 4 s
  uint64_t word = 31ull * 48000u + 4ull * t.inter_char_us + t.inter_word_us;
  assert(word > 3990000 && word < 4010000);
}

static void test_weight_keeps_speed(void) {
  keyer_timing_t a = keyer_compute_timing(20, 0, 50);
  keyer_timing_t b = keyer_compute_timing(20, 0, 60);
  assert(b.dit_on_us > a.dit_on_us);
  assert(b.dit_on_us + b.intra_us == a.dit_on_us + a.intra_us);
}

int main(void) {
  test_identity();
  test_freq_regs();
  test_paris_timing();
  test_word_gap();
  test_abort_is_immediate();
  test_host_watchdog();
  test_tune_limit();
  test_tune_off();
  test_fifo_overflow_and_level();
  test_readonly();
  test_farnsworth();
  test_weight_keeps_speed();
  printf("keyer tests: OK\n");
  return 0;
}
