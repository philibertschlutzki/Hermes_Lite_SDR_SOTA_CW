# Antennen (SOTA CW)

Dieses Verzeichnis enthält **alle Unterlagen** rund um den schnellen, tunerlosen ("ohne ATU") Antennenaufbau für die Ziel‑Frequenzen 7,032 MHz und 14,062 MHz (jeweils ±5 kHz).

Empfohlenes Konzept: zwei getrennte, vorab getrimmte Monoband‑EFHW‑Drähte (40 m und 20 m), die am selben 49:1/50:1‑Feedpoint betrieben werden, sodass am Gipfel nur der Draht gewechselt wird.

## Ziel: "ohne ATU" am Gipfel

- Pro Band ein eigener Drahtsatz, jeweils auf Resonanz in der realen Aufbaugeometrie getrimmt.
- Gemeinsamer Feedpoint (49:1 / ~50:1) + definierter Rückleiter (Counterpoise) + In‑Line‑Choke zur Reproduzierbarkeit.

## Startwerte (zum Trimmen)

Als grober Startwert für die Halbwellen‑Drahtlänge kann genutzt werden:

- Näherung: L ≈ 143 / f(MHz)  (Meter)
- In der Praxis wird **länger** zugeschnitten und dann auf die Wunschfrequenz gekürzt.

Startlängen (vor dem Kürzen):

- 40 m @ 7,032 MHz: ca. 20,34 m (2034 cm)
- 20 m @ 14,062 MHz: ca. 10,17 m (1017 cm)

## Dateien in diesem Ordner

- `Einkaufsliste.md`: Stückliste für 2× Monoband‑EFHW (gemeinsamer Core + 2 Drahtsätze).
- `Messvorgaenge.md`: NanoVNA‑Messaufbau, Protokollvorlage, Trimmschritte.
- `Checklisten.md`: Pre‑Trip, Aufbau am Gipfel, Bandwechsel, Abbau.
