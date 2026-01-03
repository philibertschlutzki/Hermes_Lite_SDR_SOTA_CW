# WebUI (statisch)

Die WebUI ist reine statische Seite (HTML/JS/CSS) und spricht das FastAPI-Backend via Fetch an. [file:1]

## Betrieb

- Im einfachsten Fall lokal öffnen und die Backend-URL anpassen.
- Empfohlen: via nginx ausliefern (siehe `deploy/nginx-site.conf`) und `/api` auf das Backend reverse-proxyen. [file:1]

Dateien:
- `static/index.html`
- `static/app.js`
- `static/style.css`
