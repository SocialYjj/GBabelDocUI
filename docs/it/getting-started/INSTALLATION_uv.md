# Installare GBabelDocUI con uv

GBabelDocUI include già il sottoinsieme verificato di pdf2zh-next necessario. Non usare la CLI upstream al posto di `gbabeldocui`.

## Requisiti

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Installare ed eseguire

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

=== "Linux/macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

Aprire quindi `http://127.0.0.1:7860/login.html`.

In produzione mantenere i cookie Secure, usare HTTPS e una sola istanza per directory dati.

## Ambiente di sviluppo

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
