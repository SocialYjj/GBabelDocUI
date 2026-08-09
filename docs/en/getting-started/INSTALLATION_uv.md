[**Getting Started**](./getting-started.md) > **Installation** > **uv** _(current)_

---

# Install GBabelDocUI with uv

This page installs GBabelDocUI itself. The project bundles the verified `pdf2zh-next 2.9.0` runtime subset it needs; do not install or invoke the upstream `pdf2zh_next` CLI as a substitute for `gbabeldocui`.

## Requirements

- Python 3.10 through 3.13
- Git
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

## Install and run

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

For local HTTP:

=== "Linux and macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

Open `http://127.0.0.1:7860/login.html`.

For a public deployment, keep `GBABELDOCUI_COOKIE_SECURE=true`, place the service behind an HTTPS reverse proxy, and run one process and one replica for each data directory.

## Development environment

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
