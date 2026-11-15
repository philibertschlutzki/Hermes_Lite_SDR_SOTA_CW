# Bring-up Checkliste (Inbetriebnahme)

Jeder Punkt soll eindeutig „OK“ oder „nicht OK“ sein. Erst weitermachen, wenn der vorherige Abschnitt OK ist.

> **Vor dem ersten Senden:** Filterumschaltung und SWR-Schutz sind im Backend noch nicht funktionsfähig ([07_known_gaps.md](07_known_gaps.md), G2–G4). Sende nur an einer Dummy-Load und mit geringer Leistung, bis diese Punkte behoben und getestet sind.

## 0) Vorbereitung

- [ ] HL2-IP, Pi-IP und Subnetzmaske notiert.
- [ ] Rufzeichen und SOTA-Referenz bereit (für QSO-Bot und Log).

## 1) HL2 allein am PC (Referenztest)

Damit ist klar, dass die Hardware funktioniert, bevor der Pi ins Spiel kommt.

- [ ] HL2 mit Thetis, SparkSDR oder Quisk am PC: RX funktioniert (Wasserfall, Audio).
- [ ] Kurzer TX-Test an Dummy-Load mit geringer Leistung.
- [ ] Filterboard schaltet beim Bandwechsel hörbar (Relais-Klicken).

## 2) Raspberry Pi einrichten

```bash
git clone https://github.com/philibertschlutzki/Hermes_Lite_SDR_SOTA_CW.git
cd Hermes_Lite_SDR_SOTA_CW
chmod +x deploy/*.sh
sudo ./deploy/install_full_stack.sh
```

Das Script kopiert den Code nach `/opt/sota-cw` und richtet Python-Umgebung, nginx, systemd-Dienste, PipeWire und Zeitsync ein.

- [ ] Script ohne Fehler durchgelaufen.
- [ ] HL2-IP in `pi/backend/.env` (`SOTA_CW_HL2_IP=…`) bzw. in der systemd-Unit gesetzt.
- [ ] `systemctl status sota-sdr-backend` zeigt `active (running)`.

## 3) Netzwerk und Backend

- [ ] `ping <HL2-IP>` vom Pi ohne Verluste.
- [ ] `curl http://localhost:8000/health` liefert eine Antwort.
- [ ] `curl http://localhost:8000/diag` zeigt die erwartete Konfiguration.
- [ ] Vom Tablet: `http://<Pi-IP>/` öffnet die WebUI.

## 4) Zeitsynchronisation (für FT8/FT4)

- [ ] USB-GPS steckt, `cgps` zeigt einen Fix.
- [ ] `chronyc sources -v` zeigt eine ausgewählte Quelle (`*`).
  Hat der GPS-Stick kein PPS, muss beim GPS-Eintrag in `/etc/chrony/chrony.conf` `noselect` entfernt werden (siehe [07_known_gaps.md](07_known_gaps.md), B1).
- [ ] Abweichung zu UTC deutlich unter 1 s (`chronyc tracking`).

## 5) IO-Board (wenn genutzt)

- [ ] Firmware geflasht.
- [ ] Minimaler Lese-/Schreibtest eines Registers funktioniert.

Hinweis: Das IO-Board wird über I2C2 des HL2 (Adresse 0x1D) mit 8-bit-Registern angesprochen. Der aktuelle Backend-Code und die Pico-Firmware passen dazu noch nicht ([03_ioboard_register_protocol.md](03_ioboard_register_protocol.md)).

## 6) PTT/KEY-Funktionstest

- [ ] PTT: TX geht sicher an und wieder aus.
- [ ] KEY: CW-Tastung zuverlässig, kein Hängenbleiben.
- [ ] Wirkt etwas invertiert: Low-Side-Schalter und „High = aktiv“ der Pico-GPIOs prüfen.

## 7) Digitalmodi

- [ ] `systemctl status sota-wsjtx sota-fldigi` zeigt beide Dienste aktiv.
- [ ] WebUI-Tab WSJT-X zeigt Verbindung (grüner Punkt).

Hinweis: Empfangs- und Sendeaudio zwischen HL2 und WSJT-X/fldigi ist noch nicht implementiert ([07_known_gaps.md](07_known_gaps.md), A1–A2).

## Nächster Schritt

- Läuft alles: [04_webui_user_guide.md](04_webui_user_guide.md)
- Hakt etwas: [05_troubleshooting.md](05_troubleshooting.md)
