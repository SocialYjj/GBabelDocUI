[**Empezar**](./getting-started.md) > **Instalación** > **WebUI** _(actual)_

---

### Usar GBabelDocUI a través de Webui

#### Cómo abrir la página de WebUI:

Existen varios métodos para abrir la interfaz de WebUI. Si estás usando **Windows**, por favor consulta [este artículo](./INSTALLATION_winexe.md);

1. Python instalado (versión 3.10 <= versión <= 3.12)

2. Instala nuestro paquete:

3. Comienza a usar en el navegador:

    ```bash
    gbabeldocui
    ```

4. Si tu navegador no se ha iniciado automáticamente, ve a

    ```bash
    http://localhost:7860/
    ```

    Arrastra el archivo PDF a la ventana y haz clic en `Translate`.

5. Si despliegas GBabelDocUI con docker, y estás usando ollama como backend LLM de GBabelDocUI, debes llenar "Ollama host" con

   ```bash
   http://host.docker.internal:11434
   ```

> **Nota de seguridad:** Ollama es un servicio del lado del servidor y solo está disponible para administradores. El endpoint privado `http://host.docker.internal:11434` se rechaza de forma predeterminada. Solo en un despliegue de confianza, establece `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` en el entorno del contenedor. Esto relaja la protección contra SSRF; no lo habilites si usuarios no confiables pueden acceder a GBabelDocUI.

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Preview## Vista previa

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>Parte del contenido de esta página ha sido traducido por GPT y puede contener errores.</small></h6>