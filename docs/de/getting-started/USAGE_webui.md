[**Erste Schritte**](./getting-started.md) > **Installation** > **WebUI** _(aktuell)_

---

### Verwendung von GBabelDocUI über Webui

#### So öffnen Sie die WebUI-Seite:

Es gibt mehrere Methoden, um die WebUI-Oberfläche zu öffnen. Wenn Sie **Windows** verwenden, lesen Sie bitte [diesen Artikel](./INSTALLATION_winexe.md);

1. Python installiert (3.10 <= Version <= 3.12)

2. Installieren Sie unser Paket:

3. Beginnen Sie mit der Verwendung im Browser:

    ```bash
    gbabeldocui
    ```

4. Falls Ihr Browser nicht automatisch gestartet wurde, gehen Sie zu

    ```bash
    http://localhost:7860/
    ```

    Ziehen Sie die PDF-Datei in das Fenster und klicken Sie auf `Translate`.

5. Wenn Sie GBabelDocUI mit Docker bereitstellen und ollama als Backend-LLM für GBabelDocUI verwenden, sollten Sie "Ollama host" mit folgendem Wert ausfüllen:

   ```bash
   http://host.docker.internal:11434
   ```

> **Sicherheitshinweis:** Ollama ist ein serverseitiger Dienst und steht nur Administratoren zur Verfügung. Der private Endpunkt `http://host.docker.internal:11434` wird standardmäßig abgelehnt. Setzen Sie `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` in der Container-Umgebung nur bei einer vertrauenswürdigen Bereitstellung. Dadurch wird der SSRF-Schutz gelockert; aktivieren Sie dies nicht, wenn nicht vertrauenswürdige Benutzer auf GBabelDocUI zugreifen können.

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Preview## Vorschau

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>Ein Teil des Inhalts dieser Seite wurde von GPT übersetzt und kann Fehler enthalten.</small></h6>