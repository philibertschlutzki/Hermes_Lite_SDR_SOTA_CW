#include "cw_morse.h"

static inline uint32_t clamp_u32(uint32_t v, uint32_t lo, uint32_t hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

static inline uint16_t clamp_u16(uint16_t v, uint16_t lo, uint16_t hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

// PARIS standard: dit length = 1200 / WPM ms
cw_timing_t cw_timing_from_wpm(uint16_t wpm) {
  if (wpm < 5) wpm = 5;
  if (wpm > 60) wpm = 60;

  uint32_t dit_ms = 1200u / (uint32_t)wpm;
  uint32_t dit_us = dit_ms * 1000u;

  cw_timing_t t = {
    .dit_us = dit_us,
    .dah_us = 3u * dit_us,
    .intra_symbol_us = dit_us,
    .inter_char_us = 3u * dit_us,
    .inter_word_us = 7u * dit_us,
  };
  return t;
}

void cw_apply_farnsworth(cw_timing_t* t, uint16_t element_wpm, uint16_t farnsworth_wpm) {
  if (!t) return;

  if (element_wpm < 5) element_wpm = 5;
  if (element_wpm > 60) element_wpm = 60;

  if (farnsworth_wpm == 0) farnsworth_wpm = element_wpm;
  farnsworth_wpm = clamp_u16(farnsworth_wpm, 5, element_wpm);

  // Crude but effective: scale only spacing by ratio element/farnsworth.
  // When farnsworth_wpm < element_wpm => spacing gets longer.
  // Keep an upper bound to avoid absurd long waits.
  uint32_t ratio_x1000 = (uint32_t)element_wpm * 1000u / (uint32_t)farnsworth_wpm; // >= 1000
  ratio_x1000 = clamp_u32(ratio_x1000, 1000u, 5000u);

  t->inter_char_us = (t->inter_char_us * ratio_x1000) / 1000u;
  t->inter_word_us = (t->inter_word_us * ratio_x1000) / 1000u;
}

void cw_apply_weight(cw_timing_t* t, uint16_t weight_pct) {
  if (!t) return;

  // Nominal is 50%. Clamp to a conservative range.
  if (weight_pct == 0) weight_pct = 50;
  weight_pct = clamp_u16(weight_pct, 35, 65);

  // Scale key-down durations (dit/dah). Keep spacing as-is.
  t->dit_us = (t->dit_us * (uint32_t)weight_pct) / 50u;
  t->dah_us = (t->dah_us * (uint32_t)weight_pct) / 50u;
}

bool cw_is_word_gap(char c) {
  return (c == ' ' || c == '\t');
}

static const char* pattern_for_letter(char c) {
  switch (c) {
    case 'A': return ".-";
    case 'B': return "-...";
    case 'C': return "-.-.";
    case 'D': return "-..";
    case 'E': return ".";
    case 'F': return "..-.";
    case 'G': return "--.";
    case 'H': return "....";
    case 'I': return "..";
    case 'J': return ".---";
    case 'K': return "-.-";
    case 'L': return ".-..";
    case 'M': return "--";
    case 'N': return "-.";
    case 'O': return "---";
    case 'P': return ".--.";
    case 'Q': return "--.-";
    case 'R': return ".-.";
    case 'S': return "...";
    case 'T': return "-";
    case 'U': return "..-";
    case 'V': return "...-";
    case 'W': return ".--";
    case 'X': return "-..-";
    case 'Y': return "-.--";
    case 'Z': return "--..";

    case '0': return "-----";
    case '1': return ".----";
    case '2': return "..---";
    case '3': return "...--";
    case '4': return "....-";
    case '5': return ".....";
    case '6': return "-....";
    case '7': return "--...";
    case '8': return "---..";
    case '9': return "----.";

    case '/': return "-..-.";
    case '?': return "..--..";
    case '=': return "-...-";
    case '.': return ".-.-.-";
    case ',': return "--..--";
    default: return 0;
  }
}

const char* cw_morse_pattern(char c) {
  if (c >= 'a' && c <= 'z') c = (char)(c - 32);
  if (c >= 'A' && c <= 'Z') return pattern_for_letter(c);
  if (c >= '0' && c <= '9') return pattern_for_letter(c);
  return pattern_for_letter(c);
}
