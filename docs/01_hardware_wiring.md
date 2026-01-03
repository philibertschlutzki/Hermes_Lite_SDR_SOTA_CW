# Hardware & Verdrahtung

Ziel: Am Ende dieser Seite ist klar, welche Kabel wohin müssen, damit PTT/KEY (und optional weitere IOs) korrekt funktionieren.

## Voraussetzungen
- HL2 ist mechanisch fertig aufgebaut und kann mit Strom versorgt werden.
- Optional: IO-Board ist vorhanden und soll PTT/KEY/GPIO übernehmen.

## Prinzip: „Low-Side“ Ausgänge
Viele Ausgänge am IO-Board sind als Low-Side gedacht: Der Ausgang verbindet im aktiven Zustand den Anschluss mit GND.
Das passt gut zu PTT/KEY-Eingängen, die gegen Masse gezogen werden sollen.

## Verdrahtungs-Checkliste (kurz)
- GND ist gemeinsam (HL2, IO-Board, ggf. Key/Interface).
- PTT und KEY nicht vertauschen.
- Bei TRS-Klinke: Tip/Ring/Sleeve sauber zuordnen (Hersteller/Interface kann variieren).

## Empfohlene Dokumentation, die du parallel offen haben solltest
- HL2/Protocol Wiki (für Kontext, falls du tiefer debuggen musst): https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol

## Ergebnis: Woran erkenne ich „Verdrahtung ok“?
- PTT schaltet reproduzierbar in TX (ohne „Flattern“).
- KEY erzeugt saubere CW-Tastung (ohne Hänger).
- Nichts wird heiß, keine Brownouts/Resets.

## Nächster Schritt
Weiter mit: 02_bringup_checklist.md
