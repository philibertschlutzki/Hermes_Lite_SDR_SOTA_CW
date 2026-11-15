# WebUI Benutzeranleitung (Android Tablet Remote Cockpit)

Diese Web-Applikation ist speziell für die ergonomische Touch-Bedienung auf einem **Android Tablet** im portablen SOTA- oder Stationsbetrieb optimiert. Sämtliche SDR-Prozesse laufen headless auf dem Raspberry Pi 4B.

> **Stand der Funktionen:** Die Oberfläche ist vollständig, einige Anzeigen und Aktionen haben im Backend aber noch keine Wirkung. Sie sind unten mit ⚠️ markiert. Details: [07_known_gaps.md](07_known_gaps.md).

---

## 1. Schnellzugriff & Übersicht

Öffne auf dem Android Tablet im Chrome- oder Firefox-Browser die URL:
```text
http://<IP-des-Raspberry-Pi>/
```
*(Tipp: Über das Browser-Menü **„Zum Startbildschirm hinzufügen“** eine Verknüpfung anlegen. Ein Web-App-Manifest fehlt noch, deshalb öffnet sie als normaler Browser-Tab, nicht als Vollbild-PWA.)*

---

## 2. Hauptanzeige & VFO-Leiste (Immer sichtbar)

- **Große Frequenzanzeige (VFO):** Zeigt die aktuelle Arbeitsfrequenz in Hertz an.
- **Schnellband-Tasten:** Direkter Wechsel auf 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m oder 10m.
  - Ziel: Das N2ADR-Filterboard schaltet das passende Tief- und Hochpassrelais, das IO-Board seine Bandausgänge.
  - ⚠️ Derzeit wird das Relaiswort an die falsche C&C-Adresse geschickt; die Filter schalten nicht um (G2). Bis zur Korrektur nicht senden.
- **Schrittweiten (-1k, -100, +100, +1k):** Schnelles Abstimmen mit großen Touch-Zielen.
- **FWD PWR & VSWR Meter:** 
  - Zeigt Vorwärtsleistung in Watt und Stehwellenverhältnis (VSWR).
  - Farbcodierung: Grün (≤ 1,5), Gelb (bis 2,5), Rot (> 2,5).
  - ⚠️ Die HL2-Telemetrie wird noch nicht ausgewertet; die Anzeige steht fest auf SWR 1,0 und 0 W. Eine automatische Abschaltung bei VSWR > 3,0 ist geplant, aber nicht umgesetzt (G4).
- **TUNE ATU Button:** Startet den Abstimmzyklus eines externen Antennentuners (z. B. Icom AH-4) über das IO-Board. ⚠️ Hängt von der IO-Board-Anbindung ab (G7, G12).
- **PTT Button (RX/TX):** Manuelles Umschalten des Senders mit roter optischer Sende-Warnung.
- **RX Audio Stream:** 
  - Antippen von **„🔊 RX Audio“** startet die Audioausgabe auf dem Tablet über WebSocket (16-bit-PCM).
  - Über den Schieberegler wird die Wiedergabelautstärke geregelt.
  - ⚠️ Das Backend speist noch kein Audio in den Stream ein; es bleibt still (A1, A3).
- **SOTA Kontrast-Modus:** 
  - Umschalter zwischen **Dunkel-Modus** und **Outdoor-Modus** (starker Schwarz-Weiß-Kontrast für den Einsatz bei grellem Sonnenlicht auf Berggipfeln).

---

## 3. Die Betriebsmodi im Detail

### Tab 1: CW Cockpit (Reiner Text-Morser)
- **CW Empfang (RX):** 
  - Automatische Dekodierung empfangener Morsesignale mit `multimon-ng`.
  - ⚠️ IQ-Format und Samplerate passen noch nicht zum HL2; der Decoder liefert derzeit keinen sinnvollen Text (G5, A4).
  - Automatisches Scrollen im Terminalfenster.
- **CW Senden (TX via Pico Keyer):**
  - Text eingeben und mit **„Senden (TX)“** oder Enter abschicken.
  - Ziel: Der Pico erzeugt das Morse-Timing in Hardware, unabhängig von Linux-Latenzen.
  - ⚠️ Die Übertragung des Textes vom Pi zum Pico funktioniert noch nicht (G7, G8).
  - **SOTA Schnell-Makros:** Ein-Klick-Tasten für `CQ SOTA`, `599 BK`, `TU 73`, `QRL?`, `AGN?`, `QRZ?`.
- **Keyer Parameter:**
  - Tempo (WPM): Schieberegler von 10 bis 40 WPM.
  - Farnsworth WPM & PTT Vor-/Nachlaufzeiten.
- **Automatischer QSO Bot:**
  - Ruft selbstständig CQ, erkennt Antwort-Rufzeichen, tauscht Rapport (599) aus und loggt das QSO.

---

### Tab 2: WSJT-X (FT8 / FT4 / WSPR / FST4)
- **Statusanzeige:** Grüner Punkt signalisiert aktive UDP-Verbindung zu WSJT-X auf dem Pi (läuft unter Xvfb).
- ⚠️ Empfangs- und Sendeaudio zwischen HL2 und WSJT-X fehlen noch; Decodes kommen erst, wenn WSJT-X Audio bekommt (A1, A2).
- **Live Bandaktivitäts-Tabelle:**
  - Zeigt alle empfangenen Signale der Periode mit UTC-Zeit, Signalstärke in dB (SNR), Zeitversatz (DT) und NF-Frequenz.
  - CQ-Rufe werden farblich hervorgehoben.
- **One-Touch QSO:**
  - Ein Klick auf **„Antworten“** bei einem Rufzeichen übernimmt die Station sofort in WSJT-X und initiiert die QSO-Sequenz.
- **CQ Rufen & HALT TX:** Sofortiger Start des eigenen CQ-Rufs oder Not-Abbruch des Senders.

---

### Tab 3: PSK31 / RTTY
- **Modem-Auswahl:** Umschalten zwischen `BPSK-31`, `QPSK-31`, `RTTY` (45,45 Baud / 170 Hz Shift) und `CW` (fldigi DSP).
- ⚠️ Wie bei WSJT-X fehlt der Audiopfad zum HL2 (A1, A2).
- **Text-Terminal:** Kontinuierlicher Zeichenstrom beim Empfang.
- **Sende-Puffer:** Text vorab eintippen und mit einem Klick aussenden.
- **Digitale Makros:** Vordefinierte Texte für Rapport- und Abschluss-Meldungen.

---

### Tab 4: N2ADR & Hardware Telemetrie
- Zeigt die Relaiszustände des N2ADR Filter Boards (aktiver LPF und schaltbarer 3-MHz-Hochpassfilter).
- Zeigt den Zustand des IO-Boards (Pico), der I2C-Register und des Antennentuners.

---

### Tab 5: SOTA Log & Export
- Listet alle protokollierten QSOs auf.
- Direkte Download-Buttons für:
  - **SOTA CSV:** Für den Upload in die SOTA-Datenbank (Format vor dem ersten Upload mit einem Test-Log prüfen).
  - **ADIF (.adi):** Standardformat für jedes Logbuchprogramm (z. B. Log4OM, Cloudlog, QRZ.com).
