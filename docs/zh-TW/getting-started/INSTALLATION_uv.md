[**開始使用**](./getting-started.md) > **安裝** > **uv** _(目前頁面)_

---

# 使用 uv 安裝 GBabelDocUI

本頁安裝的是 GBabelDocUI。專案已內建所需且經過校驗的 `pdf2zh-next 2.9.0` 執行時子集，不要另外安裝或使用上游 `pdf2zh_next` 命令取代 `gbabeldocui`。

## 環境需求

- Python 3.10–3.13
- Git
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)

## 安裝並執行

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

本機使用明文 HTTP 時：

=== "Linux 與 macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

開啟 `http://127.0.0.1:7860/login.html`。

公開部署時保持 `GBABELDOCUI_COOKIE_SECURE=true`，使用 HTTPS 反向代理，並確保每個資料目錄只執行一個程序與一個副本。

## 開發環境

```bash
uv sync --dev --frozen
uv run pytest -q
uv run ruff check gbabeldocui tests
uv run ruff format --check gbabeldocui tests
```
