# Troubleshooting

Diese Seite ist symptomorientiert: Suche dein Problem und arbeite die Checks von oben nach unten ab. Viele Symptome haben derzeit eine bekannte Ursache im Code; der Verweis in Klammern zeigt auf [07_known_gaps.md](07_known_gaps.md).

## Backend startet nicht oder WebUI zeigt keine Wirkung

Checks:
- `systemctl status sota-sdr-backend` und `journalctl -u sota-sdr-backend -n 100`
- `curl http://localhost:8000/health` und `curl http://localhost:8000/diag`
- HL2-IP in `.env` bzw. systemd-Unit (`SOTA_CW_HL2_IP`) stimmt mit dem echten HL2 überein.
- `ping <HL2-IP>` vom Pi aus.

Fix:
- IP korrigieren, `sudo systemctl restart sota-sdr-backend`, Logs erneut prüfen.

## HL2 reagiert nicht auf Frequenz oder PTT aus der WebUI

Bekannte Ursache: Die C&C-Frames werden ohne das vom Protokoll verlangte Framing gesendet (G1).

Checks:
- HL2 am PC mit Thetis/SparkSDR/Quisk testen. Funktioniert es dort, liegt es am Backend.
- Kein anderes SDR-Programm darf gleichzeitig mit dem HL2 verbunden sein; Protocol 1 bedient nur einen Host.

## Filter schalten nicht um, Relais klicken nicht beim Bandwechsel

Bekannte Ursache: Das Relaiswort geht an Adresse 0x08 statt an die Open-Collector-Bits in Adresse 0x00 (G2, G3). Bis zur Korrektur nicht senden.

## SWR-Anzeige steht immer auf 1,0, Leistung auf 0 W

Bekannte Ursache: Die Telemetrie des HL2 wird nicht ausgewertet, es gibt noch keinen SWR-Schutz (G4). SWR extern messen (z. B. NanoVNA, siehe [tx_quality_nanovna_h4.md](tx_quality_nanovna_h4.md)).

## Kein Ton auf dem Tablet

Checks:
- Browser hat Audiowiedergabe erlaubt (einmal auf „🔊 RX Audio“ tippen).

Bekannte Ursache: Das Backend speist noch kein Audio in `/ws/audio` ein (A1, A3).

## CW-Decoder zeigt nichts oder nur Zeichensalat

Bekannte Ursache: IQ-Format und Samplerate passen nicht zum HL2 bzw. zu `multimon-ng` (G5, A4).

## IO-Board / Pico-Keyer reagiert nicht

Bekannte Ursache: Backend und Firmware nutzen noch keinen I2C-Weg, den der HL2 unterstützt (G7, G8). Siehe [03_ioboard_register_protocol.md](03_ioboard_register_protocol.md).

Checks für die Hardware:
- Versorgung und Masse des IO-Boards.
- Mit der Original-IO-Board-Firmware und Thetis/Quisk am PC testen.

## PTT/KEY falsches Verhalten (invertiert, vertauscht, „hängt“)

Checks:
- CN4-Belegung: Tip = KEY, Ring = PTT, Sleeve = GND.
- Low-Side-Schalter: Ausgang zieht gegen GND, solange der Pico-GPIO High ist.
- Pico-GPIOs laut `firmware/pico_cw_keyer/src/outputs.c`: PTT = GPIO 2, KEY = GPIO 3.

Fix:
- Leitungen tauschen bzw. Schaltstufe korrigieren.

## FT8/FT4: Decodes fehlen oder DT ist groß

Checks:
- `chronyc tracking`: Abweichung deutlich unter 1 s?
- `chronyc sources -v`: Ist eine Quelle ausgewählt (`*`)? Wenn nur `GPS` mit `?`/`x` und kein `PPS`: beim GPS-Eintrag in `/etc/chrony/chrony.conf` `noselect` entfernen (B1).
- `cgps`: Hat der GPS-Empfänger einen Fix?

## WSJT-X oder fldigi startet nicht

Checks:
- `journalctl -u sota-wsjtx -n 50` bzw. `-u sota-fldigi`
- Beide Units nutzen `xvfb-run -n 99`. Bei Konflikten jedem Dienst eine eigene Display-Nummer geben.
- fldigi-Kommandozeile gegen `fldigi --help` prüfen (A6).
