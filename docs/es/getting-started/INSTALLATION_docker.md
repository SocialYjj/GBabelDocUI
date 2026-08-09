# Instalar GBabelDocUI con Docker Compose

Se requieren Docker Engine con Compose v2 y Git. La configuración del repositorio incluye los montajes y límites de seguridad necesarios.

## Inicio local

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

En Linux, prepare el directorio de datos para que UID/GID 10001 pueda escribir:

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

Después, abra `http://127.0.0.1:7860/login.html`.

## Publicar mediante HTTPS

Configure primero un proxy inverso HTTPS e inicie Compose al menos con:

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

Use el token de configuración solo para crear remotamente el primer administrador. Elimínelo después y reinicie el servicio.

No escale el servicio ni use varios workers de Uvicorn con el mismo directorio de datos.

## Datos persistentes

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
