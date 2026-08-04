[**開始使用**](./getting-started.md) > **如何安裝** > **WebUI** _(current)_

---

> **說明：** 本頁的主入口是 GBabelDocUI Web UI；命令行、`uv` 與 Windows EXE 頁面僅是官方 `pdf2zh-next` 執行時參考，參數彼此不相容。

### 透過 Webui 使用 GBabelDocUI

#### 如何開啟 WebUI 頁面：

有幾種方法可以開啟 WebUI 介面。如果您使用的是 **Windows**，請參考 [這篇文章](./INSTALLATION_winexe.md)；

1. 已安裝 Python（3.10 <= 版本 <= 3.12）

2. 安裝我們的套件：

3. 在瀏覽器中開始使用：

    ```bash
    gbabeldocui
    ```

4. 如果瀏覽器未自動啟動，請前往

    ```bash
    http://localhost:7860/
    ```

    將 `PDF` 文件拖入視窗並點擊 `Translate`。

5. 如果您使用 docker 部署 GBabelDocUI，且使用 ollama 作為 GBabelDocUI 的後端 LLM，應在「Ollama host」欄位填入

   ```bash
   http://host.docker.internal:11434
   ```

   Ollama 是伺服器側服務，僅管理員可使用。`host.docker.internal` 等私有位址預設會被拒絕；只有在可信部署中，才在容器環境設定 `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true`。這會放寬 SSRF 防護，不應對不可信使用者開啟。

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## 預覽

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right">
<h6><small>Some content on this page has been translated by GPT and may contain errors.</small></h6>
