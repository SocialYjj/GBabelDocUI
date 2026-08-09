# Docker Compose で GBabelDocUI をインストール

Docker Engine、Compose v2、Git が必要です。リポジトリの設定には必要な永続化マウントとセキュリティ制約が含まれます。

## ローカル起動

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
```

Linux では UID/GID 10001 が書き込めるようにデータディレクトリを準備します。

```bash
mkdir -p data
sudo chown -R 10001:10001 data
docker compose up -d --build
```

起動後に `http://127.0.0.1:7860/login.html` を開きます。

## HTTPS で公開

先に HTTPS リバースプロキシを設定し、少なくとも次の環境変数で Compose を起動します。

```bash
export GBABELDOCUI_COOKIE_SECURE=true
export GBABELDOCUI_SETUP_TOKEN='replace-with-a-long-random-one-time-value'
docker compose up -d --build
```

セットアップトークンは最初の管理者を遠隔作成するときだけ使用し、完了後に削除してサービスを再起動します。

サービスをスケールさせたり、同じデータディレクトリで複数の Uvicorn worker を使用したりしないでください。

## 永続データ

- `./data:/app/data`: accounts, settings, tasks, uploads, and outputs.
- `babeldoc-cache:/cache`: BabelDOC models and font caches.
- `/tmp`: bounded temporary filesystem.

```bash
docker compose ps
docker compose logs --tail 200 gbabeldocui
docker compose down
```
