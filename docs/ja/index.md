# GBabelDocUI

GBabelDocUI は、BabelDOC を利用するセルフホスト型のマルチユーザー PDF 翻訳 Web UI です。

本プロジェクトは eaiu/GBabelDocUI を基にし、検証済みの pdf2zh-next 2.9.0 ランタイムの一部を同梱しています。上流の CLI、Gradio UI、HTTP API は含みません。

## 主な機能

- ユーザーごとに分離されたアカウント、設定、ファイル、タスク、履歴。
- HttpOnly Cookie、CSRF 対策、ログイン制限、セッション上限。
- PDF 内容、サイズ、ページ、保存容量、同時実行数の検証。
- OpenAI、Azure OpenAI、Google Gemini の Web 設定。
- SQLite 永続化と、単一インスタンス向けに強化された Docker Compose。

## クイックスタート

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

起動後に `http://127.0.0.1:7860/login.html` を開きます。

## デプロイ上の制約

- 公開する場合は HTTPS リバースプロキシと `GBABELDOCUI_COOKIE_SECURE=true` が必要です。
- 最初の管理者はローカルで作成します。遠隔初期化には一度限りの `GBABELDOCUI_SETUP_TOKEN` が必要です。
- データディレクトリごとに、アプリケーションプロセスとレプリカは 1 つだけです。
- `data/` にはアカウント、API キー、PDF、生成物が含まれるため公開しないでください。

## ドキュメント

- [Docker](./getting-started/INSTALLATION_docker.md)
- [uv](./getting-started/INSTALLATION_uv.md)
- [Web UI](./getting-started/USAGE_webui.md)
- [Advanced reference](./advanced/advanced.md)

## ソースとライセンス

GBabelDocUI と同梱ランタイムは AGPL-3.0 で配布されます。由来、チェックサム、変更範囲は NOTICE と UPSTREAM.md に記載されています。

- [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)
- [NOTICE](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)
- [UPSTREAM.md](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)
