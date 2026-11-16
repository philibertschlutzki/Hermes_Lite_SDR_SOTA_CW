Terminated Rhombic RX-Antenne (40m / 30m / 20m) – Engineering & Integrationsleitfaden
Systemarchitektur: Monodirektionale Wanderwellen-Empfangsantenne (Terminated Rhombic)
Zielbänder: 40m (7{,}0\text{–}7{,}2\,\text{MHz}), 30m (10{,}10\text{–}10{,}15\,\text{MHz}), 20m (14{,}0\text{–}14{,}35\,\text{MHz})
SDR-Frontend: Hermes-Lite 2 (HL2, AD9866 12-Bit ADC) + N2ADR Filter-Board + RP2040 IO-Board
Standort: LV95 2'685'931.37, 1'152'055.87 (1528\,\text{m} ü. M., alpiner Nadelwald / Lichtung)
1. Physikalische Auslegung & Standortparameter
1.1 Richtwirkung und 3D-Hanggeometrie
 * Wanderwellen-Prinzip (Hauptstrahlrichtung): Der Empfangsgewinn entsteht durch phasenrichtige Aufsummierung der entlang der Drähte laufenden Welle in Richtung des Speisepunkts, während Wellen aus der Gegenrichtung im Abschlusswiderstand in Wärme umgesetzt werden.
   * Speisepunkt (Feedpoint): Westsüdwest (255^\circ\text{–}260^\circ)
   * Abschlusspunkt (Termination): Ostnordost (75^\circ\text{–}80^\circ)
   * Resultierender Hauptempfangsvektor (Main Lobe): 75^\circ\text{–}80^\circ (Ostnordost – Osteuropa, Zentralasien, Japan/Fernost).
   * Rückdämpfung (Nullstelle): 255^\circ\text{–}260^\circ (Westsüdwest).
 * Entkopplung von Quer- und Längsneigung am Nordhang:
   Da das Gelände bei LV95 2'685'931.37, 1'152'055.87 nach Nordnordwest (\text{Azimut} \approx 350^\circ) abfällt, erzeugt eine Montage entlang der Höhenlinie (75^\circ\text{–}80^\circ) bei konstanter Masthöhe über Grund lediglich eine Querneigung (Roll) der Antennenebene nach Norden, jedoch keine Absenkung des Erhebungswinkels in Hauptstrahlrichtung.
 * Gezielte Pitch-Neigung (Längsgefälle in Strahlrichtung):
   Um den vertikalen Erhebungswinkel (\Delta) in Richtung Ostnordost real um \beta_{\text{pitch}} \approx -4{,}3^\circ abzusenken und gleichzeitig den Wellenwiderstand (Z_0 \approx 750\,\Omega) über dem Boden konstant zu halten, wird die Aufhängung gestaffelt:
   * West-Anker (Speisepunkt): 15{,}5\text{–}16{,}0\,\text{m} über Waldboden
   * Nord-/Süd-Anker (Seiten-Apices): 12{,}5\text{–}13{,}0\,\text{m} über Waldboden
   * Ost-Anker (Abschlusspunkt): 9{,}5\text{–}10{,}0\,\text{m} über Waldboden
1.2 Elektromagnetische 3D-Phasenbilanz (L = 44\,\text{m}, \phi = 65^\circ, \overline{H} = 13\,\text{m})
Über trockenem alpinem Fels-/Waldboden (\sigma \approx 10^{-3}\,\text{S/m}, \varepsilon_r \approx 5) überlagern sich der Phasenwinkel des Einzelschenkels \cos(\theta_0) = 1 - \frac{0{,}371 \cdot \lambda}{L} (mit \cos(\theta_0) = \cos(\Delta_{\text{wire}}) \cdot \sin(\phi)) und der erste vertikale Bodenreflexionszipfel \Delta_{\text{ground}} = \arcsin\left(\frac{\lambda}{4\overline{H}}\right) wie folgt:
| Parameter | 40m-Band (7{,}05\,\text{MHz}) | 30m-Band (10{,}12\,\text{MHz}) | 20m-Band (14{,}05\,\text{MHz}) |
|---|---|---|---|
| Wellenlänge (\lambda) | 42{,}52\,\text{m} | 29{,}62\,\text{m} | 21{,}34\,\text{m} |
| Elektrische Schenkellänge (L/\lambda) | 1{,}03\,\lambda | 1{,}49\,\lambda | 2{,}06\,\lambda |
| Drahtkegel-Winkel (\theta_0) | 50{,}1^\circ | 41{,}4^\circ | 34{,}9^\circ |
| Phasen-Elevation (\Delta_{\text{wire}} bei \phi = 65^\circ) | 45{,}0^\circ | 34{,}2^\circ | 24{,}8^\circ |
| Boden-Elevation (\Delta_{\text{ground}} bei \overline{H} = 13\,\text{m}) | 54{,}9^\circ | 34{,}8^\circ | 24{,}2^\circ |
| Effektiver Abstrahlwinkel inkl. -4{,}3^\circ Pitch | 43^\circ\text{–}48^\circ | 30{,}2^\circ | 20{,}2^\circ |
| Richtgewinn (dBi, inkl. Terminierungsverlust) | \approx 7{,}5\,\text{dBi} | \approx 10{,}2\,\text{dBi} | \approx 12{,}5\,\text{dBi} |
| Vor-Rück-Verhältnis (F/B Ratio, kompensiert) | \approx 18\,\text{dB} | \approx 24\,\text{dB} | \approx 26\,\text{dB} |
| Horizontale Halbwertsbreite (-3\,\text{dB} Azimut) | \approx 32^\circ | \approx 22^\circ | \approx 16^\circ |
2. Geometrie, Trigonometrie & Vermessung
                           [NORD-ANKER]
                         (12,5-13,0m Höhe)
                         Umlenkrolle + 9,5 kg
                                /\
                               /  \
                Schenkel 1    /    \    Schenkel 2
                 L = 44,0m   / 130° \    L = 44,0m
                            / (2*phi)\
                           /          \
   [WEST-ANKER: FEED]     /     ^      \     [OST-ANKER: TERM]
   (15,5-16,0m Höhe)     < 50°  | 37,2m >    (9,5-10,0m Höhe)
   Statisch auf Klampe    \     v      /     Statisch auf Klampe
   (Haltekraft ~20,3 kgf)  \          /      (Haltekraft ~20,3 kgf)
                            \  130°  /
                Schenkel 4   \      /   Schenkel 3
                 L = 44,0m    \    /     L = 44,0m
                               \  /
                                \/
                           [SÜD-ANKER]
                         (12,5-13,0m Höhe)
                         Umlenkrolle + 9,5 kg

   |<---------------- Draht-Längsachse: 79,75 m --------------->|
   |<--- +3,0m --->|                             |<--- +3,0m --->|
   |<------------- Baum-Ankerabstand Ost-West: 85,75 m --------->|

2.1 Massvorgaben für L = 44{,}0\,\text{m} (Regelausbau) und L = 38{,}0\,\text{m} (Kompaktvariante)
Um dielektrische Zusatzverluste und Verstimmungen durch nasses Nadelholz oder Schneebehang zu verhindern, müssen die vier Eckisolatoren mittels Dyneema-Vorlaufseilen mindestens 3{,}0\,\text{m} frei vor den Stämmen und Ästen schweben.
| Geometrie-Parameter | Formel | Regelausbau (L = 44{,}0\,\text{m}) | Kompaktvariante (L = 38{,}0\,\text{m}) |
|---|---|---|---|
| Halber Stumpfwinkel (\phi) | Vorgabe | 65{,}0^\circ (2\phi = 130^\circ) | 65{,}0^\circ (2\phi = 130^\circ) |
| Halber Spitzwinkel (\alpha) | 90^\circ - \phi | 25{,}0^\circ (2\alpha = 50^\circ) | 25{,}0^\circ (2\alpha = 50^\circ) |
| Schenkellänge (L) | Vorgabe | 44{,}00\,\text{m} | 38{,}00\,\text{m} |
| Gesamtdrahtlänge (4 \times L) | 4 \cdot L + 1{,}0\,\text{m} Zugabe | 177{,}00\,\text{m} | 153{,}00\,\text{m} |
| Draht-Längsdiagonale (D_{\text{long}}) | 2 \cdot L \cdot \sin(65^\circ) | 79{,}75\,\text{m} | 68{,}88\,\text{m} |
| Draht-Querdiagonale (D_{\text{trans}}) | 2 \cdot L \cdot \cos(65^\circ) | 37{,}19\,\text{m} | 32{,}12\,\text{m} |
| Min. Baumabstand Ost–West (D_{\text{Baum, long}}) | D_{\text{long}} + 2 \cdot 3{,}0\,\text{m} | 85{,}75\,\text{m} | 74{,}88\,\text{m} |
| Min. Baumabstand Nord–Süd (D_{\text{Baum, trans}}) | D_{\text{trans}} + 2 \cdot 3{,}0\,\text{m} | 43{,}19\,\text{m} | 38{,}12\,\text{m} |
3. Stückliste (Bill of Materials – BOM)
| Pos. | Baugruppe | Komponente / Spezifikation | Menge | Richtpreis (CHF) |
|---|---|---|---|---|
| 1.1 | Strahler & Seile | Kupfer-Stahl-Litze (Copperweld / DX-Wire UL oder FL, \varnothing\,1{,}5\text{–}1{,}8\,\text{mm}, UV-PE-Mantel, Bruchlast \ge 60\,\text{daN}) | 180\,\text{m} | 95.00 |
| 1.2 |  | Dyneema SK78 Geflechtseil (\varnothing\,3{,}0\,\text{mm}, Bruchlast 950\,\text{daN}, Reck \lt 1\,\%, schwarz UV-stabilisiert) | 120\,\text{m} | 78.00 |
| 1.3 |  | Keramik- oder PTFE-Ei-Isolatoren (Bruchlast \ge 150\,\text{daN}) für Nord-/Süd-Ecken | 4\,\text{Stk.} | 16.00 |
| 2.1 | Mechanik (4 Bäume) | Baumschoner-Rundschlingen (Polyester, 2\,\text{m} Umfang, 1000\,\text{daN}, grün/schwarz) | 4\,\text{Stk.} | 36.00 |
| 2.2 |  | Edelstahl-Blockseilrollen (V4A / AISI 316, kugelgelagert, für 4\text{–}6\,\text{mm} Seil) + V4A-Schäkel | 6\,\text{Stk.} | 54.00 |
| 2.3 |  | Edelstahl-Belegklampen (150\,\text{mm}, auf Montageplatte mit Spanngurt am Stammfuss West & Ost) | 2\,\text{Stk.} | 28.00 |
| 2.4 |  | Gegengewichte nur für Nord & Süd (z. B. mit Kies/Blei gefüllte PE-Rohre, exakt 9{,}5\,\text{kg} je Seite) | 2\,\text{Stk.} | 25.00 |
| 3.1 | West-Box (Feed) | Gehäuse Fibox ARCA / Bopla Polycarbonat IP67 (120 \times 80 \times 60\,\text{mm}) + M12-Druckausgleichsmembran | 1\,\text{Stk.} | 24.00 |
| 3.2 |  | Doppellochkern Fair-Rite 2861000202 (Material 61, bevorzugt) oder 2843000202 (Material 43) | 1\,\text{Stk.} | 8.50 |
| 3.3 |  | PTFE-Wickeldraht AWG 22 (\varnothing\,0{,}65\,\text{mm}, versilbert) für 2:8 Wdg. (Mittenanzapfung bei Wdg. 4) | 1{,}5\,\text{m} | 3.00 |
| 3.4 |  | Kompensationskondensator 82\,\text{pF} (C0G/NP0, 500\,\text{V}) parallel zur Primärwicklung | 1\,\text{Stk.} | 1.20 |
| 3.5 |  | Bleeder-/Schutznetzwerk: 1 \times 47\,\text{k}\Omega / 2\,\text{W} Metalloxid + Bourns 90\,\text{V} GDT (2093-90-SM / bedrahtet) | 1\,\text{Set} | 4.50 |
| 3.6 |  | Mantelwellensperre: Ringkern Fair-Rite FT240-31 + 1{,}6\,\text{m} RG-400 PTFE-Koax + 2x BNC/N-Stecker | 1\,\text{Set} | 32.00 |
| 4.1 | Ost-Box (Term) | Gehäuse Polycarbonat IP67 (120 \times 80 \times 60\,\text{mm}) + M12-Druckausgleichsmembran + V4A-Augenschrauben | 1\,\text{Stk.} | 24.00 |
| 4.2 |  | Abschluss-Array: 4 \times 3{,}0\,\text{k}\Omega / 2\,\text{W} induktionsarme Metalloxid-/Schichtwiderstände (parallel = 750\,\Omega) | 4\,\text{Stk.} | 4.00 |
| 4.3 |  | Kompensationskondensator 12\,\text{pF} (Glimmer / Silver Mica oder C0G/NP0, 500\,\text{V}) parallel zu 750\,\Omega | 1\,\text{Stk.} | 2.50 |
| 5.1 | Zuleitung & HL2 | Koaxkabel Messi & Paoloni Hyperflex 5 (\varnothing\,5{,}4\,\text{mm}, Litzen-Innenleiter, doppelt geschirmt) | 50\,\text{m} | 85.00 |
| 5.2 |  | Blitzschutz am Gebäudeeintritt: Koax-Überspannungsableiter (GDT 90\,\text{V}, z. B. Diamond SP-1000) | 1\,\text{Stk.} | 42.00 |
| 5.3 |  | Monoband-BPF-Bank (40m / 30m / 20m, 3-Pol T50-6 / C0G) geschaltet via N2ADR IO-Board + BAV99 Limiter | 1\,\text{Einheit} | 65.00 |
4. Seilstatik & Mechanische Installation (1528\,\text{m} ü. M.)
4.1 Kräftegleichgewicht der Rhombus-Geometrie
Damit sich die Winkel 2\alpha = 50^\circ (West/Ost) und 2\phi = 130^\circ (Nord/Süd) unter Zug nicht verziehen, muss das Verhältnis der Haltekräfte an den Ecken exakt dem Kosinusverhältnis der Halbwinkel entsprechen:
Für eine definierte Drahtvorspannung von T_{\text{wire}} = 110\,\text{N} (11{,}2\,\text{kgf}) pro Schenkel (Durchhang trocken f = \frac{0{,}20\,\text{N/m} \cdot (44\,\text{m})^2}{8 \cdot 110\,\text{N}} = 0{,}44\,\text{m}) gilt folgendes Montagekonzept:
 * West- und Ost-Ecke (Statische Festpunkte mit Wartungsabsenkung):
   * An den Bäumen im Westen (15{,}5\text{–}16{,}0\,\text{m} Höhe) und Osten (9{,}5\text{–}10{,}0\,\text{m} Höhe) wird das Dyneema-Seil über je eine Umlenkrolle nach unten zu einer Belegklampe am Stammfuss geführt.
   * Keine Gegengewichte an West und Ost verwenden: Die beiden Endpunkte werden nach dem Hochziehen fest auf den Klampen belegt (statische Zuglast an der Klampe: F_{\text{West/Ost}} = 1{,}813 \cdot 110\,\text{N} \approx 200\,\text{N} bzw. 20{,}3\,\text{kgf}). Dadurch bleiben Speisepunkt (inkl. Koaxkabel-Gewicht) und Abschlusspunkt räumlich fixiert und lassen sich für Wartungsarbeiten jederzeit vom Boden aus ablassen.
 * Nord- und Süd-Ecke (Dynamischer Lastausgleich über Gegengewichte):
   * An den Bäumen im Norden und Süden (12{,}5\text{–}13{,}0\,\text{m} Höhe) läuft das Dyneema-Seil über die Umlenkrolle zu je einem frei hängenden Gegengewicht von 9{,}5\text{–}10{,}0\,\text{kg} (F_{\text{Nord/Süd}} = 0{,}845 \cdot 110\,\text{N} = 93\,\text{N} \approx \mathbf{9{,}5\,\text{kgf}}).
   * Da alle vier Drahtschenkel an den Nord-/Süd-Isolatoren durchlaufend bzw. kraftschlüssig gekoppelt sind, regeln diese beiden Seitengewichte die Drahtspannung im gesamten Rhombus exakt auf 110\,\text{N} ein.
 * Schneelast-Fangschlaufe (Fail-Safe Stop):
   * Die Gegengewichte im Norden und Süden auf ca. 3{,}5\,\text{m} Höhe über dem Boden einhängen.
   * 1{,}2\,\text{m} oberhalb der Ruheposition des Gewichts einen Achterknoten mit Sicherheitskarabiner in eine feste Fangschlaufe am Stamm setzen: Bei extremem Nassschnee oder Eisregen wandert das Gewicht maximal 1{,}2\,\text{m} nach oben (gibt ca. 1{,}0\,\text{m} Draht nach, senkt die Spitzenzugkraft) und geht danach in den statischen Anschlag über, bevor die Eckisolatoren an die oberen Umlenkrollen gezogen werden.
5. HF-Systemdesign & Schaltungsaufbau
5.1 Gesamtschaltbild (West-Box & Ost-Box)
=======================================================================================
WEST-BOX (Speisepunkt, IP67)                                OST-BOX (Abschluss, IP67)
=======================================================================================

                               Schenkel 1 + 2 (Nord, 88,0m)
          +--------------------/\/\/\-----------------------+
          |                                                 |
   +------+------+                                   +------+------+
   |             |                                   |             |
   |  4 Wdg.     | Fair-Rite                         |   4x 3,0k   |  Parallel = 750 Ohm
   |   )  ||     | 2861000202                        |   (2W MOX)  |  (8W induktionsarm)
   |   )  ||  (  +---o--+---[ 82pF ]---+---o BNC     |      ||     |
   |   )  ||  (  |      |              |   (50 Ohm)  |   [ 12pF ]  |  Kompensation 20m
   |   )  ||  (  |      |   2 Wdg.     |             |  (NP0 500V) |
   +--o---+      |      +--------------+             |             |
   |  |   ||  (  |                     |             |  Komplett   |
   |  |   ||     |                     |             |  erdfrei!   |
   |  | 4 Wdg.   |                     |             | (floating)  |
   +--+---+------+                     |             +------+------+
      |   |                            |                    |
      |   +--------------------+-------+                    |
      |                        |    Schenkel 3 + 4 (Süd)    |
      |                        +-------/\/\/\---------------+
      |
      +---[ 47 kOhm / 2W ]-----+
      |                        |
      +---[ 90V GDT Bourns ]---+---> Auf BNC-Masse (Koax-Schirm VOR Mantelwellensperre)
 (Symmetrie-Mittenanzapfung)
                               |
                        [BNC-Durchführung]
                               |
                        (10 Wdg. RG-400 Crossover auf FT240-31)
                               |
                        [Zugentlastung am Stamm]
                               |
                        (50m Hyperflex 5 zum Rustico)
=======================================================================================

5.2 Fertigung der West-Box (Speisepunkt & Elektrostatik-Ableitung)
 * Impedanzübertrager (16:1 \implies 50\,\Omega \text{ auf } 800\,\Omega):
   * Ein Einzeldraht-Rhombus (\varnothing\,1{,}6\,\text{mm}) auf 13\,\text{m} Höhe besitzt einen mittleren Wellenwiderstand von Z_0 \approx 750\,\Omega.
   * Auf den Doppellochkern Fair-Rite 2861000202 (Material 61, geringere Kernverluste oberhalb 10\,\text{MHz}) oder 2843000202 (Material 43) zunächst die Primärwicklung mit N_p = 2\,\text{Windungen} PTFE-Draht wickeln.
   * Getrennt davon die Sekundärwicklung mit N_s = 8\,\text{Windungen} einbringen (n^2 = (8/2)^2 = 16 \implies Z_{\text{sec}} = 800\,\Omega, ergibt gegenüber 750\,\Omega ein ideales \text{SWR} = 1{,}06).
   * Exakt nach der 4. Sekundärwindung eine Mittenanzapfung herausführen (elektrischer Nullpunkt für symmetrische HF-Spannungen).
   * Direkt über die Primäranschlüsse (BNC-Innenseite) einen 82\,\text{pF} C0G/NP0-Kondensator (500\,\text{V}) löten, um die Streuinduktivität des Kerns auf dem 20m-Band zu kompensieren.
 * Elektrostatische Ableitung (Precipitation Static Bleeder):
   * Da die beiden Antennenschenkel im Osten über den 750\,\Omega-Abschlusswiderstand gleichstrommässig verbunden sind, bildet der gesamte Rhombus eine geschlossene DC-Schleife.
   * Die Mittenanzapfung (Windung 4) der Sekundärwicklung wird über die Parallelschaltung aus einem 47\,\text{k}\Omega / 2\,\text{W} Metalloxid-Widerstand und einem 90\,\text{V} Gasentladungsableiter (GDT) mit der Masse der BNC-Buchse (Koax-Schirm) verbunden.
   * Wirkprinzip: Statische Ladungen durch Höhenwind, Graupel oder trockenen Pulverschnee fliessen kontinuierlich und symmetrisch über den 47\,\text{k}\Omega-Widerstand auf den im Rustico geerdeten Koax-Schirm ab. Für die HF-Signale liegt die Mittenanzapfung im Spannungsnullpunkt (virtuelle Masse), sodass die galvanische Trennung zwischen Antenne und Koaxkabel zu 100\,\% erhalten bleibt.
5.3 Fertigung der Mantelwellensperre (FT240-31)
 * Unmittelbar unterhalb der West-Box werden 10 Windungen RG-400 PTFE-Koaxkabel auf einen Fair-Rite FT240-31 Ringkern gewickelt.
 * Wickelschema (Reisert-Crossover): 5 Windungen auf einer Kernhälfte wickeln, das Kabel diagonal durch die Kernmitte auf die gegenüberliegende Seite führen und weitere 5 Windungen in Gegenrichtung aufbringen.
 * Dies halbiert die parasitäre Durchgangskapazität zwischen Ein- und Ausgang, legt die Eigenresonanz (SRF) exakt auf ca. 10{,}5\,\text{MHz} (30m-Band) und garantiert eine rein resistive Gleichtakt-Sperrimpedanz von Z_{\text{cm}} \gt 4{,}0\,\text{k}\Omega von 7{,}0\text{ bis }14{,}35\,\text{MHz}.
 * Mechanische Entlastung: Das abgehende Hyperflex 5 Koaxkabel 1{,}5\,\text{m} unterhalb der Drossel mit einer gummierten Kabelschelle am tragenden Abspannseil abfangen, damit kein Kabelgewicht am Stecker oder Ringkern zieht.
5.4 Fertigung der Ost-Box (Kompensierter 750\,\Omega-Abschluss)
 * Vollständige Erdfreiheit: Im Ost-Gehäuse werden keinerlei Erdleitungen, GDTs oder Bleeder gegen Boden angeschlossen. Eine vertikale Erdleitung am östlichen Ende würde als 10\,\text{m} lange Vertikalantenne in den Abschlusswiderstand einkoppeln und die Rückdämpfung zerstören.
 * Widerstands-Array: Vier identische, ungewendelte 3{,}0\,\text{k}\Omega / 2\,\text{W} Metalloxid- oder Dickschichtwiderstände eng nebeneinander mit minimaler Anschlussdrahtlänge parallel schalten (R_{\text{ges}} = 750\,\Omega, Belastbarkeit 8\,\text{W}, ein Viertel der parasitären Serieninduktivität eines Einzelwiderstands).
 * Blindwiderstands-Kompensation: Parallel zur Widerstandsgruppe einen 12\,\text{pF} Glimmer- oder C0G/NP0-Kondensator (500\,\text{V}) einlöten. Dieser kompensiert den induktiven Blindanteil der spitz zulaufenden Antennenenden (2\alpha = 50^\circ) auf 30m und 20m und vertieft die Rückwärts-Nullstelle um 6\text{ bis }10\,\text{dB}.
6. Zuleitung, Blitzschutz & Hermes-Lite 2 (HL2) Integration
6.1 Koax-Zuleitung und Gebäudeeintritt (NIN / SEV 1000)
 * Kabeltyp: Durchgehend Messi & Paoloni Hyperflex 5 verwenden. Aufgrund des flexibel verseilten Litzen-Innenleiters (19 \times 0{,}28\,\text{mm}) bricht der Leiter bei windbedingter Bewegung an der West-Aufhängung nicht. Die Kabeldämpfung von ca. 2{,}8\,\text{dB} auf 50\,\text{m} bei 14\,\text{MHz} hat keinerlei negativen Einfluss auf das Empfänger-SNR, da das externe atmosphärische Rauschen (F_{\text{am}}) am Richt-Rhombus um mehr als 25\,\text{dB} über dem thermischen Rauschflur liegt.
 * Potentialausgleich: Am Gebäudeeintritt ins Rustico einen koaxialen Überspannungsableiter (90\,\text{V} GDT) installieren und dessen Gehäuse mit mindestens 6\,\text{mm}^2 Kupfer direkt auf die Potentialausgleichsschiene legen.
6.2 HL2-Signalkette, Preselektion und TX/RX-Koexistenz
[Hyperflex 5 vom Rhombus]
        |
        v
+-----------------------+
| Koax-Blitzschutz GDT  |===> Potentialausgleichsschiene (6 mm² Cu)
+-----------------------+
        |
        v
+-----------------------+
| TX-Mute Relais +      | <--- PTT-Steuersignal vom N2ADR-Board
| BAV99 Dioden-Limiter  |      (schliesst RX-Eingang bei TX auf Masse kurz)
+-----------------------+
        |
        v
+-----------------------+
| Monoband-BPF Bank     | <--- Bandwahl via RP2040 / N2ADR IO-Board
| (40m / 30m / 20m)     |      (Unterdrückung 41m/31m BC-Sender > 45 dB)
+-----------------------+
        |
        v
[HL2 J9 (RF2) Dedizierter RX-Eingang] (Umgeht N2ADR TX-Tiefpassfilter)

 * Nutzung des dedizierten RX-Eingangs J9 (RF2):
   Den Rhombus auf dem Hermes-Lite 2 Mainboard am separaten Empfangseingang J9 (RF2) anschliessen (Jumper auf RF2 setzen). Dadurch läuft das Empfangssignal nicht über die Sende-Tiefpassfilter des N2ADR-Boards, während eine separate Sendeantenne (z. B. 2 \times 20{,}1\,\text{m} Doublet) fest an der N2ADR-Hauptbuchse verbleiben kann.
 * Zwingender TX-Überspannungsschutz bei Mehrantennenbetrieb:
   Wird auf dem Grundstück mit 5\,\text{W} über eine separate Sendeantenne gesendet, koppelt der 176\,\text{m} lange Rhombus im Nahfeld hohe HF-Spannungen (\gt +20\,\text{dBm}) ein. Unmittelbar vor der Bandpassfilter-Bank ein PTT-gesteuertes Kleinleistungsrelais (legt den RX-Pfad während PTT = aktiv auf Masse) sowie einen antiparallelen Dioden-Begrenzer (BAV99 oder 2 \times \text{1N4148} gegen Masse, Schwellspannung \pm 0{,}7\,\text{V} \approx +7\,\text{dBm}) vorsehen.
 * AD9866 LNA Gain-Staging (Vermeidung von ADC-Clipping):
   Den internen LNA des AD9866 in Quisk / SparkSDR / Thetis pro Band so kalibrieren, dass der Grundrauschpegel beim Umschalten von einem 50\,\Omega-Abschlusswiderstand auf die Rhombus-Antenne um exakt 8\text{ bis }10\,\text{dB} ansteigt:
| Band | Frequenzbereich | BPF-Status (RP2040 IO) | Zielwert HL2 LNA-Gain | Resultierender MDS (500\,\text{Hz} CW) | Nutzbarer BDR am AD9866 |
|---|---|---|---|---|---|
| 40m | 7{,}00\text{–}7{,}20\,\text{MHz} | 40m-BPF aktiv | -3 dB bis 0 dB | \approx -113\text{ bis }-116\,\text{dBm} | 100\text{–}102\,\text{dB} |
| 30m | 10{,}10\text{–}10{,}15\,\text{MHz} | 30m-BPF aktiv | 0 dB bis +3 dB | \approx -116\text{ bis }-119\,\text{dBm} | 97\text{–}99\,\text{dB} |
| 20m | 14{,}00\text{–}14{,}35\,\text{MHz} | 20m-BPF aktiv | +3 dB bis +6 dB | \approx -119\text{ bis }-122\,\text{dBm} | 94\text{–}96\,\text{dB} |
7. Montageablauf & VNA-Inbetriebnahmeprotokoll
7.1 Schritt-für-Schritt-Aufbau im Gelände
 * Laser-Distanz- und Kompass-Vermessung:
   * Vom Zentrum der Lichtung mit Kompass (Deklination Schweiz 2026: ca. +3{,}0^\circ Ost berücksichtigen) und Laser-Entfernungsmesser die Längsachse (75^\circ\text{–}80^\circ / 255^\circ\text{–}260^\circ, Baumabstand \ge 85{,}8\,\text{m}) und die senkrecht dazu stehende Querachse (165^\circ\text{–}170^\circ / 345^\circ\text{–}350^\circ, Baumabstand \ge 43{,}2\,\text{m}) markieren.
 * Anschlagen der Rollen und Klampen:
   * Baumschoner-Gurte und V4A-Rollen an den vier Bäumen auf den gestaffelten Zielhöhen (West 15{,}5\,\text{m}, Nord/Süd 12{,}8\,\text{m}, Ost 9{,}8\,\text{m}) montieren; Hilfsleinen durchziehen.
   * Am Stammfuss des West- und Ost-Baums je eine Belegklampe auf 1{,}2\,\text{m} Griffhöhe mit Spanngurt befestigen.
 * Konfektionierung des Antennendrahts am Boden:
   * Zwei durchgehende Drahtstränge à 88{,}5\,\text{m} (2 \times 44{,}0\,\text{m} plus 0{,}5\,\text{m} für Endschlaufen) ablängen.
   * Exakt bei der Mittelmarkierung (44{,}25\,\text{m}) jedes Drahts den Nord- bzw. Süd-Ei-Isolator einbinden und dort das Dyneema-Zugseil anschlagen.
   * Die Drahtenden im Westen an die Zugentlastungs-Ösen der West-Box und im Osten an die Ösen der Ost-Box klemmen und elektrisch verlöten (Schrumpfschlauch mit Innenkleber).
 * Hochziehen und Spannen:
   * Zuerst West-Box (inkl. vormontierter FT240-31-Drossel und Hyperflex 5) und Ost-Box hochziehen, bis die Gehäuse exakt 3{,}0\,\text{m} vor den Stämmen schweben; Seile auf den Klampen fest belegen.
   * Danach die Nord- und Süd-Ecken über die Umlenkrollen hochziehen und die 9{,}5\,\text{kg}-Gegengewichte inkl. Fangschlaufen einhängen. Der Rhombus spannt sich nun selbsttätig auf seine Sollgeometrie.
7.2 Abnahmemessung mit dem NanoVNA (am Ende des Hyperflex 5 im Rustico)
| Prüfschritt | Messbereich / Modus | Sollwert / Akzeptanzkriterium | Fehlerdiagnose bei Abweichung |
|---|---|---|---|
| 1. DC-Schleifentest | Multimeter (Widerstand Innenleiter gegen Schirm) | 47\,\text{k}\Omega \pm 5\,\% | \infty\,\Omega: Unterbruch im Bleeder; \lt 1\,\text{k}\Omega: Kurzschluss im Koax oder GDT defekt. |
| 2. Breitband-SWR | NanoVNA S11 SWR (3{,}0\text{–}30{,}0\,\text{MHz}) | \text{SWR} \le 1{,}35 : 1 durchgehend von 6{,}5\text{ bis }16{,}0\,\text{MHz} (flacher Verlauf ohne steile Resonanzspitzen) | Starke periodische Welligkeit (\text{SWR} schwankt zwischen 1{,}1 und 2{,}5 im Abstand von \Delta f \approx \frac{300}{2 \cdot 88\,\text{m}} \approx 1{,}7\,\text{MHz}): Unterbruch am östlichen 750\,\Omega-Abschlusswiderstand! |
| 3. Komplexe Impedanz | NanoVNA S11 Smith (7{,}0 / 10{,}1 / 14{,}1\,\text{MHz}) | R = 42\text{–}58\,\Omega, Blindanteil \vert{}X\vert{} \le 12\,\Omega | Stark induktiv (+jX \gt 20\,\Omega) bei 14\,\text{MHz}: 82\,\text{pF} Primärkondensator in West-Box prüfen. |
| 4. Rausch- & F/B-Test | HL2 in Quisk / SparkSDR (14{,}100\,\text{MHz} NCDXF-Baken) | Rauschanstieg beim Anstecken: +8\text{ bis }+10\,\text{dB}; Baken aus Ost/Asien (4U1UN Long-Path / JA / VR2 / UA0) +15\text{ bis }+25\,\text{dB} stärker als West-Signale | Kein merklicher Rauschanstieg: RX-Pfad J9 (RF2) in Software nicht aktiviert oder PTT-Mute-Relais hängt. |
