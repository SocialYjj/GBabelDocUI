# GBabelDocUI

GBabelDocUI — самостоятельно размещаемый многопользовательский веб-интерфейс для перевода PDF с помощью BabelDOC.

Проект основан на eaiu/GBabelDocUI и содержит проверенную часть среды выполнения pdf2zh-next 2.9.0. В состав не входят исходные CLI, интерфейс Gradio и HTTP API.

## Возможности

- Изолированные по пользователям учетные записи, настройки, файлы, задания и история.
- HttpOnly cookie, защита CSRF, ограничение входов и количества сессий.
- Проверка PDF, размера, страниц, квоты хранения и параллельных заданий.
- Веб-настройка OpenAI, Azure OpenAI и Google Gemini.
- Хранение в SQLite и защищенное развертывание одной копии через Docker Compose.

## Быстрый запуск

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # Linux bind mounts only
docker compose up -d --build
```

### uv

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

После запуска откройте `http://127.0.0.1:7860/login.html`.

## Ограничения развертывания

- Для публичного доступа нужны обратный прокси HTTPS и `GBABELDOCUI_COOKIE_SECURE=true`.
- Первый администратор создается локально; удаленная инициализация требует одноразовый `GBABELDOCUI_SETUP_TOKEN`.
- Для каждого каталога данных допускается один процесс и одна копия приложения.
- `data/` может содержать учетные записи, ключи API, PDF и результаты и не должен публиковаться.

## Документация

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## Исходный код и лицензия

GBabelDocUI и встроенная часть среды распространяются по AGPL-3.0. Происхождение, контрольные суммы и изменения описаны в NOTICE и UPSTREAM.md.

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
