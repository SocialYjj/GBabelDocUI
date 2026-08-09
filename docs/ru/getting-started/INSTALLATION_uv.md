# Установка GBabelDocUI через uv

GBabelDocUI уже содержит необходимую проверенную часть pdf2zh-next. Не используйте исходный CLI вместо `gbabeldocui`.

## Требования

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Установка и запуск

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

После запуска откройте `http://127.0.0.1:7860/login.html`.

В публичной среде сохраняйте Secure cookie, используйте HTTPS и одну копию на каталог данных.

## Среда разработки

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
