# Hardware & Verdrahtung

Ziel: Am Ende dieser Seite ist klar, welche Kabel wohin gehören, damit RX, TX, PTT und KEY funktionieren.

## Voraussetzungen

- HL2 ist fertig aufgebaut, N2ADR-Filterboard ist gesteckt.
- Raspberry Pi 4B mit Netzteil (stabile 5 V, ≥ 3 A).
- Optional: IO-Board mit Raspberry Pi Pico.

## Übersicht der Verbindungen

| Von | Nach | Kabel | Zweck |
|---|---|---|---|
| HL2 Ethernet | Pi 4B Ethernet | kurzes Cat-Kabel, direkt | openHPSDR Protocol 1 (UDP) |
| Pi 4B WLAN | Tablet | – | WebUI, API, Audio |
| Pi 4B USB | USB-GPS | – | Zeitquelle für FT8/FT4 |
| Pi 4B USB | Pico | USB-Micro | nur zum Flashen und für Debug-Ausgaben |
| Key/PTT-Quelle | HL2 CN4 (3,5 mm) | Klinke | **Tip = KEY, Ring = PTT, Sleeve = GND** |
| IO-Board | HL2 (intern) | Steckverbinder | I2C2 (Adresse 0x1D), Versorgung |

Laut [HL2-Protokoll-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol): Wird der **Ring** von CN4 auf Masse gezogen, meldet der HL2 PTT. Wird der **Tip** auf Masse gezogen, tastet der HL2 und erzeugt selbst ein geformtes CW-Signal.

## Pico-Keyer anschließen

Die Firmware in `firmware/pico_cw_keyer` setzt zwei GPIOs (änderbar in `src/outputs.c`):

| Signal | Pico-GPIO | Logik |
|---|---|---|
| PTT_OUT | GPIO 2 | High = senden |
| KEY_OUT | GPIO 3 | High = Taste gedrückt |

Die GPIOs dürfen **nicht direkt** an CN4. Zwischen Pico und CN4 gehört je ein Low-Side-Schalter (z. B. NPN-Transistor oder N-MOSFET, alternativ ein Optokoppler), der Tip bzw. Ring gegen GND zieht, solange der GPIO High ist.

> Hinweis: Die Firmware ist derzeit ein Skeleton mit Mock-Registern, die Steuerung vom Pi über I2C funktioniert noch nicht. Details in [07_known_gaps.md](07_known_gaps.md), G7–G9.

## Verdrahtungs-Checkliste

- [ ] Gemeinsame Masse zwischen HL2, Keyer-Schaltung und Pico.
- [ ] PTT (Ring) und KEY (Tip) nicht vertauscht. Mit Multimeter an der Klinke prüfen.
- [ ] Antenne bzw. Dummy-Load am HL2 angeschlossen, bevor irgendetwas sendet.
- [ ] Netzwerk: HL2 und Pi im selben Subnetz, feste IP für den HL2 notiert.

## Woran erkenne ich „Verdrahtung ok“?

- Ring gegen GND: Der HL2 meldet PTT (in Thetis/SparkSDR am PC oder später in der WebUI sichtbar).
- Tip gegen GND: Saubere CW-Tastung ohne Hänger, auf einem zweiten Empfänger hörbar.
- Nichts wird heiß, keine Resets beim Umschalten auf TX.

## Nächster Schritt

Weiter mit [02_bringup_checklist.md](02_bringup_checklist.md).
