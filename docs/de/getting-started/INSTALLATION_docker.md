# GBabelDocUI mit Docker Compose installieren

Erforderlich sind Docker Engine mit Compose v2 und Git. Die Repository-Konfiguration enthält die benötigten Mounts und Sicherheitsgrenzen.

## Lokal starten

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Unter Linux muss das eingebundene Datenverzeichnis für UID/GID 10001 beschreibbar sein:

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

Öffnen Sie anschließend `http://127.0.0.1:7860/login.html`.

## Über HTTPS veröffentlichen

Konfigurieren Sie zuerst einen HTTPS-Reverse-Proxy und starten Sie Compose mindestens mit:

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

Verwenden Sie das Setup-Token nur für die entfernte Erstanlage des Administrators. Entfernen Sie es danach und starten Sie den Dienst neu.

Skalieren Sie den Dienst nicht und verwenden Sie keine mehreren Uvicorn-Worker für dasselbe Datenverzeichnis.

## Persistente Daten

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
