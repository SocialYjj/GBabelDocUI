# GBabelDocUI

基於官方 [`pdf2zh-next`](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next) 執行時的多使用者 PDF 翻譯 Web UI 適配層。

本專案基於 [`eaiu/GBabelDocUI`](https://github.com/eaiu/GBabelDocUI) 修改，目前維護的儲存庫是 [`SocialYjj/GBabelDocUI`](https://github.com/SocialYjj/GBabelDocUI)。核心翻譯引擎由 [`BabelDOC`](https://github.com/funstory-ai/BabelDOC) 提供。

## 主要功能

- 多使用者註冊、登入，以及管理員與一般使用者權限隔離。
- 使用者設定、翻譯歷史、上傳檔案與輸出檔案持久化保存。
- PDF 上傳驗證、使用者儲存配額、翻譯任務狀態與任務恢復。
- 支援官方執行時提供的 OpenAI、SiliconFlow、Gemini、Ollama 等翻譯服務。
- 支援單語 PDF、雙語 PDF、頁面範圍、術語擷取與 BabelDOC 進階選項。

## Docker 部署

在 Linux 或 VPS 上，建議使用儲存庫根目錄的 Compose 設定：

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
docker compose up -d --build
```

預設存取 `http://127.0.0.1:7860`。Compose 會將 `./data` 掛載到 `/app/data`，其中包含帳戶、設定、上傳檔案與翻譯結果；此目錄只應保留在本機或 VPS，不得提交到公開儲存庫。

首次 GitHub Actions 發布完成後，也可以使用目前儲存庫的 amd64 GHCR 映像：

```bash
docker pull ghcr.io/socialyjj/gbabeldocui:latest
docker run -d \
  --name gbabeldocui \
  --restart unless-stopped \
  -p 127.0.0.1:7860:7860 \
  -v "$(pwd)/data:/app/data" \
  ghcr.io/socialyjj/gbabeldocui:latest
```

公開存取時應設定 HTTPS 反向代理。翻譯執行器按單一程序設計，請保持一個 Uvicorn worker 和一個應用程式副本，不要讓多個副本共用同一個 `data/` 目錄。

## Web UI 使用

1. 開啟 `/login.html`，首次執行時建立管理員帳戶。
2. 在「設定」頁面填寫翻譯服務、模型、API Key、來源語言、目標語言、PDF 輸出與頁面範圍。
3. 在「上傳」頁面選擇 PDF 並開始翻譯；任務進度與歷史記錄會依目前使用者隔離。
4. 翻譯完成後下載單語或雙語 PDF。API Key 等敏感設定只會儲存在本機 `data/`，不要匯出或提交到 Git。

詳細說明：

- [Docker 安裝](./getting-started/INSTALLATION_docker.md)
- [Web UI 使用](./getting-started/USAGE_webui.md)
- [進階選項](./advanced/advanced.md)
- [翻譯服務文件](./advanced/Documentation-of-Translation-Services.md)
- [支援的語言](./supported_languages.md)

## 本機開發

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```

實際部署與資料邊界請參考根目錄的 [`README.md`](https://github.com/SocialYjj/GBabelDocUI/blob/main/README.md)、[`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE) 和 [`docker-compose.yml`](https://github.com/SocialYjj/GBabelDocUI/blob/main/docker-compose.yml)。

## 來源與授權

本專案遵循 [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE)。第三方執行時、BabelDOC 與早期來源的修改範圍請參考 [`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE)。

問題回報和程式碼貢獻請提交至 [GitHub Issues](https://github.com/SocialYjj/GBabelDocUI/issues) 或 Pull Request；不要上傳 `data/`、`yuan/`、資料庫、密鑰、PDF 和生成結果。
