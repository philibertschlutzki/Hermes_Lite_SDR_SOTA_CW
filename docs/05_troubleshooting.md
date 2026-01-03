# Troubleshooting

## IO-Board reagiert nicht

- Prüfen, ob IO-Board-Read/Write grundsätzlich funktioniert (Testregister). [file:1]
- Prüfen, ob die Firmware geflasht wurde und beim Boot nicht im Error-Status hängen bleibt. [file:1]

## PTT/KEY falsches Verhalten

- Verdrahtung TRS: Tip/Ring/Sleeve prüfen; KEY/PTT nicht vertauschen. [file:1]
- Sicherstellen, dass OUT1/OUT2 Low-Side genutzt wird (Kontakt nach Masse). [file:1]
- OUT8 nicht für CW-Keying verwenden. [file:1]

## WebUI/Backend keine Wirkung

- Backend-Logs prüfen (systemd/journalctl). [file:1]
- HL2-IP/Port Konfiguration prüfen (`SOTA_CW_HL2_IP`, `SOTA_CW_HL2_PORT`). [file:1]
