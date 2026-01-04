#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef struct {
  uint32_t dit_us;
  uint32_t dah_us;
  uint32_t intra_symbol_us;
  uint32_t inter_char_us;
  uint32_t inter_word_us;
} cw_timing_t;

// Element speed based on PARIS standard: dit length = 1200 / WPM ms
cw_timing_t cw_timing_from_wpm(uint16_t wpm);

// Apply Farnsworth spacing: keep dit/dah element speed from current timing,
// but slow down inter-character and inter-word spacing using farnsworth_wpm.
// If farnsworth_wpm == 0, it is treated as element_wpm.
void cw_apply_farnsworth(cw_timing_t* t, uint16_t element_wpm, uint16_t farnsworth_wpm);

// Apply keying weight in percent (50 = nominal). This scales dit/dah key-down duration.
// Spacings are kept as-is (so extreme settings can affect effective speed).
void cw_apply_weight(cw_timing_t* t, uint16_t weight_pct);

// Returns pointer to a null-terminated pattern string consisting of '.' and '-'.
// Returns NULL if unsupported character.
const char* cw_morse_pattern(char c);

bool cw_is_word_gap(char c);
