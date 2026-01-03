# IO-Board Register/Protokoll (Entwickler & Debug)

Diese Seite ist für alle, die verstehen wollen, wie das IO-Board per Register angesprochen wird, oder die Backend/WebUI erweitern möchten.

## Kontext: HL2 Protokoll
Der Hermes-Lite-2 ist kompatibilitätsorientiert aufgebaut und lehnt sich an openHPSDR „protocol1“/Metis an; Details inkl. Board_ID und Paketstruktur stehen im HL2-Wiki.

## Registermodell (typisches Muster)
Viele IO-Board-Firmwares nutzen ein statisches Register-Array (z. B. 256 Bytes), in das geschrieben und aus dem gelesen werden kann; ohne Zusatzlogik liefert ein Read oft einfach den zuletzt geschriebenen Wert zurück.

## Register-Namensraum / Kollisionen vermeiden
Wenn mehrere Tools/Backends Register nutzen, ist es sinnvoll, „höhere“ Register (z. B. ab 200) für projektspezifische Features zu verwenden und die Nutzung zu dokumentieren, um Kollisionen zu vermeiden.

## Empfehlung für diese Repo-Doku
- Lege eine kleine Tabelle im Code/Repo an: Register → Bedeutung → Bitfelder → Default → Version.
- Dokumentiere mindestens:
  - Welche Register steuern PTT/KEY?
  - Welche sind „Status“ vs. „Command“?
  - Welche sind latched / welche sind edge-triggered?

## Weiterführende Links
- HL2 Protocol Wiki: https://github.com/softerhardware/Hermes-Lite2/wiki/Protocol
- Diskussion/Best-Practice zu IO-Board-Registerarrays und Registerbereichen: https://groups.google.com/g/hermes-lite/c/zVF4yR1VyjA
