[**开始使用**](./getting-started.md) > **如何安装** > **WebUI** _(当前)_

---

### 通过 Webui 使用 GBabelDocUI

#### 如何打开 WebUI 页面：

有多种方法可以打开 WebUI 界面。如果您使用的是 **Windows**，请参考 [这篇文章](./INSTALLATION_winexe.md)；

1. 已安装 Python（3.10 <= 版本 <= 3.12）

2. 安装我们的软件包：

3. 在浏览器中开始使用：

    ```bash
    gbabeldocui
    ```

4. 如果浏览器未自动启动，请访问

    ```bash
    http://localhost:7860/
    ```

    将 `PDF` 文件拖入窗口并点击 `Translate`。

5. 如果您通过 docker 部署 GBabelDocUI，并使用 ollama 作为 GBabelDocUI 的后端 `LLM`，则应在 "Ollama host" 中填写

   ```bash
   http://host.docker.internal:11434
   ```

> **安全提示：** Ollama 是服务器侧服务，仅管理员可使用。私有地址 `http://host.docker.internal:11434` 默认会被拒绝。只有在可信部署中，才在容器环境变量中设置 `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true`。该设置会放宽 SSRF 防护；如果不可信用户可以访问 GBabelDocUI，不要启用它。

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## 预览

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>本页面的部分内容由 GPT 翻译，可能包含错误。</small></h6>