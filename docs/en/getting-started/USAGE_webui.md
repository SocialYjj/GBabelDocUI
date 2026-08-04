[**Getting Started**](./getting-started.md) > **Installation** > **WebUI** _(current)_

---

### Use GBabelDocUI via Webui

#### How to open the WebUI page:

There are several methods to open the WebUI interface. If you are using **Windows**, please refer to [this article](./INSTALLATION_winexe.md);

1. Python installed (3.10 <= version <= 3.12)

2. Install our package:

3. Start using in browser:

    ```bash
    gbabeldocui
    ```

4. If your browswer has not been started automatically, goto

    ```bash
    http://localhost:7860/
    ```

    Drop the PDF file into the window and click `Translate`.

5. If you deploy GBabelDocUI with docker, and you are using ollama as GBabelDocUI's backend LLM, you should fill "Ollama host" with

   ```bash
   http://host.docker.internal:11434
   ```

> **Security note:** Ollama is a server-side service available only to administrators. The private endpoint `http://host.docker.internal:11434` is rejected by default. Only for a trusted deployment, set `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` in the container environment. This relaxes SSRF protection; do not enable it when untrusted users can access GBabelDocUI.

<!-- <img src="./images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Preview## Preview

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>
