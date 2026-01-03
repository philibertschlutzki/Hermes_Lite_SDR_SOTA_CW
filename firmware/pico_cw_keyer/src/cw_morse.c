#include "cw_morse.h"

// PARIS standard: dit length = 1200 / WPM ms
cw_timing_t cw_timing_from_wpm(uint16_t wpm) {
  if (wpm < 5) wpm = 5;
  if (wpm > 60) wpm = 60;

  uint32_t dit = 1200u / (uint32_t)wpm;
  cw_timing_t t = {
    .dit_ms = dit,
    .dah_ms = 3u * dit,
    .intra_symbol_ms = dit,
    .inter_char_ms = 3u * dit,
    .inter_word_ms = 7u * dit,
  };
  return t;
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
