# Instalar GBabelDocUI con uv

GBabelDocUI ya incluye el subconjunto verificado de pdf2zh-next que necesita. No instale ni use la CLI original como sustituto de `gbabeldocui`.

## Requisitos

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Instalar y ejecutar

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

Después, abra `http://127.0.0.1:7860/login.html`.

En producción mantenga las cookies Secure, use HTTPS y una sola instancia por directorio de datos.

## Entorno de desarrollo

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
