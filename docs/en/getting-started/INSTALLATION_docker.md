[**Getting Started**](./getting-started.md) > **Installation** > **Docker** _(current)_

---

# Install GBabelDocUI with Docker Compose

Docker Engine with Compose v2 and Git are required. The repository Compose file is the supported container deployment because it includes the required persistent mounts and security settings.

## Start locally

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

On Linux, prepare the bind-mounted data directory for the container user:

```bash
mkdir -p data
sudo chown -R 10001:10001 data
```

Build and start the service:

```bash
docker compose up -d --build
```

Open `http://127.0.0.1:7860/login.html`. The local Compose defaults deliberately set `GBABELDOCUI_COOKIE_SECURE=false` because the service is reached over loopback HTTP.

## Publish through HTTPS

Before exposing the service, configure an HTTPS reverse proxy and start Compose with at least:

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

Use the setup token only when the initial administrator must be created remotely. Remove the variable and restart the service immediately after initialization.

Do not scale the service or add multiple Uvicorn workers. One application process owns one `data/` directory, and a second instance using the same directory intentionally fails fast.

## Persistent data

- `./data:/app/data` stores accounts, settings, task history, uploads, and outputs.
- The `babeldoc-cache` named volume stores model and font caches under `/cache`.
- The container root filesystem is read-only; `/tmp` is a bounded temporary filesystem.

Do not commit, package, or publish `./data`.

## Check and stop

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```

`docker compose down` does not remove `./data` or the named cache volume unless they are deleted explicitly.
