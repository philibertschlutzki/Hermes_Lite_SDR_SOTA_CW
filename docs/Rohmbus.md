### Vorgehen: Aufbau & Integration der Terminated Rhombic RX-Antenne

* **1. Standortvermessung & Ausrichtung festlegen (LV95: `2'685'931.37, 1'152'055.87`):**
  * **Hauptachse ausrichten:** Längsachse entlang der Lichtung mit einem Azimut von **$75^\circ\text{–}80^\circ$ (Ostnordost)** parallel zu den Höhenlinien festlegen (Speisepunkt im Westen, Abschlusswiderstand im Osten)[cite: 1].
  * **Baum-Ankerpunkte wählen:** Vier stabile Randbäume außerhalb der Lichtung auswählen[cite: 1], die eine Längsachse von **$75\text{–}85\,\text{m}$**[cite: 1] und eine Querachse von **$35\text{–}40\,\text{m}$**[cite: 1] ermöglichen.
  * **Mindestabstand zum Bewuchs:** Eckisolatoren mittels Dyneema-Abspannseilen mindestens **$2,5\text{–}3,0\,\text{m}$** von Baumstämmen und Ästen distanzieren, um Bedämpfung durch feuchtes Holz/Laub zu vermeiden.

* **2. Geometrie & Hangparallelität einmessen:**
  * **Schenkellänge & Winkel:** Vier identische Schenkel à **$42\text{–}46\,\text{m}$** (ca. $176\,\text{m}$ Gesamtdrahtlänge) mit stumpfen Seitenwinkeln von **$130^\circ$** (Nord/Süd) und spitzen Endwinkeln von **$50^\circ$** (West/Ost) konfektionieren.
  * **Hangparallele Aufhängung:** Alle vier Eckpunkte jeweils **$12\text{–}14\,\text{m}$ senkrecht über dem jeweiligen Waldboden** montieren (nicht nach Wasserwaage nivellieren), um den Wellenwiderstand ($600\text{–}700\,\Omega$) konstant zu halten und die Strahlungskeule leicht ins Tal zu neigen[cite: 1].

* **3. Mechanische Aufhängung & Wind-/Schneelast-Entkopplung:**
  * **Baumschonende Montage:** Baumschoner-Gurte und Edelstahl-Umlenkrollen an den vier Ankerbäumen anbringen (keine Nägel/Schrauben).
  * **Dynamischer Lastausgleich:** Umlenkrollen mit **$4\text{–}5\,\text{kg}$ Gegengewichten** pro Ecke ausstatten, um asynchrone Baumbewegungen bei Wind sowie Nassschneelasten auf $1528\,\text{m}$ Höhe[cite: 1] ohne Drahtriss abzufangen.
  * **Wartungszugang:** Abspannseile an Speise- und Abschlusspunkt über Umlenkrollen zu Klampen am Stammfuß führen, um Balun- und Widerstandsbox jederzeit ohne Klettern absenken zu können.

* **4. HF-Komponenten fertigen & montieren:**
  * **Speisepunkt (West):** 12:1 RX-Übertrager (2 Wdg. primär / 7 Wdg. sekundär auf **Fair-Rite 2843000202**, galvanisch getrennt) in einem IP67-Polycarbonat-Gehäuse mit Druckausgleichselement verbauen.
  * **Mantelwellensperre:** Direkt unterhalb des Speisegehäuses eine 1:1 Gleichtaktdrossel (12 Windungen **RG-400** auf **Fair-Rite FT240-31**) einfügen.
  * **Abschlusspunkt (Ost):** Induktionsarmen Abschlusswiderstand (**$680\text{–}750\,\Omega$**, z. B. $2\times 1,5\,\text{k}\Omega$ Metalloxid parallel) inkl. **$100\,\text{k}\Omega$ Bleeder-Widerstand** und **$90\,\text{V}$ Gasentladungsableiter (GDT)** zur Ableitung elektrostatischer Aufladungen im zweiten IP67-Gehäuse montieren.

* **5. Zuleitung, Blitzschutz & Hermes-Lite 2 (HL2) Integration:**
  * **Koax-Zuleitung:** Verlustarmes, doppelt geschirmtes Koaxkabel (**Hyperflex 5** oder **Ecoflex 10**) vom Speisepunkt ins Rustico verlegen.
  * **Potentialausgleich:** Am Gebäudeeintritt einen Koax-Überspannungsableiter (GDT) an die Potentialausgleichsschiene anbinden.
  * **Preselektion (Zwingend vor HL2):** Steilflankige Monoband-Bandpassfilter für **40 m, 30 m und 20 m** (geschaltet über das **N2ADR IO-Board / RP2040**) vor den HL2-RX-Eingang schalten, um Kurzwellen-Rundfunksender um $>45\,\text{dB}$ zu unterdrücken und `ADC Clipping` zu verhindern.
  * **HL2 Gain-Staging:** Internen LNA-Gain auf **`0 dB` bis `+4 dB`** einstellen (keinen externen Preamp nutzen), sodass das Antennenrauschen den SDR-Grundrauschpegel sauber um ca. $8\,\text{dB}$ anhebt.
