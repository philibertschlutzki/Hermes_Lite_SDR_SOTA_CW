# Messvorgänge (NanoVNA) & Trimmen

Ziel: Die 40 m‑ und 20 m‑EFHW‑Drähte so trimmen, dass die Resonanz (SWR‑Minimum bzw. |S11|‑Minimum) nahe an den Ziel‑Frequenzen liegt:

- 7,032 MHz (±5 kHz)
- 14,062 MHz (±5 kHz)

## Messaufbau (wichtig: wie im späteren Einsatz)

1. Antenne **realistisch aufhängen** (Höhe/Neigung/Endhöhe ähnlich wie SOTA‑Aufbau).
2. Feedpoint/Transformer anschließen.
3. In‑Line 1:1‑Choke in die Speiseleitung (Position dokumentieren und später beibehalten).
4. Counterpoise anschließen (Länge/Anordnung dokumentieren und später beibehalten).
5. NanoVNA an den Koax‑Eingang (bzw. dort, wo später der TRX sitzt).

## Sweep‑Einstellungen (Empfehlung)

- 40 m: Sweep z. B. 6,8–7,3 MHz
- 20 m: Sweep z. B. 13,8–14,4 MHz

Hinweis: Kalibrierung (SOL) möglichst am Messpunkt (Koax‑Ende) durchführen.

## Trim‑Vorgehen (kürzen bis Resonanz passt)

1. Startlänge bewusst **zu lang** wählen.
2. Sweep aufnehmen, Resonanzfrequenz notieren.
3. Ist die Resonanz **zu tief** (unter Soll), Draht schrittweise kürzen.
4. In kleinen Schritten kürzen (typisch 1–2 cm), dann erneut messen.
5. Nach Erreichen der Zielmitte (7,032 / 14,062) eine Messreihe ±100 kHz dokumentieren.

## Protokollvorlage (zum Kopieren)

- Datum/Ort:
- Band (40 m / 20 m):
- Drahtlänge (cm):
- Aufbau: (sloper/inverted‑L, Höhe, Endhöhe, Winkel):
- Counterpoise: (Länge, Verlegung):
- Choke‑Position: (Abstand vom Feedpoint):
- Sweepbereich:
- Resonanz (MHz):
- SWR min:
- Notizen (Boden, Nähe Metall, Baumart, Feuchte):
