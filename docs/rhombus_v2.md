# Terminated Rhombic RX-Antenne (40 m / 30 m / 20 m)  
**Engineering- & Integrationsleitfaden**

- **Systemarchitektur:** Monodirektionale Wanderwellen-Empfangsantenne (Terminated Rhombic)  
- **Zielbänder:**  
  - 40 m: 7,0–7,2 MHz  
  - 30 m: 10,10–10,15 MHz  
  - 20 m: 14,0–14,35 MHz  
- **SDR-Frontend:** Hermes-Lite 2 (HL2, AD9866 12‑Bit ADC) + N2ADR Filter-Board + RP2040 IO-Board  
- **Standort:** LV95 2’685’931.37, 1’152’055.87 (1528 m ü. M., alpiner Nadelwald / Lichtung)

---

## 1. Physikalische Auslegung & Standortparameter

### 1.1 Richtwirkung und 3D-Hanggeometrie

- **Wanderwellen-Prinzip (Hauptstrahlrichtung)**  
  Der Empfangsgewinn entsteht durch phasenrichtige Aufsummierung der entlang der Drähte laufenden Welle in Richtung des Speisepunkts.  
  Wellen, die aus der Gegenrichtung einfallen, werden im Abschlusswiderstand in Wärme umgesetzt. Dadurch entsteht eine hohe Richtwirkung mit starker Rückdämpfung.

- **Speisepunkt (Feedpoint)**  
  - Lage: Westsüdwest  
  - Azimut: ca. 255–260°

- **Abschlusspunkt (Termination)**  
  - Lage: Ostnordost  
  - Azimut: ca. 75–80°

- **Resultierender Hauptempfangsvektor (Main Lobe)**  
  - Azimut: ca. 75–80° (Ostnordost)  
  - Zielgebiete: Osteuropa, Zentralasien, Japan / Fernost, teilweise Long‑Path nach Nordamerika

- **Rückdämpfung (Nullstelle)**  
  - Azimut: ca. 255–260° (Westsüdwest)  
  - Starke Unterdrückung von Signalen aus Westeuropa, Nordatlantik und grossem Teil von Nordamerika (Short‑Path)

- **Entkopplung von Quer- und Längsneigung am Nordhang**  
  Das Gelände fällt bei LV95 2’685’931.37, 1’152’055.87 nach Nordnordwest ab (Azimut ≈ 350°).  
  Die Antenne wird entlang der Höhenlinie (Azimut 75–80°) montiert.  
  Bei konstanter Masthöhe über Grund ergibt sich dadurch:
  - eine **Querneigung (Roll)** der Antennenebene nach Norden  
  - jedoch **keine relevanten Änderungen des Erhebungswinkels** in Hauptstrahlrichtung.  
  Die Elevation der Hauptkeule wird also nicht durch das Hanggefälle in Längsrichtung beeinflusst.

- **Gezielte Pitch-Neigung (Längsgefälle in Strahlrichtung)**  
  Ziel: Den vertikalen Erhebungswinkel Δ in Richtung Ostnordost um ca.  
  \(\beta_\text{pitch} \approx -4{,}3^\circ\) abzusenken und gleichzeitig den Wellenwiderstand  
  \(Z_0 \approx 750\,\Omega\) über dem Boden weitgehend konstant zu halten.

  Dazu wird die Aufhängung gestaffelt:

  - **West-Anker (Speisepunkt):** 15,5–16,0 m über Waldboden  
  - **Nord-/Süd-Anker (Seiten-Apices):** 12,5–13,0 m über Waldboden  
  - **Ost-Anker (Abschlusspunkt):** 9,5–10,0 m über Waldboden  

  Die Antennenebene fällt damit leicht nach Osten ab (Pitch), was den wirksamen Elevationswinkel der Hauptkeule reduziert.

---

### 1.2 Elektromagnetische 3D-Phasenbilanz  
*(L = 44 m, φ = 65°, mittlere Höhe \(\overline{H} = 13\,\text{m}\))*

Über trockenem alpinem Fels-/Waldboden gelten näherungsweise:  
- Leitfähigkeit: \(\sigma \approx 10^{-3}\,\text{S/m}\)  
- relative Permittivität: \(\varepsilon_r \approx 5\)

Die resultierende Elevation des Hauptempfangsstrahls ergibt sich aus der Überlagerung von:

1. **Phasenwinkel des Einzelschenkels**  
   \[
   \cos(\theta_0) = 1 - \frac{0{,}371 \cdot \lambda}{L},
   \]
   wobei \(\cos(\theta_0) = \cos(\Delta_\text{wire}) \cdot \sin(\phi)\).  
   Daraus folgt \(\Delta_\text{wire}\), die Elevation der Drahtkeule ohne Bodenreflexion.

2. **Erster vertikaler Bodenreflexionszipfel**  
   \[
   \Delta_\text{ground} = \arcsin\left(\frac{\lambda}{4 \overline{H}}\right).
   \]

3. **Pitch-Korrektur**  
   - Die oben beschriebene Längsneigung (Pitch) von ca. −4,3° senkt den effektiven Elevationswinkel zusätzlich.

#### Zusammenfassung der resultierenden Parameter

| Parameter                                           | 40 m-Band (7,05 MHz) | 30 m-Band (10,12 MHz) | 20 m-Band (14,05 MHz) |
|-----------------------------------------------------|----------------------|-----------------------|-----------------------|
| Wellenlänge λ                                       | 42,52 m              | 29,62 m               | 21,34 m               |
| Elektrische Schenkellänge L/λ                       | 1,03 λ               | 1,49 λ                | 2,06 λ                |
| Drahtkegel-Winkel θ₀                               | 50,1°                | 41,4°                 | 34,9°                 |
| Phasen-Elevation Δ_wire (bei φ = 65°)               | 45,0°                | 34,2°                 | 24,8°                 |
| Boden-Elevation Δ_ground (bei \(\overline{H}=13\,\)m) | 54,9°                | 34,8°                 | 24,2°                 |
| Effektiver Abstrahlwinkel inkl. −4,3° Pitch         | ca. 43–48°           | ca. 30,2°             | ca. 20,2°             |
| Richtgewinn (inkl. Terminierungsverlust)            | ≈ 7,5 dBi            | ≈ 10,2 dBi            | ≈ 12,5 dBi            |
| Vor‑Rück‑Verhältnis (F/B, kompensiert)              | ≈ 18 dB              | ≈ 24 dB               | ≈ 26 dB               |
| Horizontale Halbwertsbreite (−3 dB Azimut)          | ≈ 32°                | ≈ 22°                 | ≈ 16°                 |

---

## 2. Geometrie, Trigonometrie & Vermessung

### 2.1 Grundgeometrie der Rhombus-Antenne

Schematische Draufsicht (nicht massstabstreu):

```text
           [NORD-ANKER]
        (12,5–13,0 m Höhe)
         Umlenkrolle + 9,5 kg
                 /\
                /  \
               /    \
   Schenkel 1 /      \ Schenkel 2
     L = 44 m /        \ L = 44 m
             / 130° (2φ) \
            /            \
[WEST-ANKER: FEED]      [OST-ANKER: TERM]
   (15,5–16,0 m)         (9,5–10,0 m)
   statisch auf Klampe   statisch auf Klampe
   (Haltekraft ~20,3 kgf) (Haltekraft ~20,3 kgf)
            \            /
             \ 130°    /
   Schenkel 4 \      / Schenkel 3
     L = 44 m  \    /  L = 44 m
               \  /
                \/
            [SÜD-ANKER]
        (12,5–13,0 m Höhe)
         Umlenkrolle + 9,5 kg
```

Längs- und Querabstände:

- Draht-Längsachse: ca. 79,75 m  
- Mindestabstand der Eckisolatoren zu den Baumstämmen: 3,0 m  
- Daraus folgt:  
  - **Baum-Ankerabstand Ost–West:** ca. 85,75 m  
  - **Baum-Ankerabstand Nord–Süd:** siehe Tabelle unten

### 2.2 Massvorgaben für L = 44,0 m (Regelausbau) und L = 38,0 m (Kompaktvariante)

Um dielektrische Zusatzverluste und Verstimmungen durch nasses Nadelholz oder Schneebehang zu minimieren, müssen die vier Eckisolatoren mittels Dyneema-Vorlaufseilen mindestens 3,0 m frei vor den Stämmen und Ästen schweben.

| Geometrie-Parameter                    | Formel                            | Regelausbau (L = 44,0 m)         | Kompaktvariante (L = 38,0 m)      |
|----------------------------------------|-----------------------------------|-----------------------------------|-----------------------------------|
| Halber Stumpfwinkel φ                  | Vorgabe                           | 65,0° (2φ = 130°)                 | 65,0° (2φ = 130°)                 |
| Halber Spitzwinkel α                   | 90° − φ                           | 25,0° (2α = 50°)                  | 25,0° (2α = 50°)                  |
| Schenkellänge L                        | Vorgabe                           | 44,00 m                           | 38,00 m                           |
| Gesamtdrahtlänge                       | 4·L + 1,0 m Zugabe                | 177,00 m                          | 153,00 m                          |
| Draht-Längsdiagonale \(D_\text{long}\) | 2·L·sin(65°)                      | 79,75 m                           | 68,88 m                           |
| Draht-Querdiagonale \(D_\text{trans}\) | 2·L·cos(65°)                      | 37,19 m                           | 32,12 m                           |
| min. Baumabstand Ost–West              | \(D_\text{long} + 2·3,0\) m       | 85,75 m                           | 74,88 m                           |
| min. Baumabstand Nord–Süd              | \(D_\text{trans} + 2·3,0\) m      | 43,19 m                           | 38,12 m                           |

---

## 3. Stückliste (Bill of Materials – BOM)

### 3.1 Übersicht

| Pos. | Baugruppe            | Komponente / Spezifikation                                                                                                  | Menge       | Richtpreis (CHF) |
|------|----------------------|------------------------------------------------------------------------------------------------------------------------------|-------------|------------------|
| 1.1  | Strahler & Seile     | Kupfer-Stahl-Litze (Copperweld / DX-Wire UL oder FL, Ø 1,5–1,8 mm, UV-PE-Mantel, Bruchlast ≥ 60 daN)                         | 180 m       | 95.00            |
| 1.2  |                      | Dyneema SK78 Geflechtseil (Ø 3,0 mm, Bruchlast 950 daN, Reck \< 1 %, schwarz UV-stabilisiert)                               | 120 m       | 78.00            |
| 1.3  |                      | Keramik- oder PTFE-Ei-Isolatoren (Bruchlast ≥ 150 daN) für Nord-/Süd-Ecken                                                  | 4 Stk.      | 16.00            |
| 2.1  | Mechanik (4 Bäume)   | Baumschoner-Rundschlingen (Polyester, 2 m Umfang, 1000 daN, grün/schwarz)                                                   | 4 Stk.      | 36.00            |
| 2.2  |                      | Edelstahl-Blockseilrollen (V4A / AISI 316, kugelgelagert, für 4–6 mm Seil) + V4A-Schäkel                                   | 6 Stk.      | 54.00            |
| 2.3  |                      | Edelstahl-Belegklampen (150 mm, auf Montageplatte mit Spanngurt am Stammfuss West & Ost)                                   | 2 Stk.      | 28.00            |
| 2.4  |                      | Gegengewichte Nord & Süd (z. B. mit Kies/Blei gefüllte PE-Rohre, exakt 9,5 kg je Seite)                                     | 2 Stk.      | 25.00            |
| 3.1  | West-Box (Feed)      | Gehäuse Fibox ARCA / Bopla Polycarbonat IP67 (120×80×60 mm) + M12-Druckausgleichsmembran                                    | 1 Stk.      | 24.00            |
| 3.2  |                      | Doppellochkern Fair-Rite 2861000202 (Material 61, bevorzugt) oder 2843000202 (Material 43)                                  | 1 Stk.      | 8.50             |
| 3.3  |                      | PTFE-Wickeldraht AWG 22 (Ø 0,65 mm, versilbert) für 2:8 Windungen (Mittenanzapfung bei Wdg. 4)                              | 1,5 m       | 3.00             |
| 3.4  |                      | Kompensationskondensator 82 pF (C0G/NP0, 500 V) parallel zur Primärwicklung                                                | 1 Stk.      | 1.20             |
| 3.5  |                      | Bleeder-/Schutznetzwerk: 1× 47 kΩ / 2 W Metalloxid + Bourns 90 V GDT (2093‑90‑SM / bedrahtet)                              | 1 Set       | 4.50             |
| 3.6  |                      | Mantelwellensperre: Ringkern Fair-Rite FT240‑31 + 1,6 m RG‑400 PTFE-Koax + 2× BNC/N‑Stecker                                 | 1 Set       | 32.00            |
| 4.1  | Ost-Box (Term)       | Gehäuse Polycarbonat IP67 (120×80×60 mm) + M12-Druckausgleichsmembran + V4A-Augenschrauben                                  | 1 Stk.      | 24.00            |
| 4.2  |                      | Abschluss-Array: 4× 3,0 kΩ / 2 W induktionsarme Metalloxid-/Schichtwiderstände (parallel = 750 Ω)                         | 4 Stk.      | 4.00             |
| 4.3  |                      | Kompensationskondensator 12 pF (Glimmer / Silver Mica oder C0G/NP0, 500 V) parallel zu 750 Ω                               | 1 Stk.      | 2.50             |
| 5.1  | Zuleitung & HL2      | Koaxkabel Messi & Paoloni Hyperflex 5 (Ø 5,4 mm, Litzen-Innenleiter, doppelt geschirmt)                                     | 50 m        | 85.00            |
| 5.2  |                      | Blitzschutz am Gebäudeeintritt: Koax-Überspannungsableiter (GDT 90 V, z. B. Diamond SP‑1000)                               | 1 Stk.      | 42.00            |
| 5.3  |                      | Monoband-BPF-Bank (40 m / 30 m / 20 m, 3‑Pol T50‑6 / C0G) geschaltet via N2ADR IO-Board + BAV99 Limiter                   | 1 Einheit   | 65.00            |

---

## 4. Seilstatik & Mechanische Installation (1528 m ü. M.)

### 4.1 Kräftegleichgewicht der Rhombus-Geometrie

Damit sich die Winkel 2α = 50° (West/Ost) und 2φ = 130° (Nord/Süd) unter Zug nicht verziehen, muss das Verhältnis der Haltekräfte an den Ecken dem Kosinusverhältnis der Halbwinkel entsprechen.

- **Definierte Drahtvorspannung**
  - Drahtkraft pro Schenkel:  
    \(T_\text{wire} = 110\,\text{N} \approx 11{,}2\,\text{kgf}\)
  - Durchhang (trocken):  
    \(f = \dfrac{w \cdot L^2}{8 \cdot T}\)  
    mit \(w \approx 0{,}20\,\text{N/m}\) und \(L = 44\,\text{m}\) ergibt:  
    \(f \approx 0{,}44\,\text{m}\)

#### West- und Ost-Ecke (statische Festpunkte mit Wartungsabsenkung)

- Dyneema-Seil läuft an den Bäumen im Westen (15,5–16,0 m) und Osten (9,5–10,0 m) über Umlenkrollen nach unten.  
- Unten wird das Seil auf Belegklampen am Stammfuss festgesetzt.  
- Es werden **keine Gegengewichte** an West und Ost verwendet.

**Zuglast an der Klampe:**

\[
F_\text{West/Ost} = 1{,}813 \cdot T_\text{wire} \approx 200\,\text{N} \approx 20{,}3\,\text{kgf}
\]

Vorteile:

- Speisepunkt (inkl. Koaxgewicht) und Abschlusspunkt sind räumlich stabil.  
- Beide Boxen lassen sich für Wartung (z. B. Anpassungen, Reparaturen) vom Boden aus ablassen.

#### Nord- und Süd-Ecke (dynamischer Lastausgleich über Gegengewichte)

- Dyneema-Seil läuft an Nord- und Südbäumen (12,5–13,0 m) über Umlenkrollen zu je einem frei hängenden Gegengewicht.  
- Gegengewicht je Seite: 9,5–10,0 kg.

**Resultierende Haltekraft:**

\[
F_\text{Nord/Süd} = 0{,}845 \cdot T_\text{wire} \approx 93\,\text{N} \approx 9{,}5\,\text{kgf}
\]

Da alle vier Drahtschenkel an den Nord-/Süd-Isolatoren kraftschlüssig gekoppelt sind, regulieren diese beiden Seitengewichte die Drahtspannung im gesamten Rhombus automatisch auf ca. 110 N.

#### Schneelast-Fangschlaufe (Fail-Safe)

- Gegengewichte in Nord und Süd auf ca. 3,5 m Höhe über dem Boden einhängen.  
- Etwa 1,2 m oberhalb der Ruheposition des Gewichts:  
  - festen Achterknoten mit Sicherheitskarabiner in eine Fangschlaufe am Stamm setzen.  

**Wirkprinzip:**

- Bei extremem Nassschnee oder Eisregen wandert das Gewicht max. ca. 1,2 m nach oben.  
- Dadurch werden etwa 1,0 m Draht nachgegeben, die Spitzenzugkraft sinkt.  
- Anschliessend geht das System in den statischen Anschlag über, bevor die Eckisolatoren in die Umlenkrollen gezogen werden.

---

## 5. HF-Systemdesign & Schaltungsaufbau

### 5.1 Gesamtschaltbild (West-Box & Ost-Box)

```text
=======================================================================================
WEST-BOX (Speisepunkt, IP67)                 OST-BOX (Abschluss, IP67)
=======================================================================================

   Schenkel 1 + 2 (Nord, gesamt 88,0 m)
   +--------------------/\/\/\-----------------------+
   |                                                |
   +------+-----------------------------+-----------+
          |                             |
          |  4 Wdg.                     |
          | ) ||                        |  4 × 3,0 kΩ (2 W) MOX
          | ) ||                        |  parallel = 750 Ω (8 W)
          | ) ||   Fair-Rite            |
          | ) ||   2861000202           +---o--+---[ 82 pF ]---+---o  BNC
   4 Wdg. | ) ||   (oder 2843000202)    |     |                |      (50 Ω)
          | ) ||                        |     |                |
          | ) ||                        |   2 Wdg.             |
          +--o--------------------------+----------------------+ 
             |                          |                [ 12 pF ]
             |                          |                (NP0 500 V)
             |                          |                    |
             |                          |                    |
             |      Komplett erdfrei (floating)!             |
             +-----------------------------------------+------+
                                                   Schenkel 3 + 4 (Süd)
                                                   +-------/\/\/\-------+

   Symmetrie-Mittenanzapfung (Sekundärwicklung, Wdg. 4):

           +---[ 47 kΩ / 2 W ]---+
           |                     |
           +---[ 90 V GDT ]------+---> auf BNC-Masse (Koax-Schirm VOR Mantelwellensperre)

   BNC-Durchführung
           |
           | 10 Wdg. RG-400 als Crossover-Choke auf FT240-31
           v
   (Mantelwellensperre)
           |
           v
   50 m Hyperflex 5 zum Rustico

=======================================================================================
```

- Die Rhombusantenne ist HF-seitig **komplett erdfrei** (floating).  
- Die Mittenanzapfung dient nur zur kontrollierten Ableitung statischer Ladungen und liegt HF-mässig im Spannungsnullpunkt.

---

### 5.2 Fertigung der West-Box (Speisepunkt & Elektrostatik-Ableitung)

#### Impedanzübertrager (16:1 → 50 Ω auf ca. 800 Ω)

- Ein einzelner Rhombusdraht (Ø 1,5–1,8 mm) in ca. 13 m Höhe besitzt einen mittleren Wellenwiderstand von ca. 750 Ω.  
- Ziel: Anpassung auf 50 Ω Koax über einen 16:1-Transformator.

**Vorgehen:**

1. Doppellochkern Fair-Rite 2861000202 (Material 61, bevorzugt) oder 2843000202 (Material 43) verwenden.  
2. **Primärwicklung:**  
   - Np = 2 Windungen PTFE-Wickeldraht AWG 22.  
3. **Sekundärwicklung:**  
   - Ns = 8 Windungen, räumlich getrennt von der Primärseite.  
   - Übersetzungsverhältnis: \(n = \dfrac{N_s}{N_p} = 4\)  
   - Impedanzverhältnis: \(n^2 = 16\) → 50 Ω · 16 ≈ 800 Ω.  
   - Gegenüber 750 Ω resultiert ein **SWR ≈ 1,06**, also nahezu ideal.  
4. **Mittenanzapfung:**  
   - Nach der 4. Sekundärwindung (Ns/2) eine Anzapfung herausführen.  
   - Diese bildet den elektrischen Nullpunkt für symmetrische HF-Spannungen.

5. **Kompensationskondensator:**  
   - Direkt über die Primäranschlüsse (BNC-seitig) einen 82 pF C0G/NP0 (500 V) löten.  
   - Zweck: Kompensation der Streuinduktivität des Kerns und Optimierung der Anpassung im 20 m-Band.

#### Elektrostatische Ableitung (Precipitation Static Bleeder)

- Die beiden Antennenschenkel sind im Osten DC-mässig über den 750 Ω-Abschluss verbunden → geschlossene DC-Schleife.  
- Die Mittenanzapfung (Windung 4) der Sekundärwicklung wird an die Masse der BNC-Buchse (Koax-Schirm) geführt – jedoch über ein Schutznetzwerk:

**Bleeder-/Schutznetzwerk:**

- 47 kΩ / 2 W Metalloxid-Widerstand **parallel** zu einem 90 V Gasentladungsableiter (GDT).  
- Verbindung von Mittenanzapfung → Bleeder/GDT → BNC-Gehäuse / Koax-Schirm.

**Wirkprinzip:**

- Langsame statische Aufladungen (Höhenwind, Graupel, trockener Pulverschnee) werden über 47 kΩ kontinuierlich und symmetrisch zur geerdeten Koax-Schirmung im Rustico abgeleitet.  
- Für HF-Signale liegt die Mittenanzapfung im Spannungsnullpunkt; die galvanische Trennung zwischen Antenne und Koax bleibt vollständig erhalten.  
- Der GDT schützt zusätzlich vor Überspannungsereignissen (z. B. entfernte Blitzeinschläge), indem er bei ca. 90 V zündet und die Mittenanzapfung kurzzeitig hart auf Masse zieht.

---

### 5.3 Fertigung der Mantelwellensperre (FT240‑31)

- Montage unmittelbar unterhalb der West-Box.

**Aufbau:**

1. 10 Windungen RG‑400 PTFE-Koaxkabel auf einen FT240‑31 Ringkern wickeln.  
2. Wickelschema (Reisert-Crossover):  
   - 5 Windungen auf einer Kernhälfte wickeln,  
   - Kabel diagonal durch die Kernmitte führen,  
   - weitere 5 Windungen in Gegenrichtung auf der anderen Hälfte aufbringen.

**Vorteile:**

- Reduzierte parasitäre Durchgangskapazität zwischen Ein- und Ausgang.  
- Eigenresonanz (SRF) liegt bei ca. 10,5 MHz (30 m-Band).  
- Rein **resistive** Gleichtakt-Sperrimpedanz \(Z_\text{cm} > 4\,\text{k}\Omega\) von 7,0 bis 14,35 MHz.

**Mechanische Entlastung:**

- Das abgehende Hyperflex‑5-Kabel ca. 1,5 m unterhalb der Drossel mit einer gummierten Kabelschelle am tragenden Abspannseil befestigen.  
- So hängt kein Kabelgewicht an BNC-Stecker oder Ringkern.

---

### 5.4 Fertigung der Ost-Box (kompensierter 750 Ω-Abschluss)

#### Vollständige Erdfreiheit

- In der Ost-Box werden **keine** Erdleitungen, GDTs oder Bleeder gegen Boden angeschlossen.  
- Eine vertikale Erdleitung am östlichen Ende würde als (ungewollte) Vertikalantenne wirken, in den Abschlusswiderstand einkoppeln und die Rückdämpfung erheblich verschlechtern.

#### Widerstands-Array

- 4 identische 3,0 kΩ / 2 W Metalloxid- oder Dickschichtwiderstände  
- Eng nebeneinander, kurze Anschlussdrähte, **parallel** verschaltet:

\[
R_\text{ges} = \dfrac{3{,}0\,\text{k}\Omega}{4} = 750\,\Omega
\]

- Gesamtbelastbarkeit: 8 W  
- Parallelverschaltung reduziert die parasitäre Serieninduktivität auf etwa ein Viertel eines Einzelwiderstands.

#### Blindwiderstands-Kompensation

- Parallel zur Widerstandsgruppe:  
  - 12 pF Glimmer- oder C0G/NP0-Kondensator (500 V).  
- Zweck: Kompensation des induktiven Blindanteils der spitz zulaufenden Antennenenden (2α = 50°) insbesondere auf 30 m und 20 m.  
- Effekt: Vertiefung der Rückwärts-Nullstelle um ca. 6–10 dB, Verbesserung des F/B-Verhältnisses.

---

## 6. Zuleitung, Blitzschutz & Hermes-Lite 2 Integration

### 6.1 Koax-Zuleitung und Gebäudeeintritt (NIN / SEV 1000)

#### Kabelwahl

- **Typ:** Messi & Paoloni Hyperflex 5  
- Eigenschaften:
  - Flexibler, verseilter Litzen-Innenleiter (19 × 0,28 mm) → unempfindlich gegen Bruch durch Windbewegung.  
  - Kabeldämpfung auf 50 m bei 14 MHz: ca. 2,8 dB.  

Diese Dämpfung ist unkritisch, da das externe atmosphärische Rauschen am Richt-Rhombus die innere Rauschzahl des Empfängers um mehr als 25 dB übersteigt.

#### Potentialausgleich

- Am Gebäudeeintritt ins Rustico:
  - Koaxialen Überspannungsableiter (GDT 90 V, z. B. Diamond SP‑1000) installieren.  
  - Gehäuse des Überspannungsableiters mit min. 6 mm² Cu direkt auf die Potentialausgleichsschiene führen (NIN / SEV 1000-konform).

---

### 6.2 HL2-Signalkette, Preselektion und TX/RX-Koexistenz

#### Blockdiagramm

```text
[Hyperflex 5 vom Rhombus]
            |
            v
   +-----------------------+
   | Koax-Blitzschutz GDT |====> Potentialausgleichsschiene (≥ 6 mm² Cu)
   +-----------------------+
            |
            v
   +-----------------------+
   | TX-Mute Relais +     | <--- PTT vom N2ADR-Board
   | BAV99 Dioden-Limiter |      (legt RX-Pfad bei TX auf Masse)
   +-----------------------+
            |
            v
   +-----------------------+
   | Monoband-BPF Bank    | <--- Bandwahl via RP2040 / N2ADR IO-Board
   | (40 m / 30 m / 20 m) |      Unterdrückung 41 m / 31 m BC > 45 dB
   +-----------------------+
            |
            v
 [HL2 J9 (RF2) Dedizierter RX-Eingang]
 (umgeht N2ADR TX-Tiefpassfilter)
```

#### Nutzung des dedizierten RX-Eingangs J9 (RF2)

- Rhombus an **RF2 (J9)** des HL2 anschliessen.  
- Jumper auf dem HL2 so setzen, dass RF2 als RX-Eingang aktiv ist.  
- Vorteil: Empfangssignal durchläuft **nicht** die Sende-Tiefpassfilter des N2ADR-Boards.  
- Eine separate Sendeantenne (z. B. 2× 20,1 m Doublet) bleibt dauerhaft am N2ADR-Hauptausgang (TX).

#### Zwingender TX-Überspannungsschutz bei Mehrantennenbetrieb

- Bei Betrieb einer separaten Sendeantenne mit ca. 5 W im gleichen Nahfeld koppeln im Rhombus hohe HF-Spannungen ein (oft > +20 dBm).  
- Daher direkt vor der BPF-Bank:

  1. **PTT-gesteuertes Relais:**  
     - Während PTT aktiv → RX-Pfad kurzzeitig auf Masse legen.

  2. **Dioden-Begrenzer (Clipper):**  
     - z. B. BAV99 oder 2× 1N4148 antiparallel von Signal gegen Masse.  
     - Schwellspannung ca. ±0,7 V → ≈ +7 dBm am Eingang.  
     - Schützt den AD9866 vor Übersteuerung bzw. Dauerschäden durch eingekoppelte HF.

#### AD9866 LNA Gain-Staging (Vermeidung von ADC-Clipping)

Ziel:  
Beim Umschalten von einem 50 Ω-Dummyload auf den Rhombus soll der Grundrauschpegel im SDR um **8–10 dB** ansteigen.

**Empfohlene LNA-Gains und Zielwerte:**

| Band | Frequenzbereich         | BPF-Status (RP2040 IO) | Zielwert HL2 LNA-Gain | Resultierender MDS (500 Hz CW) | Nutzbarer BDR am AD9866 |
|------|-------------------------|------------------------|------------------------|---------------------------------|-------------------------|
| 40 m | 7,00–7,20 MHz           | 40 m-BPF aktiv         | −3 dB bis 0 dB         | ≈ −113 bis −116 dBm             | 100–102 dB              |
| 30 m | 10,10–10,15 MHz         | 30 m-BPF aktiv         | 0 dB bis +3 dB         | ≈ −116 bis −119 dBm             | 97–99 dB                |
| 20 m | 14,00–14,35 MHz         | 20 m-BPF aktiv         | +3 dB bis +6 dB        | ≈ −119 bis −122 dBm             | 94–96 dB                |

- Feinanpassung jeweils im realen Betrieb mit Quisk / SparkSDR / Thetis vornehmen.  
- Oberziel: Atmosphärisches Rauschen klar dominierend, ADC nie in Clip.

---

## 7. Montageablauf & VNA-Inbetriebnahmeprotokoll

### 7.1 Schritt-für-Schritt-Aufbau im Gelände

1. **Laser-Distanz- und Kompass-Vermessung**

   - Vom Zentrum der Lichtung aus:
     - Kompass nutzen (Deklination Schweiz 2026: ca. +3,0° Ost einrechnen).  
     - Längsachse markieren:  
       - Azimut 75–80° / 255–260°, Baumabstand ≥ 85,8 m.  
     - Querachse (orthogonal) markieren:  
       - Azimut 165–170° / 345–350°, Baumabstand ≥ 43,2 m.  
   - Abstände mit Laser-Entfernungsmesser prüfen und geeignete Bäume auswählen.

2. **Anschlagen der Rollen und Klampen**

   - Baumschoner-Gurte und V4A-Rollen an den vier Bäumen auf den Zielhöhen montieren:
     - West: 15,5 m  
     - Nord/Süd: 12,8 m  
     - Ost: 9,8 m  
   - Hilfsleinen durch die Rollen ziehen.  
   - Am Stammfuss der West- und Ost-Bäume je eine Belegklampe in ca. 1,2 m Höhe mittels Spanngurt befestigen.

3. **Konfektionierung des Antennendrahts am Boden**

   - Zwei durchgehende Drahtstränge à 88,5 m ablängen  
     (2 × 44,0 m plus 0,5 m für Endschlaufen).  
   - Bei 44,25 m (Mitte) je einen Nord- bzw. Süd-Ei-Isolator einsetzen und dort das Dyneema-Zugseil anschlagen.  
   - Drahtenden:
     - im Westen an Zugentlastungsösen der West-Box befestigen und verlöten,  
     - im Osten an Ösen der Ost-Box befestigen und verlöten.  
   - Alle Lötstellen mit Schrumpfschlauch (mit Innenkleber) wetterfest versiegeln.

4. **Hochziehen und Spannen**

   - Zuerst West-Box (mit vormontierter FT240‑31-Drossel und Hyperflex 5) und Ost-Box hochziehen,  
     bis die Gehäuse jeweils ca. 3,0 m vor den Stämmen stehen.  
   - Dyneema-Seile auf den Klampen fest belegen (statische Endpunkte).  
   - Danach Nord- und Süd-Ecken über die Umlenkrollen hochziehen und die 9,5 kg-Gegengewichte inklusive Fangschlaufen einhängen.  
   - Der Rhombus spannt sich nun selbsttätig in die Sollgeometrie ein.

---

### 7.2 Abnahmemessung mit dem NanoVNA  
*(Messpunkt: Ende Hyperflex 5 im Rustico)*

| Prüfschritt              | Messbereich / Modus                   | Sollwert / Akzeptanzkriterium                                                                                                                     | Fehlerdiagnose bei Abweichung                                                                                                                            |
|--------------------------|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1. DC-Schleifentest      | Multimeter, R zwischen Innenleiter u. Schirm | 47 kΩ ± 5 %                                                                                                                                        | ∞ Ω: Unterbruch im Bleeder; \< 1 kΩ: Kurzschluss im Koax oder defekter GDT.                                                                               |
| 2. Breitband-SWR         | NanoVNA S11, SWR 3–30 MHz             | SWR ≤ 1,35:1 von 6,5–16,0 MHz, flacher Verlauf ohne scharfe Resonanzspitzen                                                                       | Starke periodische Welligkeit (SWR schwankt z. B. 1,1–2,5 im Abstand von Δf ≈ 300/(2·88 m) ≈ 1,7 MHz): → Unterbruch am 750 Ω-Abschluss im Osten.         |
| 3. Komplexe Impedanz     | NanoVNA S11, Smith bei 7,0 / 10,1 / 14,1 MHz | R = 42–58 Ω, \|X\| ≤ 12 Ω                                                                                                                           | Stark induktiv (+jX > 20 Ω) bei 14 MHz: Primärkondensator 82 pF in der West-Box prüfen (Wert, Lötstelle, Anschlusslänge).                                |
| 4. Rausch- & F/B-Test    | HL2 in Quisk / SparkSDR, z. B. 14,100 MHz (NCDXF-Baken) | Rauschanstieg beim Anstecken: +8 bis +10 dB; Baken aus Ost/Asien (4U1UN Long‑Path / JA / VR2 / UA0) +15 bis +25 dB stärker als West‑Signale | Kein merklicher Rauschanstieg: RX-Pfad J9 (RF2) in Software nicht aktiviert, falsche Eingangswahl, PTT-Mute-Relais hängt, oder BPF-Bank ist nicht korrekt geschaltet. |

---

*Ende des Leitfadens*
