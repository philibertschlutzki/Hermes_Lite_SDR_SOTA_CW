# Hardware-Verdrahtung (HL2 + IO-Board)

## Annahmen

- HL2 nutzt eine 3,5mm TRS-Buchse für CW/Key/PTT; im Kontext dieses Projekts wird angenommen: **Tip = KEY**, **Ring = PTT**, **Sleeve = GND**. [file:1]
- Das HL2 IO-Board stellt Low-Side-Switch-Ausgänge bereit ("Kontakt nach Masse"). [file:1]

## Empfehlung (minimaler Start)

- IO-Board Low-Side OUT1 → PTT (Ring). [file:1]
- IO-Board Low-Side OUT2 → KEY (Tip). [file:1]
- IO-Board GND → Sleeve (GND). [file:1]

## Hinweise

- OUT8 sollte **nicht** für CW-Keying verwendet werden (typisch RC-gefiltert / PWM-Use-Case); OUT1..OUT7 sind für schnelle Schaltvorgänge geeigneter. [file:1]

## Verdrahtungstabelle

| Signal | HL2 TRS | IO-Board | Bemerkung |
|---|---|---|---|
| KEY | Tip | OUT2 (Low-Side) | Schaltet gegen GND. |
| PTT | Ring | OUT1 (Low-Side) | PTT Vor-/Nachlauf per Firmware/Job. |
| GND | Sleeve | GND | Gemeinsame Masse. |

## Vor dem ersten Einschalten

- Durchgang/Isolationsprüfung: KEY/PTT dürfen im Ruhezustand **nicht** gegen GND kurzgeschlossen sein (nur wenn Ausgang aktiv). [file:1]
- Erst danach HL2/IO-Board zusammenstecken und einschalten. [file:1]
