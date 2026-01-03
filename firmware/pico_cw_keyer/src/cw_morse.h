#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef struct {
  uint32_t dit_ms;
  uint32_t dah_ms;
  uint32_t intra_symbol_ms;
  uint32_t inter_char_ms;
  uint32_t inter_word_ms;
} cw_timing_t;

cw_timing_t cw_timing_from_wpm(uint16_t wpm);

// Returns pointer to a null-terminated pattern string consisting of '.' and '-'.
// Returns NULL if unsupported character.
const char* cw_morse_pattern(char c);

bool cw_is_word_gap(char c);
