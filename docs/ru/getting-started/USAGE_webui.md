# Использование веб-интерфейса GBabelDocUI

Сервис не открывает браузер автоматически. Запустите его и вручную откройте страницу входа.

## Требования

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## Запуск из репозитория

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

Для локального HTTP отключите атрибут Secure у cookie:

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

## Первое использование

1. Создайте первого администратора на локальной странице входа.
2. Настройте OpenAI, Azure OpenAI или Google Gemini.
3. Выберите языки, тип результата, страницы и параметры PDF.
4. Загрузите PDF, запустите задание и скачайте результат из истории.

Сохраненные ключи API остаются на сервере. Не добавляйте каталог `data/` в Git и не публикуйте его.

Для контейнеров используйте инструкцию Docker Compose. Публичное развертывание требует HTTPS и одну копию на каталог данных.
