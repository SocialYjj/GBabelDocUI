# Instalar GBabelDocUI com uv

GBabelDocUI já inclui o subconjunto verificado de pdf2zh-next necessário. Não use a CLI upstream no lugar de `gbabeldocui`.

## Requisitos

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Instalar e executar

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

Depois, abra `http://127.0.0.1:7860/login.html`.

Em produção, mantenha cookies Secure, use HTTPS e uma instância por diretório de dados.

## Ambiente de desenvolvimento

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
