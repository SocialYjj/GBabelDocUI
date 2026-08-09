# Установка GBabelDocUI через Docker Compose

Требуются Docker Engine с Compose v2 и Git. Конфигурация репозитория содержит необходимые постоянные тома и ограничения безопасности.

## Локальный запуск

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

В Linux подготовьте каталог данных для записи пользователем UID/GID 10001:

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

После запуска откройте `http://127.0.0.1:7860/login.html`.

## Публикация через HTTPS

Сначала настройте обратный прокси HTTPS и запустите Compose как минимум с такими переменными:

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

Используйте токен настройки только для удаленного создания первого администратора. После этого удалите его и перезапустите сервис.

Не масштабируйте сервис и не используйте несколько workers Uvicorn с одним каталогом данных.

## Постоянные данные

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
