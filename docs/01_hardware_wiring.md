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
| IO-Board J6 Pin 7 / Pin 8 | HL2 CN4 Tip / Ring (bzw. DB1 Pin 12 / 10) | kurze Litze im Gehäuse | **KEY / PTT vom Pico**, Masse gemeinsam |
| IO-Board | HL2 (intern) | Steckverbinder | I2C2 (Adresse 0x1D), Versorgung |

Laut [HL2-Protokoll-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol): Wird der **Ring** von CN4 auf Masse gezogen, meldet der HL2 PTT. Wird der **Tip** auf Masse gezogen, tastet der HL2 und erzeugt selbst ein geformtes CW-Signal.

## Pico-Keyer anschließen

Zwischen Pi und HL2 gibt es **nur das Netzwerkkabel**. Der Pi schickt den CW-Text über das HL2-Protokoll an den HL2, der ihn per I2C2 an den Pico auf dem IO-Board weitergibt. Der Pico tastet den HL2 über dessen eigenen Key-Eingang.

Die Firmware `firmware/pico_cw_keyer` schaltet dafür zwei der Low-Side-Schalter auf **J6** (TBD62381, ziehen nach GND, solange der GPIO High ist):

| Signal | Pico-GPIO | IO-Board | Ziel am HL2 |
|---|---|---|---|
| KEY | GPIO 9 (Out7) | J6 Pin 7 | CN4 **Tip** (DB1 Pin 12 „CW/PTT Tip“) |
| PTT | GPIO 8 (Out8) | J6 Pin 8 | CN4 **Ring** (DB1 Pin 10 „CW/PTT Ring“) |

Andere Ausgänge per CMake: `cmake -DKEY_GPIO=22 -DPTT_GPIO=8 ..`.

So wird verdrahtet:
1. Zwei kurze Litzen von J6 Pin 7 und Pin 8 zu Tip und Ring von CN4 (an den Lötpunkten der Buchse oder an DB1 Pin 12/10). Masse ist über den IO-Board-Steckverbinder schon gemeinsam.
2. Eine Handtaste an CN4 kann parallel bleiben; beide ziehen nur nach GND.
3. J4 Pin 7/8 (5-V-CMOS-Ausgänge derselben GPIOs) **nicht** zusätzlich belegen.

> Prüfen am Gerät: Die DB1-Belegung stammt aus dem HL2-Wiki (Seite „IO“). Vor dem Löten mit dem Multimeter Durchgang zwischen DB1 Pin 12 und dem CN4-Tip messen.

Firmware flashen: Pico mit gedrückter BOOTSEL-Taste per USB an einen Rechner, `pico_cw_keyer.uf2` auf das Laufwerk kopieren. Das USB-Kabel wird danach wieder abgezogen; im Betrieb braucht der Pico keine USB-Verbindung.

## Verdrahtungs-Checkliste

- [ ] J6 Pin 7 → CN4 Tip (KEY), J6 Pin 8 → CN4 Ring (PTT).
- [ ] PTT (Ring) und KEY (Tip) nicht vertauscht. Mit Multimeter an der Klinke prüfen.
- [ ] Antenne bzw. Dummy-Load am HL2 angeschlossen, bevor irgendetwas sendet.
- [ ] Netzwerk: HL2 und Pi im selben Subnetz, feste IP für den HL2 notiert.

## Woran erkenne ich „Verdrahtung ok“?

- Ring gegen GND: Der HL2 meldet PTT (in Thetis/SparkSDR am PC oder später in der WebUI sichtbar).
- Tip gegen GND: Saubere CW-Tastung ohne Hänger, auf einem zweiten Empfänger hörbar.
- Nichts wird heiß, keine Resets beim Umschalten auf TX.

## Nächster Schritt

Weiter mit [02_bringup_checklist.md](02_bringup_checklist.md).
