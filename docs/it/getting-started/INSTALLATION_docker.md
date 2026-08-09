# Installare GBabelDocUI con Docker Compose

Sono richiesti Docker Engine con Compose v2 e Git. La configurazione del repository include i mount e i limiti di sicurezza necessari.

## Avvio locale

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Su Linux preparare la directory dati affinché UID/GID 10001 possa scrivere:

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

Aprire quindi `http://127.0.0.1:7860/login.html`.

## Pubblicare tramite HTTPS

Configurare prima un reverse proxy HTTPS e avviare Compose almeno con:

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

Usare il token di configurazione solo per creare da remoto il primo amministratore. Rimuoverlo e riavviare il servizio subito dopo.

Non scalare il servizio e non usare più worker Uvicorn con la stessa directory dati.

## Dati persistenti

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
