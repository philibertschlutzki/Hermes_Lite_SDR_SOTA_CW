# Bring-up Checklist

Ziel: HL2 + IO-Board stabil in Betrieb nehmen, bevor CW-Jobs und Web-UI getestet werden. [file:1]

## Schrittfolge

1. HL2 Grundinbetriebnahme (Netzwerk, IP, Software/SDR-Client): HL2 muss zuverlässig per Ethernet erreichbar sein. [file:1]
2. IO-Board Funktion prüfen: Read/Write des IO-Board Register-Interfaces verifizieren (z. B. Testregister setzen/lesen). [file:1]
3. Pico-Firmware flashen und Grundtest: OUT1/OUT2 manuell toggeln (Testmode) und Verdrahtung prüfen. [file:1]
4. CW-Job-Protokoll testen: Kurzer Text ("TEST") als Job, Status/Progress prüfen. [file:1]
5. Erst jetzt: Pi-Backend + WebUI installieren und End-to-End testen. [file:1]

## Akzeptanzkriterien

- IO-Board-Ausgänge schalten reproduzierbar. [file:1]
- CW-Job startet/stoppt deterministisch und bricht sauber ab. [file:1]
- Keine unerwarteten PTT-Events beim Boot. [file:1]
