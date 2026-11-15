# Einkaufsstückliste: Allband-Effizienz-System ($80\text{ m} - 10\text{ m}$) für Hermes Lite 2 ($5\text{ W}$)

* **Systemkonfiguration:** $2 \times 20.1\text{ m}$ Vollkupfer-Doublet + $17.6\text{ m}$ Luft-Hühnerleiter ($Z_0 \approx 600\text{ }\Omega$, Zero-Splice) + DIY Link-Coupled Balanced Tank Koppler ($Q_0 > 280$) + Gleichtakt-Isolation für den 12-Bit ADC (`AD9866`).
* **Hinweis zum Lieferumfang:** Trägermast (GFK-Mast) und Stand-/Auffahrfuss sind gemäss Vorgabe ausgenommen. Für die Endabspannung der beiden Strahlerflügel ist lediglich leichtes Dyneema-Seil aufgeführt.

---

## Baugruppe 1: Strahler, $600\text{ }\Omega$ Luft-Hühnerleiter & Endabspannung

| Pos. | Komponente | Technische Spezifikation | Menge | Bezugsquelle (CH / EU) | Einzelpreis | Gesamtpreis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1.1** | **Kupferlitze feindrähtig** (`H07V-K` schwarz) | $1.5\text{ mm}^2$ Vollkupfer, UV-stabil; für $2 \times 37.7\text{ m}$ durchgehende Führung ($20.1\text{ m}$ Strahler + $17.6\text{ m}$ Feed, $v_p = 0.97$) | $80\text{ m}$ | Distrelec.ch / Elektro CH | $0.55\text{ CHF}$ | $44.00\text{ CHF}$ |
| **1.2** | **Hühnerleiter-Spreizer ($85\text{ mm}$)** | POM-Delrin / GFK, Leiterabstand $85\text{ mm}$ ($Z_0 \approx 600\text{ }\Omega$), Montageabstand $40\text{ cm}$ | $50\text{ Stk.}$ | DX-Wire / Funkfachhandel | $0.40\text{ CHF}$ | $20.00\text{ CHF}$ |
| **1.3** | **PTFE-Isolatoren-Set** | 1x Center Insulator + 2x End-Isolatoren aus reinem PTFE ($\tan \delta \le 0.0002$), Zugentlastung | $1\text{ Set}$ | DX-Wire / Box73 | $24.00\text{ CHF}$ | $24.00\text{ CHF}$ |
| **1.4** | **Abspannseil Dyneema** (`Mastrant-P2`) | $\varnothing\text{ }2.0\text{ mm}$, Bruchlast $\ge 100\text{ daN}$, Dehnung $< 1.5\%$ (zur Abspannung der beiden Strahlerenden) | $30\text{ m}$ | DX-Wire / Mastrant | $0.45\text{ CHF}$ | $13.50\text{ CHF}$ |
| | **Zwischensumme Baugruppe 1** | | | | | **$101.50\text{ CHF}$** |

---

## Baugruppe 2: DIY Link-Coupled Balanced Tank Koppler ($Q_0 > 280$)

| Pos. | Komponente | Technische Spezifikation | Menge | Bezugsquelle (CH / EU) | Einzelpreis | Gesamtpreis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2.1** | **Luft-Doppeldrehkondensator (`C_tank`)** | $2 \times 250\text{ pF}$ bis $2 \times 320\text{ pF}$, Plattenabstand $\ge 0.5\text{ mm}$ ($> 500\text{ V}_{\text{peak}}$), Keramik-Isolation | $1\text{ Stk.}$ | Box73 / Funkflohmarkt | $28.00\text{ CHF}$ | $28.00\text{ CHF}$ |
| **2.2** | **Luft-Drehkondensator (`C_in`)** | $1 \times 500\text{ pF}$, kompensiert die Streuinduktivität der Primärkopplung auf $50.0\text{ }\Omega$ | $1\text{ Stk.}$ | Box73 / eBay | $18.00\text{ CHF}$ | $18.00\text{ CHF}$ |
| **2.3** | **Luftspulen-Material (`L2` & `L1`)** | $3.5\text{ m}$ Cu-Draht versilbert $\varnothing\text{ }1.5\text{ mm}$ ($24\text{ Wdg.}$, $\varnothing\text{ }45\text{ mm}$) + $1\text{ m}$ PTFE-Litze ($3\text{ Wdg.}$) + Acryl-Stege | $1\text{ Set}$ | Distrelec.ch / Box73 | $16.00\text{ CHF}$ | $16.00\text{ CHF}$ |
| **2.4** | **Gehäuse, Achsisolatoren & Klemmen** | Alu-Gehäuse ($200 \times 150 \times 80\text{ mm}$), 2x Delrin-Achsverlängerung ($25\text{ mm}$), 2x Ag-Abgriffklemmen, 4x Polklemmen | $1\text{ Set}$ | Distrelec.ch / AliExpress | $34.00\text{ CHF}$ | $34.00\text{ CHF}$ |
| **2.5** | **ESD-Ableitwiderstände** | Kohlemasse- oder Metalloxid-Widerstand $100\text{ k}\Omega / 2\text{ W}$ (induktionsarm, gegen Erdbuchse) | $2\text{ Stk.}$ | Distrelec.ch | $1.50\text{ CHF}$ | $3.00\text{ CHF}$ |
| | **Zwischensumme Baugruppe 2** | | | | | **$99.00\text{ CHF}$** |

---

## Baugruppe 3: Transceiver-Anbindung & Gleichtakt-Isolation (HL2-Schutz)

| Pos. | Komponente | Technische Spezifikation | Menge | Bezugsquelle (CH / EU) | Einzelpreis | Gesamtpreis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **3.1** | **Koax-Patchkabel RG-400 (PTFE)** | $1.5\text{ m}$, doppelt versilbert, SMA-Male (HL2) auf BNC-Male (Koppler), Dämpfung $< 0.08\text{ dB}$ | $1\text{ Stk.}$ | AliExpress / Kabel-Kusch | $14.00\text{ CHF}$ | $14.00\text{ CHF}$ |
| **3.2** | **1:1 Guanella-Strombalun** | Ferritkern **Fair-Rite `2631803802` (FT240-31)** + $12\text{ Wdg.}$ RG-400 ($Z_{\text{cm}} > 4.2\text{ k}\Omega$) | $1\text{ Stk.}$ | Distrelec.ch / Box73 | $18.00\text{ CHF}$ | $18.00\text{ CHF}$ |
| **3.3** | **Statik-Erdungsspiess + Masseband** | Cu-beschichteter Stahlspiess ($40\text{ cm}$) + $3\text{ m}$ Masseleitung (nur für $100\text{ k}\Omega$-Bleeder) | $1\text{ Set}$ | Bauhaus CH / Elektro CH | $15.00\text{ CHF}$ | $15.00\text{ CHF}$ |
| | **Zwischensumme Baugruppe 3** | | | | | **$47.00\text{ CHF}$** |

---

## Gesamtkosten-Übersicht

| Baugruppe | Beschreibung | Summe (CHF) |
| :--- | :--- | :--- |
| **Baugruppe 1** | Strahler, $600\text{ }\Omega$ Luft-Hühnerleiter & Endabspannung | $101.50\text{ CHF}$ |
| **Baugruppe 2** | DIY Link-Coupled Balanced Tank Koppler | $99.00\text{ CHF}$ |
| **Baugruppe 3** | Transceiver-Anbindung & Gleichtakt-Isolation | $47.00\text{ CHF}$ |
| **Total** | **Gesamtkosten Referenz-Setup (ohne Mast & Fuss)** | **$247.50\text{ CHF}$** |

---

## Zuschnitt- & Aufbau-Checkliste

* [ ] **Zero-Splice Zuschnitt:** Die $80\text{ m}$ Kupferlitze in zwei exakt gleich lange Stücke à **$37.7\text{ m}$** schneiden. Jeweils **$20.1\text{ m}$** bilden einen horizontalen/Inverted-V Strahlerflügel, die verbleibenden **$17.6\text{ m}$** laufen ohne Unterbrechung oder Lötstelle durch den PTFE-Center-Insulator als Paralleldrahtleitung nach unten.
* [ ] **Spreizer-Montage:** Die POM/GFK-Spreizer im Abstand von $40\text{ cm}$ über die gesamte Länge von $17.6\text{ m}$ aufclipsen (ergibt $Z_0 \approx 600\text{ }\Omega$ bei $v_p = 0.97$).
* [ ] **Luftspulen-Wicklung (`L2` / `L1`):** Sekundärspule `L2` mit $24\text{ Windungen}$ ($\varnothing\text{ }45\text{ mm}$, $L \approx 16.5\text{ }\mu\text{H}$) wickeln und bei Windung $12$ die exakte Mittelanzapfung über die beiden $100\text{ k}\Omega / 2\text{ W}$ ESD-Widerstände an die Erdbuchse führen. Primäre Koppelspule `L1` ($3\text{ Windungen}$) mittig darüber anordnen.
* [ ] **Rotor-Isolation:** Beide Drehkondensatoren (`C_tank` und `C_in`) über die $25\text{ mm}$ Delrin-Isolierkupplungen an die Frontplatten-Drehknöpfe führen, um Handkapazitäten und Asymmetrien zu verhindern.
* [ ] **Import-Freigrenze (CH / BAZG):** Bei Auslandsbestellungen (DX-Wire, Box73, AliExpress) Warenwert inkl. Versand unter **$61.70\text{ CHF}$** pro Einzelsendung halten, damit der MWST-Betrag ($8.1\%$) unter der Freigrenze von $5.00\text{ CHF}$ bleibt und keine Zollvorweisungstaxen anfallen.
