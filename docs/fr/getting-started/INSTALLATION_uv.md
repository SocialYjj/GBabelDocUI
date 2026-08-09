# Installer GBabelDocUI avec uv

GBabelDocUI contient déjà le sous-ensemble vérifié de pdf2zh-next dont il a besoin. N'utilisez pas la CLI amont à la place de `gbabeldocui`.

## Prérequis

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Installer et exécuter

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

Ouvrez ensuite `http://127.0.0.1:7860/login.html`.

En production, conservez les cookies Secure, utilisez HTTPS et une seule instance par répertoire de données.

## Environnement de développement

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
