[**Начало работы**](./getting-started.md) > **Установка** > **WebUI** _(текущая)_

---

### Использование GBabelDocUI через Webui

#### Как открыть страницу WebUI:

Существует несколько способов открытия интерфейса WebUI. Если вы используете **Windows**, обратитесь к [этой статье](./INSTALLATION_winexe.md);

1. Установленный Python (версия от 3.10 до 3.12)

2. Установите наш пакет:

3. Начните использование в браузере:

    ```bash
    gbabeldocui
    ```

4. Если ваш браузер не запустился автоматически, перейдите по адресу:

    ```bash
    http://localhost:7860/
    ```

    Перетащите `PDF` файл в окно и нажмите `Translate`.

5. Если вы развертываете GBabelDocUI с помощью docker и используете ollama в качестве бэкенд LLM для GBabelDocUI, вам следует указать "Ollama host" как:

   ```bash
   http://host.docker.internal:11434
   ```

> **Примечание по безопасности:** Ollama — серверная служба, доступная только администраторам. Частная конечная точка `http://host.docker.internal:11434` по умолчанию отклоняется. Устанавливайте `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` в окружении контейнера только при доверенном развертывании. Эта настройка ослабляет защиту от SSRF; не включайте ее, если к GBabelDocUI могут обращаться ненадежные пользователи.

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Предпросмотр

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>Часть содержимого этой страницы была переведена GPT и может содержать ошибки.</small></h6>