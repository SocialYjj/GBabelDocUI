# Installer GBabelDocUI avec Docker Compose

Docker Engine avec Compose v2 et Git sont requis. La configuration du dépôt fournit les montages persistants et les limites de sécurité nécessaires.

## Démarrage local

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Sous Linux, préparez le répertoire de données pour que l'UID/GID 10001 puisse écrire :

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

Ouvrez ensuite `http://127.0.0.1:7860/login.html`.

## Publier avec HTTPS

Configurez d'abord un proxy inverse HTTPS puis démarrez Compose au minimum avec :

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

N'utilisez le jeton d'initialisation que pour créer à distance le premier administrateur. Supprimez-le ensuite et redémarrez le service.

Ne répliquez pas le service et n'utilisez pas plusieurs workers Uvicorn avec le même répertoire de données.

## Données persistantes

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
