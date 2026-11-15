#pragma once
#include <stdbool.h>

// Muster aus '.' und '-' für ein Zeichen (Groß-/Kleinschreibung egal).
// NULL für unbekannte Zeichen; diese werden übersprungen.
const char* cw_morse_pattern(char c);

bool cw_is_word_gap(char c);
