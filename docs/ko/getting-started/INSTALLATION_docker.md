# Docker Compose로 GBabelDocUI 설치

Docker Engine, Compose v2 및 Git이 필요합니다. 저장소 설정에는 필요한 영속 마운트와 보안 제한이 포함됩니다.

## 로컬 시작

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Linux에서는 UID/GID 10001이 쓸 수 있도록 데이터 디렉터리를 준비합니다.

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

시작 후 `http://127.0.0.1:7860/login.html`을 여십시오.

## HTTPS로 공개

먼저 HTTPS 리버스 프록시를 구성하고 최소한 다음 환경 변수로 Compose를 시작합니다.

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

설정 토큰은 첫 관리자를 원격 생성할 때만 사용하고, 완료 후 제거한 뒤 서비스를 다시 시작하십시오.

서비스를 확장하거나 동일한 데이터 디렉터리에 여러 Uvicorn worker를 사용하지 마십시오.

## 영속 데이터

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
