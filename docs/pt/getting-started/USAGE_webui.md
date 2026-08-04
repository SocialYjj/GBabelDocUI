[**Começar**](./getting-started.md) > **Instalação** > **WebUI** _(atual)_

---

### Usar GBabelDocUI via Webui

#### Como abrir a página WebUI:

Existem vários métodos para abrir a interface WebUI. Se você estiver usando **Windows**, consulte [este artigo](./INSTALLATION_winexe.md);

1. Python instalado (versão entre 3.10 e 3.12)

2. Instale nosso pacote:

3. Comece a usar no navegador:

    ```bash
    gbabeldocui
    ```

4. Se o seu navegador não foi iniciado automaticamente, acesse

    ```bash
    http://localhost:7860/
    ```

    Arraste o arquivo PDF para a janela e clique em `Translate`.

5. Se você implantar o GBabelDocUI com docker e estiver usando o ollama como o LLM de backend do GBabelDocUI, você deve preencher "Ollama host" com

   ```bash
   http://host.docker.internal:11434
   ```

> **Nota de segurança:** Ollama é um serviço do lado do servidor disponível apenas para administradores. O endpoint privado `http://host.docker.internal:11434` é rejeitado por padrão. Somente em uma implantação confiável, defina `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true` no ambiente do contêiner. Isso relaxa a proteção contra SSRF; não habilite essa opção se usuários não confiáveis puderem acessar o GBabelDocUI.

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Visualização

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>Parte do conteúdo desta página foi traduzida pelo GPT e pode conter erros.</small></h6>