#include "cw_morse.h"

#include <stddef.h>

bool cw_is_word_gap(char c) { return c == ' ' || c == '\t'; }

const char* cw_morse_pattern(char c) {
  if (c >= 'a' && c <= 'z') c = (char)(c - 32);
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
    case '=': return "-...-";    // BT
    case '.': return ".-.-.-";
    case ',': return "--..--";
    case '+': return ".-.-.";    // AR
    case '-': return "-....-";
    case ':': return "---...";
    case '\'': return ".----.";
    case '(': return "-.--.";    // KN
    case ')': return "-.--.-";
    case '"': return ".-..-.";
    case '@': return ".--.-.";
    case '!': return "-.-.--";
    case '&': return ".-...";    // AS
    default: return NULL;
  }
}
