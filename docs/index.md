# GBabelDocUI

GBabelDocUI is a self-hosted, multi-user PDF translation Web UI powered by BabelDOC.

This project is modified from [`eaiu/GBabelDocUI`](https://github.com/eaiu/GBabelDocUI) and bundles a verified runtime subset from `pdf2zh-next 2.9.0`. The bundled subset contains only the configuration models, high-level translation entry point, translators, and asynchronous bridge used by this Web UI; it does not include the upstream CLI, Gradio UI, or HTTP API.

## Features

- Administrator and regular-user accounts with isolated settings, files, tasks, and history.
- `HttpOnly` cookie sessions, CSRF protection, login throttling, and per-user session limits.
- PDF content, size, page-count, page-range, storage-quota, and task-concurrency validation.
- Web configuration for OpenAI, Azure OpenAI, and Google Gemini.
- SQLite-backed task state and history with explicit retention and cleanup behavior.
- A hardened, single-instance Docker Compose deployment using a non-root user and a read-only root filesystem.

## Quick start

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # Linux bind mounts only
docker compose up -d --build
```

Open `http://127.0.0.1:7860/login.html`. Compose binds to the loopback interface by default and uses `GBABELDOCUI_COOKIE_SECURE=false` for local HTTP.

### uv

Python 3.10 through 3.13 and [`uv`](https://docs.astral.sh/uv/) are required.

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

On Windows PowerShell, replace the `export` command with:

```powershell
$env:GBABELDOCUI_COOKIE_SECURE = "false"
```

## Deployment boundaries

- Public access requires an HTTPS reverse proxy and `GBABELDOCUI_COOKIE_SECURE=true`.
- The first administrator can be created only from a loopback request. For remote initialization, set a one-time high-entropy `GBABELDOCUI_SETUP_TOKEN`, complete setup, then remove it and restart the service.
- Run one application process and one replica for each data directory. Multiple Uvicorn workers or replicas must not share the same `data/` directory.
- `data/` can contain account records, API keys, uploaded PDFs, and translated output. Never commit, package, or publish it.
- The Web UI does not expose the bundled upstream CLI, Gradio UI, or HTTP API.

## Documentation

- [Docker installation](./getting-started/INSTALLATION_docker.md)
- [uv installation](./getting-started/INSTALLATION_uv.md)
- [Web UI usage](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)
- [Translation services](./advanced/Documentation-of-Translation-Services.md)

## Source and license

GBabelDocUI and the bundled upstream runtime subset are distributed under [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE). Provenance, checksums, and modification boundaries are recorded in [`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE) and the [bundled runtime source note](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md).
