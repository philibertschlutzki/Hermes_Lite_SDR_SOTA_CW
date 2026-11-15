# Einkaufsliste & Stückliste (BOM): Hermes-Lite 2 SOTA CW / FT8 Setup

* **Projektbasis:** `Hermes_Lite_SDR_SOTA_CW` (HL2 + N2ADR Filter Board + HL2 IO Board / Pi Pico + Raspberry Pi 4B)
* **Bezugsquelle:** AliExpress (inkl. Suchbegriffen für direkte Bestellung; bei Versand in die Schweiz erhebt AliExpress direkt im Checkout $8.1\%$ MWST ohne zusätzliche Post-Vorweisungstaxen)
* **Legende:** `[SET]` kennzeichnet empfohlene **Komplettsets**, die Einzelbestellungen ersetzen, Kosten sparen und Passform-Probleme vermeiden.

---

## 1. Kernkomponenten: SDR, Filter & Compute

*(Positionen überspringen, sofern bereits im Bestand)*

| Status | Pos | Komponente / Komplettset | Technische Spezifikation | AliExpress Search Keywords | Menge | Richtpreis (CHF) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| - [ ] | 1.1 | **`[SET]` Hermes-Lite 2 Komplett-Kit** | HL2 v9 Full Build inkl. Alugehäuse, 5W PA ($11\text{--}16\text{ V}$ DC) & eingebautem **N2ADR Filter Board** | `Hermes Lite 2 SDR transceiver assembled N2ADR` *(alternativ Makerfabs)* | 1 | 355.00 |
| - [ ] | 1.2 | **HL2 IO Board** *(falls nicht im Set)* | Interface-PCB für Band-Steuerung & Keyer-Routing | `Hermes Lite 2 IO board` | 1 | 25.00 |
| - [ ] | 1.3 | **Raspberry Pi Pico** | RP2040 Microcontroller (für Firmware `pico_cw_keyer`) | `Raspberry Pi Pico RP2040 board` | 1 | 5.50 |
| - [ ] | 1.4 | **`[SET]` Raspberry Pi 4B SOTA-Bundle** | RPi 4B (4GB/8GB) + **passives Alu-Kühlgehäuse** (lüfterlos, kein QRM!) + 64GB A2 microSD | `Raspberry Pi 4 Model B 8GB passive aluminum case kit` | 1 | 92.00 |

---

## 2. Stromversorgung: 18650 4S2P Power Pack ($11\text{--}16\text{ V}$, max. $100 \times 220 \times 40\text{ mm}$)

### Geometrie- & Spannungs-Auslegung
* **Bauform (4S2P flach, 1 Lage):**
  * $8 \times 18650$ Zellen ($\varnothing 18.5 \times 65.2\text{ mm}$) in $4 \times 2$ Matrix inkl. Zellhalter: **$78\text{ mm (B)} \times 136\text{ mm (L)} \times 22\text{ mm (H)}$**.
  * Restbauraum für BMS, DC-DC-Wandler, Sicherung & Buchsen: **$84\text{ mm}$** $\rightarrow$ Gesamtmaße ca. **$82 \times 195 \times 28\text{ mm}$** (strikt innerhalb **$100 \times 220 \times 40\text{ mm}$**).
  * Energieinhalt (bei $3500\text{ mAh}$ Zellen): **$7.0\text{ Ah}$ bei $14.8\text{ V} = 103.6\text{ Wh}$** ($\approx 7\text{--}9\text{ h}$ SOTA-Betrieb).
* **Überspannungsschutz für den HL2:**
  * Voll geladene 4S Li-Ion-Zellen erreichen **$16.8\text{ V}$** ($4 \times 4.2\text{ V}$), der HL2 ist auf **$11\text{--}16\text{ V}$ DC** spezifiziert.
  * Der **DC-DC Buck-Boost Wandler (fest auf $13.8\text{ V}$ eingestellt)** regelt den gesamten Entladebereich ($11.2\text{--}16.8\text{ V}$) konstant auf **$13.8\text{ V}$ DC**.

### Einkaufsliste – Power Pack & Lade-Equipment

| Status | Pos | Komponente / Komplettset | Technische Spezifikation | AliExpress Search Keywords | Menge | Richtpreis (CHF) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| - [ ] | 2.1 | **`[SET]` 18650 4S DIY Akku-Bau-Set** | 4S $20\text{A}/30\text{A}$ BMS mit Balancer ($56 \times 45 \times 4\text{ mm}$) + $2\times 4$ Zellhalter + Reinnickelband ($0.15 \times 8\text{ mm}$) + Isolierringe + Kapton-Tape | `4S 20A 18650 battery pack DIY kit BMS nickel strip holder` | 1 | 9.50 |
| - [ ] | 2.2 | **`[SET]` Mini-Punktschweißgerät (Spot Welder)** | Tragbares Akku-Punktschweißgerät inkl. Schweißstiften & Nickelband *(empfohlen, falls kein Schweißgerät vorhanden – schont 18650-Zellen vor Löthitze)* | `portable mini spot welder 18650 battery kit` | 1 | 18.00 |
| - [ ] | 2.3 | **DC-DC Buck-Boost Wandler ($13.8\text{ V}$)** | Auto Step-Up/Down Modul (IN: $9\text{--}36\text{ V}$, OUT: einstellbar auf **$13.8\text{ V}$**, $\ge 5\text{ A} / 80\text{ W}$, Bauhöhe $< 20\text{ mm}$) | `DC DC auto buck boost converter 12V to 13.8V 5A 80W` | 1 | 7.50 |
| - [ ] | 2.4 | **DC-DC Buck $5\text{ V} / 3\text{ A}$ USB-C** | Step-Down Modul IN: $9\text{--}24\text{ V}$ auf **$5\text{ V} / 3\text{ A}$** mit USB-C Kabel (für Raspberry Pi 4B) | `12V 24V to 5V 3A USB-C step down buck converter` | 1 | 3.00 |
| - [ ] | 2.5 | **Flachsicherungshalter + Wippschalter + Voltmeter** | Inline-Sicherungshalter (16 AWG) inkl. $5\text{ A}$ Sicherungen + Mini-Wippschalter ($10\text{ A}$) + ultraflache 4S LED-Spannungsanzeige | `inline blade fuse holder 5A mini rocker switch 4S indicator` | 1 | 5.50 |
| - [ ] | 2.6 | **`[SET]` Schrumpfschlauch-Sortiment** | $140\text{ mm}$ PVC-Akku-Schrumpfschlauch (für flachen 4S2P-Block) + Polyolefin-Sortiment für Leitungen | `140mm PVC heat shrink tubing battery pack assortment kit` | 1 | 5.00 |
| - [ ] | 2.7 | **Flachgehäuse (optional)** | ABS-Gehäuse max. **$100 \times 200 \times 35\text{ mm}$** (falls Hartschale statt Schrumpfschlauch gewünscht) | `ABS plastic project box enclosure 200x100x35mm` | 1 | 6.50 |
| - [ ] | 2.8 | **4S Li-Ion Ladegerät (EU)** | **$16.8\text{ V} / 2\text{ A}$** CC/CV Li-Ion Charger mit DC $5.5 \times 2.1\text{ mm}$ Stecker (CH-kompatibler Eurostecker Typ C) | `16.8V 2A lithium battery charger 4S 5.5x2.1mm EU plug` | 1 | 8.50 |
| - [ ] | 2.9 | **$8\times$ 18650 Markenzellen** | **$3500\text{ mAh}$** (Samsung INR18650-35E oder LG MJ1) – *Hinweis: Für maximale Sicherheit & echte Kapazität Bezug über CH-Fachhandel (z. B. Akkushop.ch / NKON) empfohlen* | `INR18650-35E 3500mAh Li-ion cell` | 8 | ~44.00 |

---

## 3. Tunerlose Resonanz-Antenne für FT8 & CW (NanoVNA-abgestimmt)

### Antennenkonzept: Linked 49:1 EFHW ($40\text{ m} / 30\text{ m} / 20\text{ m} / 17\text{ m} / 15\text{ m} / 10\text{ m}$)
* **Grundprinzip:** Ein **49:1 UnUn** ($2:14$ Windungen auf Fair-Rite `2643251002` / `FT140-43` Mix 43) speist einen Halbwellenstrahler ohne Antennentuner ($\text{SWR} \le 1.3$ in Resonanz).
* **NanoVNA Abstimm-Ziel ($S_{11}$):** SWR-Minimum exakt zwischen CW-Segment und FT8-Frequenz trimmen:
  * **40m:** **$7.050\text{ MHz}$** (deckt CW $7.000\text{--}7.040\text{ MHz}$ & FT8 $7.074\text{ MHz}$ bei $\text{SWR} < 1.5$ ab)
  * **20m:** **$14.045\text{ MHz}$** (deckt CW $14.000\text{--}14.070\text{ MHz}$ & FT8 $14.074\text{ MHz}$ ab)
  * **15m:** **$21.045\text{ MHz}$** (deckt CW & FT8 $21.074\text{ MHz}$ ab)
  * **10m:** **$28.045\text{ MHz}$** (deckt CW & FT8 $28.074\text{ MHz}$ ab)
  * **30m & 17m (via Band-Links):** Über $2\text{ mm}$ Goldkontakt-Steckbrücken im Strahler bei ca. **$14.2\text{ m}$** ($30\text{ m}$: $10.116\text{ CW} / 10.136\text{ FT8}$) und **$8.0\text{ m}$** ($17\text{ m}$: $18.080\text{ CW} / 18.100\text{ FT8}$) ohne Tuner schaltbar.

### Einkaufsliste – Antenne, Mantelwellensperre & Messmittel

| Status | Pos | Komponente / Komplettset | Technische Spezifikation | AliExpress Search Keywords | Menge | Richtpreis (CHF) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| - [ ] | 3.1 | **`[SET]` 49:1 QRP EFHW UnUn DIY-Bausatz** | Enthält `FT140-43` (Mix 43) Ferritkern, $100\text{ pF} / 3\text{ kV}$ C0G-Kondensator, $0.8\text{ mm}$ Kupferlackdraht, BNC-Buchse & wasserdichtes Mini-Gehäuse | `49:1 EFHW end fed antenna DIY kit FT140-43 BNC QRP` | 1 | 12.50 |
| - [ ] | 3.2 | **`[SET]` 1:1 Mantelwellensperre (Choke) Kit** | `FT140-43` oder `FT114-43` Toroid + $1.5\text{ m}$ RG316 Koax + $2\times$ BNC Male Stecker + Mini-Box | `FT140-43 ferrite toroid core RG316 coaxial BNC` | 1 | 8.50 |
| - [ ] | 3.3 | **`[SET]` SOTA Strahler- & Link-Zubehör** | $25\text{ m}$ hochflexible Silikonlitze ($20\text{ AWG} / 0.5\text{ mm}^2$) + Line-Winder + End-Isolatoren + $10\text{ m}$ Paracord ($2\text{ mm}$) + $2\text{ mm}$ Goldstecker-Set | `20AWG silicone wire 25m antenna winder insulator 2mm banana` | 1 | 11.50 |
| - [ ] | 3.4 | **`[SET]` NanoVNA-H4 Komplettset** *(falls nicht vorhanden)* | NanoVNA-H4 ($4\text{ Zoll}$ Display) inkl. **SOLT-Kalibrierkit** (Short/Open/Load/Thru) & SMA-Messkabeln | `NanoVNA-H4 vector network analyzer calibration kit` | 1 | 58.00 |
| - [ ] | 3.5 | **GFK-Teleskopmast (optional)** | **$6\text{ m}$ oder $7\text{ m}$** ultraleichter GFK-Mast (Packmaß $< 65\text{ cm}$ für SOTA-Rucksack) | `6m ultralight fiberglass fishing rod pole SOTA` | 1 | 16.00 |

---

## 4. Vollständige Kabel-, Pigtail- & Adapter-Liste (Set-optimiert)

| Status | Pos | Komponente / Komplettset | Verbindung & Spezifikation | AliExpress Search Keywords | Menge | Richtpreis (CHF) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| - [ ] | 4.1 | **`[SET]` SMA $\leftrightarrow$ BNC HF-Adapter-Kit (8-teilig)** | Kompletter Satz: SMA-M/F $\leftrightarrow$ BNC-M/F & SMA-M $\leftrightarrow$ SMA-M (für HL2, NanoVNA & Feld-Reserve) | `SMA to BNC RF coaxial adapter kit 8pcs` | 1 | 6.50 |
| - [ ] | 4.2 | **`[SET]` XT60 & DC $5.5 \times 2.1\text{ mm}$ Power-Set** | $5\times$ XT60 Paar + vorkonfektionierte XT60-auf-DC-$5.5\times 2.1\text{ mm}$ Kabel ($16\text{ AWG}$) + wasserdichte Einbaubuchsen | `XT60 to DC 5.5x2.1mm cable 16AWG panel mount jack kit` | 1 | 7.50 |
| - [ ] | 4.3 | **`[SET]` Ultra-Kurz-Patchkabel-Paket (USB & LAN)** | $2\times$ **Cat7 S/FTP LAN** ($0.25\text{ m}$, HL2 $\leftrightarrow$ RPi 4B) + $2\times$ **USB-C Power** ($0.2\text{ m}$, Buck $\leftrightarrow$ RPi 4B) *(Pico braucht im Betrieb keine USB-Verbindung zum Pi; nur zum Flashen einmal ein beliebiges Micro-USB-Kabel am Rechner)* | `short Cat7 ethernet cable 0.25m short USB C Micro USB 20cm` | 1 | 8.50 |
| - [ ] | 4.4 | **HF-Pigtail (HL2 Front $\leftrightarrow$ Koax)** | **SMA Male** auf **BNC Female**, RG316 Koax, Länge **$15\text{--}20\text{ cm}$** (Zugentlastung der SMA-Buchse am HL2) | `SMA male to BNC female RG316 pigtail cable 15cm` | 2 | 4.00 |
| - [ ] | 4.5 | **SOTA-Speiseleitung (Koax)** | **$5\text{ m}$ RG316** oder **RG58** mit **BNC Male $\leftrightarrow$ BNC Male** (leicht & flexibel für Portabelbetrieb) | `BNC male to BNC male RG316 coaxial cable 5m` | 1 | 7.50 |
| - [ ] | 4.6 | **Keying-Kabel IO-Board ACC $\leftrightarrow$ HL2 Key-Buchse** | **3,5-mm-Klinkenstecker 3-polig (Stereo/TRS)** + **D-Sub-Stecker passend zum ACC-Anschluss** (Polzahl/Geschlecht am Gerät prüfen, mit Haube) + $30\text{ cm}$ 3-adriges geschirmtes Kabel. Belegung: Out7 (KEY) → Tip, Out8 (PTT) → Ring, GND → Sleeve | `3.5mm stereo plug solder` + `D-sub connector solder hood` + `3 core shielded cable` | 1 | 6.00 |
| - [ ] | 4.7 | **IO-Board Flachbandkabel** | $2.54\text{ mm}$ IDC / Dupont Flachbandkabel ($10$-polig / $20$-polig, falls IO-Board extern angebunden wird) | `2.54mm IDC ribbon cable 10 pin 20 pin` | 1 | 2.50 |

---

## 5. Kostenübersicht & Checkliste vor Inbetriebnahme

### Geschätztes Gesamtbudget
* **Baugruppe 2 (18650 4S2P Power Pack inkl. Spot-Welder, Charger & Markenzellen):** ca. **CHF 110.50** *(ohne Spot-Welder & Gehäuse: ca. **CHF 86.00**)*
* **Baugruppe 3 (Tunerlose Linked-EFHW $40\text{m--}10\text{m}$ + Choke + Mast):** ca. **CHF 48.50** *(zzgl. ca. CHF 58.00, falls NanoVNA-H4 noch nicht vorhanden)*
* **Baugruppe 4 (Alle Kabel-, Adapter- & Stecker-Sets):** ca. **CHF 42.50**
* **Summe Peripherie (Power + Antenne + Verkabelung):** ca. **CHF 177.00 – 201.50** *(zzgl. SDR/RPi-Kernhardware aus Baugruppe 1, falls nicht vorhanden)*

### Obligatorische Prüf-Schritte vor dem ersten Einschalten
1. **Spannungs-Check (ohne HL2):** Buck-Boost Wandler (Pos. 2.3) mit Multimeter exakt auf **$13.80\text{ V}$ DC** einstellen und Potentiometer mit einem Tropfen Sicherungslack fixieren.
2. **Polaritäts-Check:** Innenstift am DC $5.5 \times 2.1\text{ mm}$ Stecker des HL2 muss zwingend **Plus ($+$)** führen.
3. **NanoVNA-Abgleich:** Antenne in realer SOTA-Aufbauhöhe (z. B. Inverted-V am $6\text{ m}$ Mast) mit kalibriertem NanoVNA (inkl. angeschlossenem 1:1 Choke & $5\text{ m}$ Koax) auf $\text{SWR} < 1.5$ für CW- und FT8-Frequenzen ablängen.
