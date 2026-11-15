# WebUI Benutzeranleitung (Android Tablet Remote Cockpit)

Diese Web-Applikation ist speziell für die ergonomische Touch-Bedienung auf einem **Android Tablet** im portablen SOTA- oder Stationsbetrieb optimiert. Sämtliche SDR-Prozesse laufen headless auf dem Raspberry Pi 4B.

---

## 1. Schnellzugriff & Übersicht

Öffne auf dem Android Tablet im Chrome- oder Firefox-Browser die URL:
```text
http://<IP-des-Raspberry-Pi>/
```
*(Empfehlung: Über das Browser-Menü **„Zum Startbildschirm hinzufügen“** wählen, um die App im vollen Vollbildmodus als PWA ohne störende URL-Leiste zu betreiben).*

---

## 2. Hauptanzeige & VFO-Leiste (Immer sichtbar)

- **Große Frequenzanzeige (VFO):** Zeigt die aktuelle Arbeitsfrequenz in Hertz an.
- **Schnellband-Tasten:** Direkter Wechsel auf 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m oder 10m.
  - Das N2ADR Filter Board schaltet dabei automatisch das passende Tiefpass- und Hochpassrelais.
  - Das HL2 IO-Board aktualisiert automatisch seine Band-Ausgänge.
- **Schrittweiten (-1k, -100, +100, +1k):** Schnelles Abstimmen mit großen Touch-Zielen.
- **FWD PWR & VSWR Meter:** 
  - Zeigt live die Vorwärtsleistung in Watt und das Stehwellenverhältnis (VSWR).
  - Farbcodierung: Grün ($\le 1.5$), Gelb ($1.6 - 2.5$), Rot ($> 2.5$).
  - *Schutzabschaltung:* Bei VSWR $> 3.0$ wird das Senden sofort unterbrochen.
- **TUNE ATU Button:** Startet den Abstimmzyklus eines externen Antennentuners (z. B. Icom AH-4) über das IO-Board.
- **PTT Button (RX/TX):** Manuelles Umschalten des Senders mit roter optischer Sende-Warnung.
- **RX Audio Stream:** 
  - Antippen von **„🔊 RX Audio“** startet die direkte, verzögerungsarme Audioausgabe über die internen Lautsprecher des Android Tablets via WebSocket.
  - Über den Schieberegler wird die Wiedergabelautstärke geregelt.
- **SOTA Kontrast-Modus:** 
  - Umschalter zwischen **Dunkel-Modus** und **Outdoor-Modus** (starker Schwarz-Weiß-Kontrast für den Einsatz bei grellem Sonnenlicht auf Berggipfeln).

---

## 3. Die Betriebsmodi im Detail

### Tab 1: CW Cockpit (Reiner Text-Morser)
- **CW Empfang (RX):** 
  - Automatische Dekodierung empfangener Morsesignale in Echtzeit.
  - Automatisches Scrollen im Terminalfenster.
- **CW Senden (TX via Pico Keyer):**
  - Text eingeben und mit **„Senden (TX)“** oder Enter abschicken.
  - Der Raspberry Pi Pico auf dem IO-Board sorgt für absolut mikrofeines, jitterfreies Timing.
  - **SOTA Schnell-Makros:** Ein-Klick-Tasten für `CQ SOTA`, `599 BK`, `TU 73`, `QRL?`, `AGN?`, `QRZ?`.
- **Keyer Parameter:**
  - Tempo (WPM): Schieberegler von 10 bis 40 WPM.
  - Farnsworth WPM & PTT Vor-/Nachlaufzeiten.
- **Automatischer QSO Bot:**
  - Ruft selbstständig CQ, erkennt Antwort-Rufzeichen, tauscht Rapport (599) aus und loggt das QSO.

---

### Tab 2: WSJT-X (FT8 / FT4 / WSPR / FST4)
- **Statusanzeige:** Grüner Punkt signalisiert aktive Verbindung zum WSJT-X Headless-Daemon auf dem Pi.
- **Live Bandaktivitäts-Tabelle:**
  - Zeigt alle empfangenen Signale der Periode mit UTC-Zeit, Signalstärke in dB (SNR), Zeitversatz (DT) und NF-Frequenz.
  - CQ-Rufe werden farblich hervorgehoben.
- **One-Touch QSO:**
  - Ein Klick auf **„Antworten“** bei einem Rufzeichen übernimmt die Station sofort in WSJT-X und initiiert die QSO-Sequenz.
- **CQ Rufen & HALT TX:** Sofortiger Start des eigenen CQ-Rufs oder Not-Abbruch des Senders.

---

### Tab 3: PSK31 / RTTY
- **Modem-Auswahl:** Schnelles Umschalten zwischen `BPSK-31`, `QPSK-31`, `RTTY` (45.45 Baud / 170 Hz Shift) und `CW` (fldigi DSP).
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
  - **SOTA CSV:** Speziell formatiert für den Direkt-Upload in die SOTA Database.
  - **ADIF (.adi):** Standardformat für jedes Logbuchprogramm (z. B. Log4OM, Cloudlog, QRZ.com).
