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
| IO-Board ACC-Anschluss (D-Sub) | HL2 Key-Buchse CN4 (3,5 mm) | Keying-Kabel: D-Sub-Stecker ↔ 3,5-mm-Klinkenstecker (3-polig) | **Out7 (KEY) → Tip, Out8 (PTT) → Ring, GND → Sleeve** |
| IO-Board | HL2 (intern) | Steckverbinder | I2C2 (Adresse 0x1D), Versorgung |

Laut [HL2-Protokoll-Wiki](https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol): Wird der **Ring** von CN4 auf Masse gezogen, meldet der HL2 PTT. Wird der **Tip** auf Masse gezogen, tastet der HL2 und erzeugt selbst ein geformtes CW-Signal.

## Pico-Keyer anschließen (Keying-Kabel)

Zwischen Pi und HL2 gibt es **nur das Netzwerkkabel**. Der Pi schickt den CW-Text über das HL2-Protokoll an den HL2, der ihn per I2C2 an den Pico auf dem IO-Board weitergibt. Der Pico tastet den HL2 über dessen eigene Key-Buchse. Dafür wird **nichts gelötet und nichts im Gehäuse verändert**: Ein kurzes externes Kabel verbindet den ACC-Anschluss des IO-Boards mit der Key-Buchse CN4 des HL2.

Die Firmware `firmware/pico_cw_keyer` schaltet zwei der Low-Side-Schalter des IO-Boards (TBD62381, ziehen nach GND, solange der GPIO High ist). Diese liegen am ACC-Anschluss (D-Sub):

| Signal | Pico-GPIO | IO-Board-Ausgang | Keying-Kabel: 3,5-mm-Klinke | Wirkung am HL2 |
|---|---|---|---|---|
| KEY | GPIO 9 | Out7 (J6 Pin 7) | **Tip** | Tip nach GND = CW-Tastung mit HL2-eigener Flankenformung |
| PTT | GPIO 8 | Out8 (J6 Pin 8) | **Ring** | Ring nach GND = PTT |
| GND | – | Masse des ACC-Anschlusses | **Sleeve** | gemeinsame Masse |

Andere Ausgänge per CMake: `cmake -DKEY_GPIO=22 -DPTT_GPIO=8 ..` (dann das Kabel entsprechend belegen).

### Kabel bauen

Material:
- 3,5-mm-Klinkenstecker, **3-polig (Stereo/TRS)**, für die Key-Buchse CN4 des HL2
- D-Sub-Stecker passend zum ACC-Anschluss des IO-Boards (Polzahl und Geschlecht an der eigenen Buchse prüfen), mit Gehäuse und Zugentlastung
- 3-adriges, möglichst geschirmtes Kabel, so kurz wie möglich (ca. 20–30 cm)

Belegung:
1. Ader 1: D-Sub-Pin von **Out7** → Klinke **Tip**
2. Ader 2: D-Sub-Pin von **Out8** → Klinke **Ring**
3. Ader 3 (bzw. Schirm): D-Sub-Pin **GND** → Klinke **Sleeve**

> **Vor dem Bauen messen:** Die D-Sub-Pinnummern für Out7, Out8 und GND sind hier bewusst nicht festgelegt. Sie hängen von der Belegung des ACC-Anschlusses ab (Schaltplan `KiCad/HL2IOBoard.pdf` im [HL2IOBoard-Repo](https://github.com/jimahlstrom/HL2IOBoard) bzw. Beschriftung am Gehäuse) und sind nicht nachgemessen. Die Angaben zu CN4/DB1 (DB1 Pin 12 „CW/PTT Tip“, Pin 10 „CW/PTT Ring“) stammen aus dem HL2-Wiki (Seite „IO“) und sind ebenfalls ungeprüft. Darum vor dem Löten des Kabels mit dem Multimeter prüfen:
> - Pico-GPIO 9 High (z. B. `POST /cw/tune` mit `{"enable": true}`, ohne Antenne an Dummy-Load): welcher D-Sub-Pin wird gegen GND niederohmig? → Out7.
> - Gleiches für Out8 (PTT, wird beim Tune ebenfalls gesetzt): den zweiten niederohmigen Pin zuordnen.
> - Durchgang D-Sub-GND ↔ HL2-Masse.

Hinweise:
- Eine Handtaste kann über ein Y-Kabel (Stereo-Verteiler) parallel an CN4 bleiben; beide ziehen nur nach GND.
- Keinen Mono-Klinkenstecker verwenden: Er verbindet Ring mit Sleeve und hält dann dauerhaft PTT.
- Die 5-V-CMOS-Ausgänge derselben GPIOs (J4 Pin 7/8) nicht zusätzlich belegen.

Firmware flashen: Pico mit gedrückter BOOTSEL-Taste per USB an einen Rechner, `pico_cw_keyer.uf2` auf das Laufwerk kopieren. Das USB-Kabel wird danach wieder abgezogen; im Betrieb braucht der Pico keine USB-Verbindung.

## Verdrahtungs-Checkliste

- [ ] Keying-Kabel gemessen: Out7 → Tip (KEY), Out8 → Ring (PTT), GND → Sleeve.
- [ ] 3-poliger (Stereo-)Klinkenstecker, kein Mono-Stecker.
- [ ] PTT (Ring) und KEY (Tip) nicht vertauscht. Mit Multimeter an der Klinke prüfen.
- [ ] Antenne bzw. Dummy-Load am HL2 angeschlossen, bevor irgendetwas sendet.
- [ ] Netzwerk: HL2 und Pi im selben Subnetz, feste IP für den HL2 notiert.

## Woran erkenne ich „Verdrahtung ok“?

- Ring gegen GND: Der HL2 meldet PTT (in Thetis/SparkSDR am PC oder später in der WebUI sichtbar).
- Tip gegen GND: Saubere CW-Tastung ohne Hänger, auf einem zweiten Empfänger hörbar.
- Nichts wird heiß, keine Resets beim Umschalten auf TX.

## Nächster Schritt

Weiter mit [02_bringup_checklist.md](02_bringup_checklist.md).
