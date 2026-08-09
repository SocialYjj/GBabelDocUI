# GBabelDocUI Web UI 사용

서비스는 브라우저를 자동으로 열지 않습니다. 시작한 뒤 로그인 페이지를 직접 여십시오.

## 요구 사항

- Python 3.10–3.13
- Git
- [uv](https://docs.astral.sh/uv/)

## 저장소에서 실행

```bash
git clone https://github.com/SocialYjj/GBabelDocUI.git
cd GBabelDocUI
uv sync --frozen
```

로컬 HTTP에서는 쿠키의 Secure 속성을 비활성화합니다.

=== "Linux/macOS"

    ```bash
    export GBABELDOCUI_COOKIE_SECURE=false
    uv run gbabeldocui
    ```

=== "Windows PowerShell"

    ```powershell
    $env:GBABELDOCUI_COOKIE_SECURE = "false"
    uv run gbabeldocui
    ```

시작 후 `http://127.0.0.1:7860/login.html`을 여십시오.

## 첫 사용

1. 로컬 로그인 페이지에서 첫 관리자를 생성합니다.
2. 설정에서 OpenAI, Azure OpenAI 또는 Google Gemini를 구성합니다.
3. 언어, 출력, 페이지 범위 및 PDF 옵션을 선택합니다.
4. PDF를 업로드하고 작업을 시작한 뒤 기록에서 결과를 내려받습니다.

저장된 API 키는 서버에만 남습니다. `data/` 디렉터리를 커밋하거나 공개하지 마십시오.

컨테이너에서는 Docker Compose 문서를 사용하십시오. 공개 배포에는 HTTPS와 데이터 디렉터리당 하나의 인스턴스가 필요합니다.
