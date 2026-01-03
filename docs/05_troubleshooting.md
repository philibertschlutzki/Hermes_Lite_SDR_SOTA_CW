# Troubleshooting

Diese Seite ist symptomorientiert: Suche dein Problem und arbeite die Checks von oben nach unten ab.

## Symptom: IO-Board reagiert nicht
Checks:
- Zuerst Minimaltest: grundlegendes Read/Write über ein Testregister.
- Firmware-Status prüfen: Boot/Init, kein „Error“-Zustand.

Fix:
- Firmware korrekt flashen und erneut testen.
- Verkabelung (GND, Versorgung, Busleitungen) systematisch prüfen.

## Symptom: PTT/KEY falsches Verhalten (invertiert, vertauscht, „hängt“)
Checks:
- TRS-Verdrahtung Tip/Ring/Sleeve prüfen; PTT und KEY nicht vertauschen.
- Low-Side-Konzept beachten: Ausgang schaltet gegen GND.
- Für CW-Keying stabile Signalquelle nutzen (Keyer/Interface) und Timing/Jitter ausschließen.

Fix:
- Leitungstausch/Polung korrigieren.
- Falls vorhanden: „active low/high“-Optionen in Software/Backend prüfen.

## Symptom: WebUI/Backend keine Wirkung
Checks:
- Backend-Logs prüfen (Startfehler, Konfigfehler, Verbindungsfehler).
- HL2-IP/Port-Konfiguration prüfen.

Fix:
- Korrekte IP/Port setzen.
- Dienst neu starten und Logs erneut prüfen.
