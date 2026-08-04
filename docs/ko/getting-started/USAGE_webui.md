[**시작하기**](./getting-started.md) > **설치** > **WebUI** _(현재)_

---

### Webui 를 통해 GBabelDocUI 사용하기

#### WebUI 페이지를 여는 방법:

WebUI 인터페이스를 여는 방법에는 여러 가지가 있습니다. **Windows**를 사용 중이라면 [이 문서](./INSTALLATION_winexe.md) 를 참조하세요.

1. Python 설치 (3.10 <= 버전 <= 3.12)

2. 패키지 설치:

3. 브라우저에서 사용 시작:

    ```bash
    gbabeldocui
    ```

4. 브라우저가 자동으로 시작되지 않은 경우 다음으로 이동:

    ```bash
    http://localhost:7860/
    ```

    PDF 파일을 창에 드롭하고 `Translate` 을 클릭하세요.

5. docker 로 GBabelDocUI 를 배포하고 ollama 를 GBabelDocUI 의 백엔드 LLM 으로 사용하는 경우 "Ollama host"에 다음을 입력해야 합니다:

   ```bash
   http://host.docker.internal:11434
   ```

> **보안 안내:** Ollama는 서버 측 서비스이며 관리자만 사용할 수 있습니다. 비공개 엔드포인트 `http://host.docker.internal:11434`는 기본적으로 거부됩니다. 신뢰할 수 있는 배포에서만 컨테이너 환경에 `GBABELDOCUI_ALLOW_PRIVATE_ENDPOINTS=true`를 설정하세요. 이 설정은 SSRF 보호를 완화하므로 신뢰할 수 없는 사용자가 GBabelDocUI에 접근할 수 있는 경우 활성화하지 마세요.

<!-- <img src="./../../images/gui.gif" width="500"/> -->
<img src='./../../images/gui.gif' width="500"/>
### Configure the translation

Use the GBabelDocUI settings page to choose the translation service, source and target languages, PDF outputs, page range and advanced options. The selected settings are saved per user and are snapshotted when a task starts.

When running the Docker container, keep `./data` mounted to `/app/data`. The default Compose deployment listens on `127.0.0.1:7860`; use an HTTPS reverse proxy for public access. The translation executor is designed for one application process and one shared data directory.
## Preview## 미리보기

<img src="./../../images/before.png" width="500"/>
<img src="./../../images/after.png" width="500"/>

<div align="right"> 
<h6><small>이 페이지의 일부 내용은 GPT 에 의해 번역되었으며 오류가 포함될 수 있습니다.</small></h6>