# Instalar GBabelDocUI com Docker Compose

Docker Engine com Compose v2 e Git são necessários. A configuração do repositório inclui montagens persistentes e limites de segurança.

## Início local

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

No Linux, prepare o diretório de dados para permitir escrita por UID/GID 10001:

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

Depois, abra `http://127.0.0.1:7860/login.html`.

## Publicar por HTTPS

Configure primeiro um proxy reverso HTTPS e inicie o Compose pelo menos com:

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

Use o token de configuração somente para criar remotamente o primeiro administrador. Remova-o depois e reinicie o serviço.

Não escale o serviço nem use vários workers Uvicorn com o mesmo diretório de dados.

## Dados persistentes

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
