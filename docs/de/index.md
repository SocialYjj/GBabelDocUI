# GBabelDocUI

GBabelDocUI ist eine selbst gehostete, mehrbenutzerfähige Weboberfläche für PDF-Übersetzungen mit BabelDOC.

Das Projekt basiert auf eaiu/GBabelDocUI und enthält einen geprüften Laufzeit-Teilsatz aus pdf2zh-next 2.9.0. Die eingebetteten Dateien umfassen weder die Upstream-Kommandozeile noch die Gradio-Oberfläche oder HTTP-API.

## Funktionen

- Getrennte Konten, Einstellungen, Dateien, Aufgaben und Verläufe für Administratoren und Benutzer.
- HttpOnly-Cookies, CSRF-Schutz, Anmeldebegrenzung und Sitzungslimits.
- Prüfung von PDF-Inhalt, Größe, Seiten, Speicherquote und Parallelität.
- Webkonfiguration für OpenAI, Azure OpenAI und Google Gemini.
- SQLite-Persistenz und gehärtete Docker-Compose-Bereitstellung als Einzelinstanz.

## Schnellstart

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # Linux bind mounts only
docker compose up -d --build
```

### uv

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

Öffnen Sie anschließend `http://127.0.0.1:7860/login.html`.

## Bereitstellungsgrenzen

- Öffentlicher Zugriff erfordert einen HTTPS-Reverse-Proxy und `GBABELDOCUI_COOKIE_SECURE=true`.
- Der erste Administrator wird lokal erstellt; für eine entfernte Initialisierung ist ein einmaliges `GBABELDOCUI_SETUP_TOKEN` erforderlich.
- Pro Datenverzeichnis darf nur ein Anwendungsprozess und eine Replik laufen.
- `data/` kann Konten, API-Schlüssel, hochgeladene PDFs und Ausgaben enthalten und darf nicht veröffentlicht werden.

## Dokumentation

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## Quellcode und Lizenz

GBabelDocUI und der eingebettete Upstream-Teilsatz werden unter AGPL-3.0 veröffentlicht. Herkunft, Prüfsummen und Änderungsgrenzen stehen in NOTICE und UPSTREAM.md.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
