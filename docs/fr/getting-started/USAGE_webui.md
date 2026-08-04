[**Commencer**](./getting-started.md) > **Installation** > **WebUI** _(current)_

---

### Utiliser GBabelDocUI via Webui

#### Comment ouvrir la page WebUI :

Il existe plusieurs méthodes pour ouvrir l'interface WebUI. Si vous utilisez **Windows**, veuillez consulter [cet article](./INSTALLATION_winexe.md);

1. Python installé (version 3.10 <= version <= 3.12)

2. Installez notre package :

3. Commencez à utiliser dans le navigateur :

    ```bash
    gbabeldocui
    ```

4. Si votre navigateur ne s'est pas lancé automatiquement, allez à

    ```bash
    http://localhost:7860/
    ```

    Déposez le fichier PDF dans la fenêtre et cliquez sur `Translate`.

5. Si vous déployez GBabelDocUI avec docker, et que vous utilisez ollama comme backend LLM de GBabelDocUI, vous devez remplir "Ollama host" avec

   ```bash
   http://host.docker.internal:11434
   ```

> **Note de sécurité :** Ollama est un service côté serveur accessible uniquement aux administrateurs. Le point de terminaison privé `http://host.docker.internal:11434` est refusé par défaut. Dans un déploiement de confiance uniquement, définissez `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` dans l'environnement du conteneur. Ce paramètre assouplit la protection SSRF ; ne l'activez pas si des utilisateurs non fiables peuvent accéder à GBabelDocUI.

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Preview## Aperçu

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>Une partie du contenu de cette page a été traduite par GPT et peut contenir des erreurs.</small></h6>