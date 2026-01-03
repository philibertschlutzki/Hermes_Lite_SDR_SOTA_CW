# Einkaufsliste (2× Monoband‑EFHW)

Ziel: Ein gemeinsamer Feedpoint/Transformer + zwei getrennte, vorab getrimmte EFHW‑Drähte (40 m / 20 m), damit vor Ort nur der Draht gewechselt wird.

## Gemeinsames "Core"‑Paket (einmalig)

- 1× EFHW‑Feedpoint/Transformer (49:1 bzw. ~50:1), QRP/portable‑tauglich, mit mechanischer Zugentlastung.
- 1× 1:1 In‑Line RF‑Choke (Common‑Mode‑Choke) in der Speiseleitung.
- 1× Counterpoise‑Draht + Anschlussmöglichkeit am Feedpoint (Ringöse/Klemme).
- 1× Koaxkabel (kurz, leicht, outdoor‑tauglich) zwischen Choke und TRX.
- 1× Adapter für TRX‑Buchse ↔ Koax (z. B. SMA↔BNC je nach HL2‑Setup).

## Pro Band: eigener Drahtsatz (2 Sätze total)

### 40 m‑Drahtsatz

- 1× Antennendraht (Startlänge ~20,34 m; danach trimmen).
- 1× Wickelkarte/Winder (für schnellen Aufbau).
- 1× End‑Isolator/Ring fürs obere Drahtende.
- 1× Clip/Karabiner am Drahtende (schnelles Ein-/Aushängen).

### 20 m‑Drahtsatz

- 1× Antennendraht (Startlänge ~10,17 m; danach trimmen).
- 1× Wickelkarte/Winder.
- 1× End‑Isolator/Ring fürs obere Drahtende.
- 1× Clip/Karabiner am Drahtende.

## Baumwurf‑/Halyard‑Set (schnell, reproduzierbar)

- 1× Wurfleine + Wurfgewicht (Throw‑Bag).
- 1× Halyard‑Leine (robuster als Wurfleine) + kleiner Clip/Mini‑Karabiner.

## Optional (für Robustheit/Reproduzierbarkeit)

- Ersatz‑Draht (kurzes Stück) + 2–3 Quetschverbinder/Crimps.
- Schrumpfschlauch/Isolierband.
- 1× Mini‑Multitool/Seitenschneider.

---

# Einkaufsliste – HL2 SOTA CW (Stecker/Kabel/Peripherie)

> Ergänzung: komplette Interconnect-/Strom-/RF-Peripherie für das Repo-Setup „Hermes Lite 2 + Raspberry Pi + HL2 IO-Board“.

## Pflichtteile (Basis)

- [ ] Hermes Lite 2 (HL2)
- [ ] HL2 IO-Board + RP2040/Pico (je nach IO-Board)
- [ ] Raspberry Pi (Pi 4 oder Pi Zero 2 W)
- [ ] microSD (≥ 32 GB, A1/A2)
- [ ] Gehäuse / Montageplatte / Abstandshalter (M2.5/M3)

## Daten / Programmierung

- [ ] Ethernet Patchkabel RJ45 (0.3–1 m) **oder** WLAN-only
- [ ] Pi-Stromkabel (USB-C bei Pi4 / Micro-USB bei Zero/alt)
- [ ] USB-Kabel fürs Pico/RP2040 (Micro-USB oder USB-C je nach Board)
- [ ] (Optional) USB-TTL Adapter 3.3 V + Dupont-Leitungen

## RF / Antenne – Koax & Adapter (empfohlenes Basis-Kit)

### Koax

- [ ] 1× Haupt-Feedline 50 Ohm, 5–10 m (leicht: RG-316/RG-174; robuster: RG-58/RG-8X)
- [ ] 1–2× Koax-Pigtail 20–50 cm (Zugentlastung/„Opferkabel“)

### Stecker/Adapter (bitte HL2-Buchsentyp verifizieren – oft SMA)

- [ ] 2× passende Stecker für HL2-Port (z. B. SMA-System)
- [ ] 2× Adapter SMA↔BNC (für portables Zubehör)
- [ ] 1× Adapter auf PL (SMA/BNC↔PL-259/SO-239), falls benötigt
- [ ] 1× Inline-Kupplung (BNC-BNC oder SMA-SMA)
- [ ] 1× Satz Staubschutzkappen (SMA/BNC)

### Outdoor-Entlastung/Schutz

- [ ] Klettband/Zugentlastung für Koax am Gehäuse
- [ ] Schrumpfschlauch-Sortiment
- [ ] Selbstverschweißendes Band (Koax-Übergänge)

## CW-Bedienung

- [ ] Paddle (iambic) oder Straight Key
- [ ] Anschlusskabel + passender Stecker (z. B. 3.5 mm TRS / 6.35 mm TRS – abhängig vom IO-Board-Panel)
- [ ] (Optional) Fußtaster / Reserve-Stecker

## Stromversorgung (portable)

- [ ] Akku (LiFePO4 oder Powerbank – je nach Konzept)
- [ ] DC-DC Wandler: Akku → 5 V stabil für Raspberry Pi
- [ ] Sicherungshalter + Flachsicherungen (z. B. 2 A / 5 A)
- [ ] Strom-Stecksystem standardisieren (z. B. DC-Hohlstecker oder Anderson Powerpole)
- [ ] Silikonlitze rot/schwarz + Aderendhülsen + Kabelschuhe

## Antennen-„Baukasten“ (generisch)

- [ ] Antennendraht (20–30 m)
- [ ] Isolatoren (2–4 Stück)
- [ ] Abspannleine + Heringe
- [ ] Wurfleine + Wurfbeutel
- [ ] Leichter Mast 6–10 m
- [ ] (Optional) Unun/Balun/Matching-Unit (je nach Antennentyp)
- [ ] (Optional) kompakter Tuner
