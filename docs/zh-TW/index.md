# GBabelDocUI

GBabelDocUI 是以 BabelDOC 為核心的自架式多使用者 PDF 翻譯 Web UI。

本專案修改自 [`eaiu/GBabelDocUI`](https://github.com/eaiu/GBabelDocUI)，並內建經過校驗的 `pdf2zh-next 2.9.0` 執行時子集。內建內容只包含本 Web UI 使用的設定模型、高階翻譯入口、翻譯器與非同步橋接，不包含上游命令列工具、Gradio 介面或 HTTP API。

## 主要功能

- 管理員與一般使用者帳戶，設定、檔案、任務與歷史記錄依使用者隔離。
- `HttpOnly` Cookie 工作階段、CSRF 防護、登入限流與單一使用者工作階段上限。
- PDF 內容、大小、頁數、頁面範圍、儲存配額與任務並行數驗證。
- Web 設定頁支援 OpenAI、Azure OpenAI 與 Google Gemini。
- 使用 SQLite 持久化任務狀態與歷史記錄，並提供明確的保留與清理機制。
- 單一執行個體 Docker Compose 部署，使用非 root 使用者與唯讀根檔案系統。

## 快速開始

### Docker Compose

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
mkdir -p data
sudo chown -R 10001:10001 data  # 僅 Linux 綁定目錄需要
docker compose up -d --build
```

開啟 `http://127.0.0.1:7860/login.html`。Compose 預設只綁定回環位址，並為本機 HTTP 設定 `GBABELDOCUI_COOKIE_SECURE=false`。

### uv

需要 Python 3.10–3.13 與 [`uv`](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
export GBABELDOCUI_COOKIE_SECURE=false
uv run gbabeldocui
```

Windows PowerShell 請將 `export` 命令替換為：

```powershell
$env:GBABELDOCUI_COOKIE_SECURE = "false"
```

## 部署邊界

- 公開存取必須使用 HTTPS 反向代理，並保持 `GBABELDOCUI_COOKIE_SECURE=true`。
- 第一個管理員只允許透過回環請求建立。必須遠端初始化時，設定一次性高強度 `GBABELDOCUI_SETUP_TOKEN`，完成後立即移除並重新啟動服務。
- 每個資料目錄只執行一個應用程式程序與一個副本；不得讓多個 Uvicorn worker 或多個副本共用同一個 `data/` 目錄。
- `data/` 可能包含帳戶、API 金鑰、上傳 PDF 與翻譯結果，禁止提交、封裝或公開。
- Web UI 不提供內建的上游命令列工具、Gradio 介面或 HTTP API。

## 文件

- [Docker 安裝](./getting-started/INSTALLATION_docker.md)
- [uv 安裝](./getting-started/INSTALLATION_uv.md)
- [Web UI 使用](./getting-started/USAGE_webui.md)
- [進階參考](./advanced/advanced.md)
- [翻譯服務](./advanced/Documentation-of-Translation-Services.md)

## 來源與授權

GBabelDocUI 與內建的上游執行時子集依 [AGPL-3.0](https://github.com/SocialYjj/GBabelDocUI/blob/main/LICENSE) 發布。來源、校驗值與修改邊界請參閱 [`NOTICE`](https://github.com/SocialYjj/GBabelDocUI/blob/main/NOTICE) 與[內建執行時來源說明](https://github.com/SocialYjj/GBabelDocUI/blob/main/gbabeldocui/_vendor/pdf2zh_next/UPSTREAM.md)。
