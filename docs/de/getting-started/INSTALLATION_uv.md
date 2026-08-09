# GBabelDocUI mit uv installieren

GBabelDocUI enthält den benötigten geprüften pdf2zh-next-Teilsatz. Installieren oder verwenden Sie die Upstream-Kommandozeile nicht als Ersatz für `gbabeldocui`.

## Voraussetzungen

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Installieren und starten

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

Öffnen Sie anschließend `http://127.0.0.1:7860/login.html`.

Für öffentliche Bereitstellungen bleiben Secure-Cookies aktiv; verwenden Sie HTTPS und genau eine Instanz pro Datenverzeichnis.

## Entwicklungsumgebung

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
